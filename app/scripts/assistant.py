from typing import Any
import time
import tempfile
import asyncio
import re
import json

from pathlib import Path
from typing import Any, Dict, List, AsyncIterator, Awaitable, Callable
from rdflib import Graph, Literal, URIRef, BNode
from openai import AsyncOpenAI
import traceback
from app.core.logger import log_error
from app.core.config import settings
from app.core.logger import log_custom
from ..MoosasPy.weather import includeEpw,MoosasWeather


def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert non-standard types into JSON-serializable equivalents.

    Handles the following cases:
      - dict / list / tuple / set  → recursively sanitized
      - str / int / float / bool / None  → returned as-is
      - pathlib.Path  → converted to str
      - objects with __dict__ (e.g. MoosasPy custom classes such as
        ThermalSettings)  → converted via vars(), then recursively sanitized
      - anything else  → converted to str via repr()

    This prevents ``PydanticSerializationError`` when FastAPI tries to
    serialise MoosasPy result objects that Pydantic cannot introspect.
    """
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(i) for i in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "tolist"):
        return _sanitize_for_json(obj.tolist())
    if hasattr(obj, "item"):
        try:
            return _sanitize_for_json(obj.item())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        # Custom objects (e.g. ThermalSettings): expose their instance attributes.
        return _sanitize_for_json(vars(obj))
    # Final fallback — use repr() to avoid silent data loss.
    return repr(obj)

async def _worker_GBAssistant(
    rdf_path: Path,
    weather_path: Path,
    energy_path: Path,
    *,
    to_xml: bool = False,
    progress_callback: Callable[[Dict[str, Any]], Awaitable[None]] | None = None,
) -> Dict[str, Any]:
    """
    Internal Green Building Assistant flow.

    Entry:
      resolved RDF / weather CSV / energy JSON paths.

    Exit:
      sanitized dict containing the generated Markdown report and the effective
      input filenames.
    """
    async def emit_status(stage: str, message: str, **extra: Any) -> None:
        if progress_callback is None:
            return
        payload: Dict[str, Any] = {
            "type": "status",
            "stage": stage,
            "message": message,
        }
        payload.update(extra)
        await progress_callback(payload)

    def require_setting(value: str, name: str) -> str:
        if value:
            return value
        raise RuntimeError(f"Environment variable '{name}' is required for this endpoint.")

    async def with_retry(label: str, factory, attempts: int = 3, delay_seconds: float = 2.0):
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return await factory()
            except Exception as exc:
                last_error = exc
                if attempt == attempts:
                    break
                await asyncio.sleep(delay_seconds)
        raise RuntimeError(f"{label} failed after {attempts} attempts: {last_error}")

    def prepare_upload_source(file_path: Path, *, to_xml: bool = False) -> tuple[Path, Path | None]:
        """
        Prepare RDF for assistant upload.

        - Default (to_xml=False): return the original path without conversion.
        - to_xml=True: parse and sanitise RDF, then write a temporary RDF/XML file.

        Returns (path_to_use, temp_xml_path_or_None).
        """
        if (not to_xml) or (file_path.suffix.lower() != ".rdf"):
            return file_path, None

        graph = Graph()
        parsed = False
        for rdf_format in ("xml", "turtle", "n3", "nt", "json-ld"):
            try:
                graph.parse(str(file_path), format=rdf_format)
                parsed = True
                break
            except Exception:
                continue

        if not parsed:
            raise ValueError(
                f"Failed to parse RDF file '{file_path.name}'. "
                "Please provide a valid RDF serialization."
            )

        uri_sanitize_ns = "https://moosas.local/normalized/"

        def sanitize_uri(uri_text: str) -> str:
            raw = uri_text.strip().strip("<>")
            cleaned = re.sub(r"[^A-Za-z0-9._~:/#?\[\]@!$&'()*+,;=%-]+", "-", raw)
            cleaned = re.sub(r"-+", "-", cleaned).strip("-")
            if not cleaned:
                cleaned = "term"
            if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", cleaned):
                cleaned = uri_sanitize_ns + cleaned.lstrip("/#")
            return cleaned

        def sanitize_subject(term):
            if isinstance(term, URIRef):
                return URIRef(sanitize_uri(str(term)))
            if isinstance(term, BNode):
                return term
            return URIRef(sanitize_uri(str(term)))

        def sanitize_predicate(term):
            if isinstance(term, URIRef):
                return URIRef(sanitize_uri(str(term)))
            return URIRef(sanitize_uri(str(term)))

        def sanitize_object(term):
            if isinstance(term, URIRef):
                return URIRef(sanitize_uri(str(term)))
            if isinstance(term, Literal):
                if isinstance(term.datatype, URIRef):
                    return Literal(
                        str(term),
                        lang=term.language,
                        datatype=URIRef(sanitize_uri(str(term.datatype))),
                    )
                return term
            if isinstance(term, BNode):
                return term
            return Literal(str(term))

        sanitized_graph = Graph()
        for s, p, o in graph:
            sanitized_graph.add((sanitize_subject(s), sanitize_predicate(p), sanitize_object(o)))

        temp_file = tempfile.NamedTemporaryFile(
            prefix=f"{file_path.stem}_",
            suffix=".xml",
            delete=False,
        )
        temp_path = Path(temp_file.name)
        temp_file.close()
        sanitized_graph.serialize(destination=str(temp_path), format="xml")
        return temp_path, temp_path

    def extract_assistant_text(message: Any) -> str:
        chunks: list[str] = []
        for block in message.content:
            if getattr(block, "type", None) == "text":
                chunks.append(block.text.value)
        if not chunks:
            raise RuntimeError("Assistant response did not contain any text content.")
        return "\n".join(chunks)

    client = AsyncOpenAI(
        api_key=require_setting(settings.OPENAI_API_KEY, "OPENAI_API_KEY"),
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
        max_retries=2,
    )

    async def retrieve_assistant():
        assistant_id = require_setting(
            settings.GREEN_BUILDING_ASSISTANT_ID,
            "GREEN_BUILDING_ASSISTANT_ID",
        )
        assistant = await client.beta.assistants.retrieve(assistant_id)

        tool_types = {tool.type for tool in assistant.tools}
        if "code_interpreter" not in tool_types:
            raise RuntimeError(
                "The configured assistant does not have the code_interpreter tool enabled."
            )

        return assistant

    async def upload_file_for_assistant(file_path: Path) -> str:
        upload_path, temp_path = prepare_upload_source(file_path, to_xml=to_xml)

        try:
            with open(upload_path, "rb") as file_handle:
                async def upload_once():
                    file_handle.seek(0)
                    return await client.files.create(file=file_handle, purpose="assistants")

                file_obj = await with_retry(f"Uploading {file_path.name}", upload_once)
            return file_obj.id
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

    await emit_status("retrieving_assistant", "Retrieving assistant configuration.")
    assistant = await with_retry("Retrieving assistant", retrieve_assistant)
    await emit_status("assistant_ready", "Assistant configuration loaded.", assistant_id=assistant.id)

    # 更稳健地获取同级目录下的app/rdf_keyword_search_helper.py
    helper_script_path = Path(__file__).parent / "rdf_keyword_search_helper.py"
    if not helper_script_path.exists():
        raise FileNotFoundError(f"Required helper script not found: {helper_script_path}")

    # 生成weather json文件
    weather_data = MoosasWeather.loadWeatherData(weather_path)
    weather_json_path = weather_path.with_suffix('.json')
    weather_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(weather_json_path, 'w', encoding='utf-8') as f:
        json.dump(_sanitize_for_json(weather_data), f, ensure_ascii=False)
    log_custom(f"Weather data converted to JSON {weather_json_path}.")
    file_ids: list[str] = []
    try:
        for file_role, file_path in (
            ("rdf", rdf_path),
            ("weather_json", weather_json_path),
            ("energy_json", energy_path),
            ("rdf_helper_script", helper_script_path),
        ):
            await emit_status(
                "uploading_file",
                f"Uploading {file_path.name}.",
                file_role=file_role,
                filename=file_path.name,
            )
            uploaded_file_id = await upload_file_for_assistant(file_path)
            file_ids.append(uploaded_file_id)
            await emit_status(
                "file_uploaded",
                f"Uploaded {file_path.name}.",
                file_role=file_role,
                filename=file_path.name,
                uploaded_file_id=uploaded_file_id,
            )

        await emit_status("creating_thread", "Creating assistant thread.")
        thread = await with_retry(
            "Creating thread",
            lambda: client.beta.threads.create(),
        )
        await emit_status("thread_created", "Assistant thread created.", thread_id=thread.id)
        attachments = [{"file_id": file_id, "tools": [{"type": "code_interpreter"}]} for file_id in file_ids]

        await emit_status("creating_message", "Attaching files and creating user message.")
        await with_retry(
            "Creating thread message",
            lambda: client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=(
                    "请严格按照 assistant 的分析要求，对附件中的 RDF、CSV 和 JSON 文件进行真实计算，"
                    "输出建筑能耗表现总结、体形系数与窗墙比及合规性评价、围护结构建议和进一步节能设计建议。"
                    "如需在 RDF 中做关键词查询或兜底检索，请优先使用附件脚本 rdf_keyword_search_helper.py，"
                    "通过 keyword_query(file_path, query, top_k) 获取结果，不要自行假设 RDF 谓词一定可按命名空间分割。"
                ),
                attachments=attachments,
            ),
        )
        await emit_status("message_created", "Assistant input message created.")

        await emit_status("creating_run", "Creating assistant run.")
        run = await client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        await emit_status(
            "run_created",
            f"Assistant run created with status '{run.status}'.",
            run_id=run.id,
            run_status=run.status,
        )

        terminal_statuses = {
            "completed",
            "failed",
            "cancelled",
            "expired",
            "incomplete",
            "requires_action",
        }
        last_status = run.status
        last_emit_at = time.monotonic()

        while run.status not in terminal_statuses:
            await asyncio.sleep(2.0)
            run = await with_retry(
                "Polling run status",
                lambda: client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                ),
            )

            now = time.monotonic()
            if run.status != last_status or (now - last_emit_at) >= 10.0:
                await emit_status(
                    "run_status",
                    f"Assistant run status: {run.status}.",
                    run_id=run.id,
                    run_status=run.status,
                )
                last_status = run.status
                last_emit_at = now

        if run.status != "completed":
            raise RuntimeError(
                f"Run failed with status: {run.status}. Last error: {run.last_error}"
            )

        await emit_status("fetching_response", "Fetching assistant response.")
        messages = await with_retry(
            "Fetching assistant response",
            lambda: client.beta.threads.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1,
            ),
        )
        report_markdown = extract_assistant_text(messages.data[0])
        await emit_status("response_ready", "Assistant response retrieved.")

        return {
            "report_markdown": report_markdown,
            "assistant_id": assistant.id,
            "input_files": {
                "rdf": rdf_path.name,
                "weather_json": weather_json_path.name,
                "energy_json": energy_path.name,
                "rdf_helper_script": helper_script_path.name,
            },
        }
    finally:
        for file_id in file_ids:
            try:
                await client.files.delete(file_id)
            except Exception:
                pass

