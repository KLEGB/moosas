# green-building-report

## 描述

绿色建筑性能分析工作流。用户上传 4 个固定格式文件后，自动提取建筑能耗、气象、几何与热工数据，并由 LLM 自由撰写一份专业的 Markdown 分析报告。

**适用场景：** 用户上传以下 4 个文件并请求生成建筑性能分析报告时触发本 Skill。

---

## 输入文件（固定 4 个）

| 文件类型 | 格式 | 识别关键词 |
|----------|------|-----------|
| 气象数据 | JSON | weather / 气象 / met / epw |
| 能耗结果 | JSON | energy / 能耗 / energyanalysis / daily |
| 建筑信息 | RDF/XML | rdf / xml / temp / building |
| 辅助脚本 | .py | helper / rdf_keyword / keyword_search |

---

## 架构说明

```
analyze.py（数据提取层）
  ├── 能耗 JSON  → energy 模块（年度/季节/峰值/EUI/光伏）
  ├── 气象 JSON  → weather 模块（温度/辐射/风速/季节均值）
  └── RDF 文本   → geometry 模块（面积/体积/体形系数/窗墙比/U值）
         ↓ 输出 data_package.json
LLM（报告撰写层）
  └── 接收完整数据包，自由撰写 Markdown 报告
```

analyze.py 只负责数值提取，不生成任何报告文本。报告由 LLM 根据数据包自主撰写，
结构、深度、语言风格完全开放，只约束三个核心主题和数值来源诚信。

---

## 执行步骤（供 Agent 参考）

### Step 1：识别文件
调用 identify_files 工具，传入用户提供的所有文件路径，确认四类文件均存在。

### Step 2：提取数据
调用 extract_data 工具，运行 scripts/analyze.py 子进程，获取结构化 data_package。

data_package 包含三个模块：

**energy 模块（能耗）**
- building_area_m2：建筑面积
- annual_consumption_kwh：年总能耗
- annual_generation_kwh：年光伏发电量
- annual_net_kwh：年净能耗（消耗 − 发电）
- annual_cooling_kwh / annual_heating_kwh / annual_lighting_kwh：分项能耗
- eui_kwh_per_m2：单位面积能耗强度
- pv_self_sufficiency_ratio：光伏自给率
- days_with_cooling / days_with_heating：制冷/采暖天数
- seasonal_breakdown：四季分项能耗
- peak_cooling_day / peak_heating_day / peak_generation_day：峰值日详情

**weather 模块（气象）**
- annual_avg/max/min_temp_c：年均/极值温度
- hot_days_above_35c / cold_days_max_below_0c：极端天气天数
- seasonal_avg_temp_c / seasonal_avg_rad_w_m2：季节均温与辐射
- annual_ghi_kwh_m2：年总水平辐射量
- annual_avg_wind_speed_m_s：年均风速

**geometry 模块（建筑几何与热工）**
- total_floor_area_m2 / total_volume_m3：建筑面积与体积
- total_outdoor_surface_area_m2：外表面积
- shape_factor_m_inv：体形系数
- window_to_wall_ratio：窗墙比
- wall_u_avg_w_m2k / window_u_avg_w_m2k：墙体/窗户平均传热系数
- rdf_parse_mode：解析模式（text_fallback 表示文本回退解析）
- parse_error：若非 null 则说明该模块解析失败

### Step 3：撰写报告

LLM 基于 data_package 自由撰写 Markdown 报告，须覆盖以下三个主题：

1. 建筑能耗表现：年度总量、分项占比、季节分布、峰值特征、光伏发电与净能耗
2. 建筑几何与围护结构：体形系数、窗墙比、热工参数，结合气候背景评价
3. 节能设计建议：至少 3 条，必须直接基于数据中的薄弱环节

约束：
- 所有数值必须来自 data_package，严禁编造
- 若字段为 null，在报告中说明"未能提取"
- 若某模块 parse_error 非 null，说明该模块解析失败，降级处理
- 报告以 # 标题开头，为合法 Markdown

---

## 脚本调用方式

```bash
python scripts/analyze.py \
  <weather_json> <energy_json> <rdf_file> <rdf_helper_py> <output_json>
```

输出：结构化 JSON 数据包（data_package.json）

---

## 注意事项

- RDF 解析采用文本回退模式（正则匹配），无需 rdflib，但依赖字段命名规范
- 若 geometry 模块 parse_error 非 null，仅基于 energy + weather 撰写降级报告
- analyze.py 超时限制为 120 秒；整体 Agent 超时为 300 秒
