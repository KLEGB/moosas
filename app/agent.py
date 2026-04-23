"""
green_building_agent.py
=======================
基于 OpenAI tool-calling 的绿色建筑性能分析 Agent。

架构说明
--------
- analyze.py（Skill 脚本）：纯数据提取层，输出结构化 JSON 数据包，不生成任何文本。
- 本 Agent：将数据包注入 LLM，由 LLM 自由撰写报告。
  LLM 拥有完整的数字事实，但报告的结构、语言风格、侧重点、深度均由其自主决定。

公开接口
--------
    run_green_building_agent(
        query: str,
        file_paths: dict[str, str],
        *,
        output_dir: str | None = None,
        model: str = "gpt-4o",
        max_iterations: int = 12,
        timeout_seconds: int = 300,
    ) -> AgentResult

AgentResult 字段
----------------
    success      : bool          — 是否成功完成
    report_md    : str | None    — LLM 生成的 Markdown 报告全文
    report_path  : str | None    — 报告写入的本地路径（若 output_dir 已指定）
    data_package : dict | None   — analyze.py 提取的原始数据包（供调试）
    error        : str | None    — 失败时的错误信息
    iterations   : int           — 实际执行的 tool-call 轮次
    tool_log     : list[dict]    — 每次工具调用的摘要日志

file_paths 键名约定（大小写不敏感，支持模糊匹配）
--------------------------------------------------
    "weather"  → 气象 JSON 文件路径
    "energy"   → 能耗 JSON 文件路径
    "rdf"      → 建筑信息 RDF/XML 文件路径
    "helper"   → rdf_keyword_search_helper.py 路径
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI

# ── Skill 脚本路径 ────────────────────────────────────────────────────────────
_SKILL_SCRIPT = (
    Path(__file__).parent / "scripts" / "analyze.py"
)

# ── 返回值数据类 ──────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    success: bool
    report_md: str | None = None
    report_path: str | None = None
    data_package: dict | None = None
    error: str | None = None
    iterations: int = 0
    tool_log: list[dict] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# 工具实现层（三个工具，全部是纯 Python / 子进程，不调用 LLM）
# ═══════════════════════════════════════════════════════════════════════════════

def _tool_identify_files(file_paths: dict | list) -> dict[str, Any]:
    """
    识别并验证四个输入文件是否存在，返回规范化路径映射。
    兼容三种模型传参方式：
      1. {"file_paths": {"weather": ..., ...}}   正常嵌套
      2. {"weather": ..., "energy": ..., ...}    顶层展开（由 _dispatch_tool 处理）
      3. [{"key": "weather", "value": ...}, ...]  数组格式
    """
    # 兼容数组格式
    if isinstance(file_paths, list):
        converted: dict[str, str] = {}
        for item in file_paths:
            if isinstance(item, dict):
                k = item.get("key") or item.get("name") or item.get("type") or ""
                v = item.get("value") or item.get("path") or ""
                if k and v:
                    converted[k] = v
        file_paths = converted

    key_map: dict[str, str | None] = {
        "weather": None, "energy": None, "rdf": None, "helper": None,
    }
    # helper 必须先于 rdf 匹配，避免 rdf_keyword_search_helper.py 被误判为 rdf
    alias_priority = [
        ("helper",  ["helper", "rdf_keyword", "keyword_search", ".py"]),
        ("weather", ["weather", "气象", "met", "epw"]),
        ("energy",  ["energy", "能耗", "energyanalysis", "daily", "sample"]),
        ("rdf",     ["rdf", "xml", "temp", "building", "建筑"]),
    ]

    for raw_key, raw_path in file_paths.items():
        norm_key   = raw_key.lower().replace("-", "_").replace(" ", "_")
        path_lower = raw_path.lower()
        for canonical, aliases in alias_priority:
            if any(a in norm_key or a in path_lower for a in aliases):
                if key_map[canonical] is None:
                    key_map[canonical] = raw_path
                break

    missing   = [k for k, v in key_map.items() if v is None]
    not_found = [v for v in key_map.values() if v and not Path(v).exists()]

    return {
        "resolved":        key_map,
        "missing_keys":    missing,
        "not_found_paths": not_found,
        "ready":           len(missing) == 0 and len(not_found) == 0,
    }


def _tool_extract_data(
    weather_path: str,
    energy_path: str,
    rdf_path: str,
    helper_path: str,
    output_json_path: str,
) -> dict[str, Any]:
    """
    调用 analyze.py 子进程，提取建筑数据并输出结构化 JSON 数据包。
    返回数据包内容供 LLM 撰写报告使用。
    """
    skill_script = str(_SKILL_SCRIPT)
    if not Path(skill_script).exists():
        return {"success": False, "error": f"Skill 脚本不存在：{skill_script}"}

    cmd = [
        sys.executable, skill_script,
        weather_path, energy_path, rdf_path, helper_path, output_json_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0 or not Path(output_json_path).exists():
            return {
                "success": False,
                "error":   proc.stderr.strip()[:500] or "脚本执行失败",
            }
        data_package = json.loads(Path(output_json_path).read_text(encoding="utf-8"))
        return {
            "success":      True,
            "data_package": data_package,
            "stdout":       proc.stdout.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "数据提取脚本超时（120s）"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ── 工具分发表 ────────────────────────────────────────────────────────────────

_TOOL_HANDLERS: dict[str, Any] = {
    "identify_files": _tool_identify_files,
    "extract_data":   _tool_extract_data,
}


def _dispatch_tool(tool_name: str, arguments: dict) -> str:
    """
    执行工具，将结果序列化为 JSON 字符串。
    对 identify_files 做参数归一化：兼容模型将 file_paths 直接展开为顶层 kwargs 的情况。
    """
    handler = _TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"未知工具：{tool_name}"}, ensure_ascii=False)

    if tool_name == "identify_files" and "file_paths" not in arguments:
        arguments = {"file_paths": arguments}

    try:
        result = handler(**arguments)
    except TypeError as exc:
        result = {"error": f"参数错误：{exc}"}
    except Exception as exc:
        result = {"error": f"工具执行异常：{exc}"}

    return json.dumps(result, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════════════
# OpenAI 工具 Schema
# ═══════════════════════════════════════════════════════════════════════════════

_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "identify_files",
            "description": (
                "识别并验证用户提供的四个输入文件（气象JSON、能耗JSON、RDF建筑文件、helper脚本）"
                "是否存在且路径正确。必须在提取数据前调用此工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "object",
                        "description": (
                            "文件路径字典，键为文件类型（weather/energy/rdf/helper），值为绝对路径。"
                            "示例：{\"weather\": \"/path/a.json\", \"energy\": \"/path/b.json\", "
                            "\"rdf\": \"/path/c.rdf\", \"helper\": \"/path/d.py\"}"
                        ),
                        "additionalProperties": {"type": "string"},
                    }
                },
                "required": ["file_paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_data",
            "description": (
                "调用数据提取脚本，从气象、能耗、RDF 三个文件中提取所有可用数值，"
                "输出结构化 JSON 数据包。必须在 identify_files 确认文件就绪后调用。"
                "返回的 data_package 包含 energy、weather、geometry 三个模块的完整数据，"
                "是后续撰写报告的唯一数据来源。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "weather_path":      {"type": "string", "description": "气象 JSON 文件绝对路径"},
                    "energy_path":       {"type": "string", "description": "能耗 JSON 文件绝对路径"},
                    "rdf_path":          {"type": "string", "description": "建筑 RDF/XML 文件绝对路径"},
                    "helper_path":       {"type": "string", "description": "rdf_keyword_search_helper.py 绝对路径"},
                    "output_json_path":  {"type": "string", "description": "数据包输出路径（含文件名，.json）"},
                },
                "required": [
                    "weather_path", "energy_path", "rdf_path",
                    "helper_path", "output_json_path",
                ],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 系统提示
# ═══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = textwrap.dedent("""\
        你是一个专业且有洞见的绿色建筑性能分析 Agent。

        目标：在严格基于数据（data_package）的前提下，输出一份可读性强、推理充分、风格自然不僵硬的分析报告。

        ## 执行流程

        1) 先调用 identify_files，确认四个文件均存在；若缺失或路径错误，直接报告并停止。
        2) 再调用 extract_data，获取结构化数据包（data_package）。
             - data_package 含 energy（能耗）、weather（气象）、geometry（建筑几何与热工）。
             - 若某模块 parse_error 非 null，须在报告中如实说明并采用降级策略（跳过相关指标或以可替代指标推断）。
        3) 仅基于 data_package 中真实可用的数值与事实撰写报告，不得编造。

        ## 报告结构（三大部分，允许自定表述但禁止空话）

        报告必须是 Markdown，以 `#` 开头，并包含以下三个主标题（风格自然、措辞灵活，但逻辑完整）：

        <!-- SECTION:1 START -->
        ## 建筑能耗表现
        - 聚焦年度总量、分项占比、季节分布与峰值时段；如有光伏，给出发电与净能耗的量化对比。
        - 结合气象特征（如采暖/制冷度日、日照）解释能耗波动原因，使用具体数值进行因果分析。
        <!-- SECTION:1 END -->

        <!-- SECTION:2 START -->
        ## 围护结构选型建议
        - 以提取到的体形系数、窗墙比、U 值、遮阳等参数为依据，评价当前围护热工合理性。
        - 给出可落地的选型/参数调整建议（明确到方向/范围/优先级），并说明预期影响机理。
        <!-- SECTION:2 END -->

        <!-- SECTION:3 START -->
        ## 节能设计建议
        - 至少 3 条，紧扣数据中暴露的薄弱环节（如特定时段空调用能、照明/插载占比偏高等），
            每条建议都需配以简短的“为什么（基于何数据） + 怎么做（可执行动作）”。
        <!-- SECTION:3 END -->

        说明：
        - 上述三部分的标题可在不改变含义的前提下略作润色；
        - 报告允许自然语言的过渡、类比与小结，但必须以 data_package 的数值为依据；
        - 若某关键指标缺失，明确写出“未能提取”，并尽可能用替代指标进行合理推断（注明依据与不确定性）。

        ## 书写风格
        - 简洁专业但不生硬，可使用小标题、要点列表、对比表述来增强可读性；
        - 用“因果—证据”的句式衔接数据与结论，避免口号式空话；
        - 中文行业术语规范，单位与数量级准确，一处定义全文一致。

        ## 约束
        - identify_files 的 file_paths 必须是 JSON 对象（键为类型字符串、值为路径字符串），禁止数组格式；
        - 严禁在未获得 data_package 前输出报告内容；
        - 严禁虚构数据；
        - 输出即为最终报告，无需额外附注。
""")


# ═══════════════════════════════════════════════════════════════════════════════
# 主 Agent 函数
# ═══════════════════════════════════════════════════════════════════════════════

def run_green_building_agent(
    query: str,
    file_paths: dict[str, str],
    *,
    output_dir: str | None = None,
    model: str = "gpt-4o",
    max_iterations: int = 12,  # 保留参数兼容性（不再使用循环）
    timeout_seconds: int = 300,
) -> AgentResult:
    """
    绿色建筑性能分析 Agent（严格多轮）：
    - 先以纯工具调用（本地函数）识别文件并提取数据包；
    - 再串行触发 3 次模型对话：能耗表现 → 围护结构 → 节能建议；
      每一轮以上一轮输出为上下文，确保递进关系；
      每一轮仅输出本节，并用 HTML 注释标记包裹，便于服务端流式分段。
    """
    client = OpenAI()

    # 超时控制（简单起见：保证整体不超过 timeout_seconds）
    start_time = time.time()
    def ensure_time_left():
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(f"Agent 执行超时（>{timeout_seconds}s）")

    # 确定输出路径
    base_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir())
    base_dir.mkdir(parents=True, exist_ok=True)
    data_json_path   = str(base_dir / "data_package.json")
    report_md_path   = str(base_dir / "建筑性能分析报告.md")

    tool_log: list[dict] = []
    iterations = 0

    # 1) 识别并验证文件
    identify_result = _tool_identify_files(file_paths)
    iterations += 1
    tool_log.append({
        "iteration": iterations,
        "tool": "identify_files",
        "args_summary": {"file_paths": file_paths},
        "result_summary": {k: v for k, v in identify_result.items() if k != "resolved"},
    })
    if not identify_result.get("ready"):
        return AgentResult(
            success=False,
            error=f"文件缺失或路径异常：missing={identify_result.get('missing_keys')}, not_found={identify_result.get('not_found_paths')}",
            iterations=iterations,
            tool_log=tool_log,
        )

    resolved = identify_result["resolved"]
    weather_path = resolved["weather"] or ""
    energy_path  = resolved["energy"] or ""
    rdf_path     = resolved["rdf"] or ""
    helper_path  = resolved["helper"] or ""

    # 2) 提取数据包（调用 analyze.py 子进程）
    ensure_time_left()
    extract_result = _tool_extract_data(
        weather_path=weather_path,
        energy_path=energy_path,
        rdf_path=rdf_path,
        helper_path=helper_path,
        output_json_path=data_json_path,
    )
    iterations += 1
    tool_log.append({
        "iteration": iterations,
        "tool": "extract_data",
        "args_summary": {
            "weather_path": weather_path,
            "energy_path": energy_path,
            "rdf_path": rdf_path,
            "helper_path": helper_path,
            "output_json_path": data_json_path,
        },
        "result_summary": {k: v for k, v in extract_result.items() if k != "data_package"},
    })
    if not extract_result.get("success"):
        return AgentResult(
            success=False,
            error=extract_result.get("error") or "数据提取失败",
            iterations=iterations,
            tool_log=tool_log,
        )
    data_package = extract_result.get("data_package") or {}

    # 2.1) 关键信息摘要 + 原始 JSON 参考片段（控制 token 压力）
    def _kv(k: str, v) -> str:
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return f"- {k}: 未能提取"
        return f"- {k}: {v}"

    def _fmt_pct(x: float | None) -> str | None:
        try:
            return f"{round(x*100, 1)}%" if x is not None else None
        except Exception:
            return None

    def summarize(dp: dict) -> str:
        e = dp.get("energy", {}) or {}
        w = dp.get("weather", {}) or {}
        g = dp.get("geometry", {}) or {}
        lines: list[str] = []
        lines.append("[能耗 Energy]")
        lines.append(_kv("建筑面积m2", e.get("building_area_m2")))
        lines.append(_kv("总耗电kWh", e.get("annual_consumption_kwh")))
        lines.append(_kv("总发电kWh", e.get("annual_generation_kwh")))
        lines.append(_kv("净能耗kWh", e.get("annual_net_kwh")))
        lines.append(_kv("EUI(耗)kWh/m2", e.get("eui_consumption_kwh_per_m2")))
        lines.append(_kv("EUI(发)kWh/m2", e.get("eui_generation_kwh_per_m2")))
        lines.append(_kv("EUI(净)kWh/m2", e.get("eui_net_kwh_per_m2")))
        lines.append(_kv("光伏自给率", _fmt_pct(e.get("pv_self_sufficiency_ratio"))))
        if isinstance(e.get("seasonal_breakdown"), dict):
            sb = e["seasonal_breakdown"]
            # 仅列出每季总耗电与制冷/采暖合计，避免过长
            for sk in ("winter", "spring", "summer", "autumn"):
                sv = sb.get(sk, {}) or {}
                c = sv.get("consumption")
                cool = sv.get("cooling")
                heat = sv.get("heating")
                if any(v is not None for v in (c, cool, heat)):
                    lines.append(f"- 季节[{sk}]: 耗电={round(c,2) if isinstance(c,(int,float)) else c} kWh; "
                                 f"制冷={round(cool,2) if isinstance(cool,(int,float)) else cool} kWh; "
                                 f"采暖={round(heat,2) if isinstance(heat,(int,float)) else heat} kWh")

        lines.append("")
        lines.append("[气象 Weather]")
        lines.append(_kv("年均温°C", w.get("annual_avg_temp_c")))
        lines.append(_kv("年GHI kWh/m2", w.get("annual_ghi_kwh_m2")))
        lines.append(_kv(
            "四季均温°C",
            {k: w.get("seasonal_avg_temp_c", {}).get(k) for k in ("winter","spring","summer","autumn")}
        ))

        lines.append("")
        lines.append("[几何 Geometry]")
        lines.append(_kv("总建筑面积m2", g.get("total_floor_area_m2")))
        lines.append(_kv("总体积m3", g.get("total_volume_m3")))
        lines.append(_kv("体形系数1/m", g.get("shape_factor_m_inv")))
        lines.append(_kv("窗墙比", g.get("window_to_wall_ratio")))
        lines.append(_kv("外墙U W/m2K", g.get("wall_u_avg_w_m2k")))
        lines.append(_kv("窗U W/m2K", g.get("window_u_avg_w_m2k")))
        return "\n".join(lines)

    summary_text = summarize(data_package)
    # 参考原始 JSON 片段，上限控制（避免 token 爆掉）。
    reference_max_chars = 6000
    data_block_full = json.dumps(data_package, ensure_ascii=False)
    reference_block = data_block_full[:reference_max_chars]

    # 3) 严格多轮对话写作（每一轮只产出一节，使用分段标记包裹）
    def section_instruction(idx: int) -> str:
        if idx == 1:
            return (
                "请撰写‘建筑能耗表现’一节：聚焦年度总量、分项占比、季节分布、峰值特征，"
                "若有光伏则给出发电与净能耗对比；结合气象特征解释能耗波动。"
            )
        if idx == 2:
            return (
                "请撰写‘围护结构选型建议’一节：基于体形系数、窗墙比、U 值、遮阳等参数，"
                "评价当前热工合理性，并给出可落地的选型/参数调整建议，说明影响机理。"
            )
        return (
            "请撰写‘节能设计建议’一节：至少 3 条，紧扣数据中的薄弱环节，"
            "每条建议包含‘为什么（基于何数据） + 怎么做（可执行动作）’。"
        )

    def wrap_marker(idx: int, content: str) -> str:
        return f"<!-- SECTION:{idx} START -->\n{content.strip()}\n<!-- SECTION:{idx} END -->"

    # 为了减少僵硬表达，我们在每轮使用更轻的节指令，系统提示仍提供风格约束
    base_system = _SYSTEM_PROMPT
    context_so_far = ""
    sections: list[str] = []

    # 将 data_package 注入上下文（为控制长度，这里直接提供全文；如需可在此处裁剪或概括）
    for idx in (1, 2, 3):
        ensure_time_left()
        user_prompt = (
            f"{query}\n\n"
            f"关键信息摘要（优先作为依据）：\n````md\n{summary_text}\n````\n\n"
            f"原始 JSON（参考片段，可能被截断）：\n````json\n{reference_block}\n````\n\n"
            f"此前已完成内容（若为空表示首节）：\n````md\n{context_so_far}\n````\n\n"
            f"任务：{section_instruction(idx)}\n"
            f"要求：仅输出本节 Markdown 内容，语言自然不僵硬；"
            f"所有数值均来自 data_package；缺失项需标明‘未能提取’并可做审慎推断（注明依据）。"
            f"如摘要与参考片段不一致，以原始 JSON 为准。\n"
            f"请严格用如下注释包裹整段输出：<!-- SECTION:{idx} START --> … <!-- SECTION:{idx} END -->\n"
        )

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": base_system},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.3,
        )
        content = (resp.choices[0].message.content or "").strip()
        # 若模型未按要求嵌入标记，则我们主动包裹
        if f"<!-- SECTION:{idx} START -->" not in content:
            content = wrap_marker(idx, content)
        sections.append(content)
        # 将该节裸内容（去标记）追加到上下文，供下一节递进
        inner = content
        try:
            start_tag = f"<!-- SECTION:{idx} START -->"
            end_tag = f"<!-- SECTION:{idx} END -->"
            inner = content.split(start_tag, 1)[-1].rsplit(end_tag, 1)[0].strip()
        except Exception:
            pass
        context_so_far += ("\n\n" if context_so_far else "") + inner

    report_content = "\n\n".join(sections)
    Path(report_md_path).write_text(report_content, encoding="utf-8")

    return AgentResult(
        success=True,
        report_md=report_content,
        report_path=report_md_path,
        data_package=data_package,
        iterations=iterations + 3,  # 两次工具 + 三次写作
        tool_log=tool_log,
    )
