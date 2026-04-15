"""
Simulation service layer.

This module contains all worker functions and their corresponding async service
functions, implementing operations provided by the MoosasPy module.

PARALLELISM MODEL
─────────────────
  FastAPI event loop  ──submits──►  ProcessPoolExecutor (MAX_WORKERS processes)
        │                                    │
        │  awaits (non-blocking)             │  each process runs one worker
        │◄──────────────────────────────────┤  function independently
        │                                    │
        │  returns response                  MoosasPy (single-threaded — OK!)

  Up to MAX_WORKERS operations run truly in parallel. Additional requests are
  queued and served as workers become free.

RULES FOR WORKER FUNCTIONS
───────────────────────────
  • Must be defined at module level (not inside a class or another function)
    so that Python's multiprocessing can pickle them.
  • All arguments must be picklable: str, Path, int, float, dict, list.
  • Do NOT reference module-level `settings` inside a worker — import
    app.core.config inside the worker body if needed, or pass values as args.
"""
import os
import time
import tempfile
import zipfile
import asyncio
import re
import requests 
import glob
from pathlib import Path
from typing import Any, Dict, List, AsyncIterator, Awaitable, Callable
import pymysql
from rdflib import Graph, Literal, URIRef, BNode
from openai import AsyncOpenAI
import traceback
from app.core.logger import log_error
from app.core.config import settings
from app.core.process_pool import run_in_process
from app.core.storage import save_output_file
from app.core.logger import log_custom
from ..MoosasPy import utils
from ..MoosasPy import loadModel, saveModel, transform
from ..MoosasPy import energyAnalysis
from ..MoosasPy.energy import facadeAnnualGeneration, roofAnnualGeneration

from ..MoosasPy.weather import includeEpw,MoosasWeather
from .haversine import calculate_haversine_distance


# ═════════════════════════════════════════════════════════════════════════════
# Shared Helper Functions
# ═════════════════════════════════════════════════════════════════════════════
def resolve_weather(station_id: str = None, station_lat: float = None, station_lon: float = None) -> str:
    """
    Resolve weather data by station_id or coordinates.
    1. If station_id exists in MoosasWeather.loadStation(), return it directly.
    2. Otherwise, use stations.db to find the best match (by id or nearest coordinates),
       import to MoosasWeather, and return the station_id.
    """
    # 1. Try MoosasWeather.loadStation()
    station_dict = MoosasWeather.loadStation()
    if station_id and station_id in station_dict:
        return station_id
    # 2. Use DB to find best match
    # MySQL connection config
    MYSQL_CONFIG = dict(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DB,
        charset="utf8mb4"
    )
    
    def _query_station_by_id(station_id: str, prefer_source: str = "onebuilding", prefer_file_type: str = "TMYx"):
        try:
            conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM stations WHERE stationId = %s", (str(station_id),))
                rows = cur.fetchall()
            conn.close()
            if not rows:
                return None
            filtered = [r for r in rows if r["sources"].lower() == prefer_source.lower()]
            if filtered:
                rows = filtered
            filtered = [r for r in rows if prefer_file_type.lower() in (r["fileType"] or "").lower()]
            if filtered:
                rows = filtered
            rows = sorted(rows, key=lambda x: x["site"], reverse=True)
            return rows[0]
        except Exception as exc:
            tb_str = traceback.format_exc()
            log_error(f"_query_station_by_id SQL error: {exc}", tb_str)
            raise
    def _query_nearest_station(lat: float, lon: float, prefer_source: str = "onebuilding", prefer_file_type: str = "TMYx"):
        import traceback
        from app.core.logger import log_error
        try:
            conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM stations WHERE lat IS NOT NULL AND lon IS NOT NULL")
                rows = cur.fetchall()
            conn.close()
            filtered = [r for r in rows if r["sources"].lower() == prefer_source.lower()]
            if filtered:
                rows = filtered
            filtered = [r for r in rows if prefer_file_type.lower() in (r["fileType"] or "").lower()]
            if filtered:
                rows = filtered
            if not rows:
                return None
            def dist(row):
                return calculate_haversine_distance(lat, lon, row["lat"], row["lon"])
            nearest = min(rows, key=dist)
            return nearest
        except Exception as exc:
            tb_str = traceback.format_exc()
            log_error(f"_query_nearest_station SQL error: {exc}", tb_str)
            raise
    if station_id:
        station = _query_station_by_id(station_id)
        if not station:
            raise ValueError(f"No station found for station_id={station_id}")
    elif station_lat is not None and station_lon is not None:
        station = _query_nearest_station(station_lat, station_lon)
        if not station:
            raise ValueError(f"No station found near lat={station_lat}, lon={station_lon}")
    else:
        raise ValueError("Must provide station_id or both station_lat and station_lon.")
    # 自动下载、解压epw并include
    
    # 直接从数据库epw_files表获取epw内容（MySQL）
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cur:
            cur.execute("SELECT epwFile FROM epw_files WHERE stationId = %s", (station["stationId"],))
            row = cur.fetchone()
        conn.close()
        if not row or not row[0]:
            raise RuntimeError(f"No epw file found in database for stationId={station['stationId']}")
        epw_bytes = row[0]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epw') as tmp_epw:
            tmp_epw.write(epw_bytes)
            epw_path = tmp_epw.name
        includeEpw(epw_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load/include epw from database: {e}")
    return station["stationId"]


def _resolve_storage_path(
        input_file_path: Path | None = None,
        input_filename: str | None = None,
) -> Path:
    """
    Resolve the effective file path from either a direct Path object or a
    filename string. Searches output storage first, then input storage.

    Raises:
        ValueError: If neither argument is provided.
        FileNotFoundError: If the filename cannot be located in storage.
    """
    if input_file_path:
        return input_file_path
    if not input_filename:
        raise ValueError("Either input_file_path or input_filename must be provided.")
    output_path = settings.OUTPUT_DIR / input_filename
    if output_path.exists():
        return output_path
    input_path = settings.INPUT_DIR / input_filename
    if input_path.exists():
        return input_path
    raise FileNotFoundError(f"File '{input_filename}' not found in storage.")


def _create_zip_archive(file_paths: List[Path], archive_name: str | None = None) -> Path:
    """
    Create a ZIP archive containing the specified files and save it to the
    output directory. Files are stored without directory structure (flat).

    Args:
        file_paths:   List of Path objects to include in the archive.
        archive_name: Optional name for the archive file. A random name is
                      generated if not provided.

    Returns:
        Path to the created ZIP archive.
    """
    if not archive_name:
        archive_name = f"result_{utils.generate_code()}.zip"
    if not archive_name.endswith(".zip"):
        archive_name += ".zip"
    zip_path = settings.OUTPUT_DIR / archive_name
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            if file_path.exists():
                zipf.write(file_path, arcname=file_path.name)
    return zip_path


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
    if hasattr(obj, "__dict__"):
        # Custom objects (e.g. ThermalSettings): expose their instance attributes.
        return _sanitize_for_json(vars(obj))
    # Final fallback — use repr() to avoid silent data loss.
    return repr(obj)


async def _worker_GBAssistant(
        rdf_path: Path,
        weather_path: Path,
        energy_path: Path,
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

    def prepare_upload_source(file_path: Path) -> tuple[Path, Path | None]:
        if file_path.suffix.lower() != ".rdf":
            return file_path, None

        graph = Graph()
        parsed = False
        # Try common RDF serializations, then export to canonical RDF/XML.
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
            # Keep URL-safe punctuation, replace all other characters with '-'.
            cleaned = re.sub(r"[^A-Za-z0-9._~:/#?\[\]@!$&'()*+,;=%-]+", "-", raw)
            cleaned = re.sub(r"-+", "-", cleaned).strip("-")
            if not cleaned:
                cleaned = "term"

            # If URI has no scheme, force it into a stable absolute namespace.
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
            # Some source RDF contains malformed predicates (e.g. plain tokens);
            # force them into a normalized absolute URI.
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
        upload_path, temp_path = prepare_upload_source(file_path)

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

    helper_script_path = Path(__file__).with_name("app/rdf_keyword_search_helper.py")
    if not helper_script_path.exists():
        raise FileNotFoundError(f"Required helper script not found: {helper_script_path}")

    file_ids: list[str] = []
    try:
        for file_role, file_path in (
            ("rdf", rdf_path),
            ("weather_csv", weather_path),
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
                "weather_csv": weather_path.name,
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


async def run_GBAssistant(
        energy_json_path: Path | None = None,
        energy_json_filename: str | None = None,
        rdf_path: Path | None = None,
        rdf_file_name: str | None = None,
        station_id: str = "545110",
) -> Dict[str, Any]:
    """
    Public service entry for Green Building Assistant analysis.

    This method is intentionally compact so API endpoints can treat it as the
    single entry point for the assistant workflow:
      1. Resolve RDF and energy JSON paths from upload path or stored filename.
      2. Resolve weather station id and derive the corresponding weather CSV.
      3. Execute the assistant run and return a structured response dict.

    Args:
        energy_json_path: Uploaded energy JSON absolute path.
        energy_json_filename: Stored energy JSON filename (optional alternative).
        rdf_path: Uploaded RDF absolute path.
        rdf_file_name: Stored RDF filename (optional alternative).
        station_id: Weather station identifier used to load weather CSV.

    Returns:
        Dict containing ``report_markdown``, ``assistant_id``, and
        ``input_files``.
    """
    rdf_path = _resolve_storage_path(rdf_path, rdf_file_name)
    energy_json_path = _resolve_storage_path(energy_json_path, energy_json_filename)

    resolved_station_id = resolve_weather(
        station_id,
        None,
        None
    )
    weather_path = Path(
        os.path.join(utils.path.dataBaseDir, "weather", f"{resolved_station_id}.csv")
    )

    return await _worker_GBAssistant(rdf_path, weather_path, energy_json_path)


async def stream_GBAssistant(
        energy_json_path: Path | None = None,
        energy_json_filename: str | None = None,
        rdf_path: Path | None = None,
        rdf_file_name: str | None = None,
        station_id: str = "545110",
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream-friendly wrapper for Green Building Assistant.

    The business flow is exactly the same as ``run_GBAssistant``; this method
    only changes how results are delivered to callers by yielding progress and
    report chunks.
    """
    rdf_path = _resolve_storage_path(rdf_path, rdf_file_name)
    energy_json_path = _resolve_storage_path(energy_json_path, energy_json_filename)

    resolved_station_id = resolve_weather(
        station_id,
        None,
        None
    )
    weather_path = Path(
        os.path.join(utils.path.dataBaseDir, "weather", f"{resolved_station_id}.csv")
    )

    queue: asyncio.Queue[Dict[str, Any] | None] = asyncio.Queue()
    result_holder: Dict[str, Any] = {}

    async def publish(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            result = await _worker_GBAssistant(
                rdf_path,
                weather_path,
                energy_json_path,
                progress_callback=publish,
            )
            result_holder.update(result)
        except Exception as exc:
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            await queue.put(None)

    yield {
        "type": "status",
        "stage": "started",
        "message": "Green Building Assistant workflow started.",
    }

    task = asyncio.create_task(runner())

    while True:
        event = await queue.get()
        if event is None:
            break
        if event.get("type") == "error":
            yield event
            await task
            return
        yield event

    await task

    result = result_holder
    yield {
        "type": "status",
        "stage": "completed",
        "message": "Assistant run completed. Streaming report content.",
    }

    report_text = result.get("report_markdown", "")
    chunk_size = 1200
    for start in range(0, len(report_text), chunk_size):
        yield {
            "type": "chunk",
            "delta": report_text[start:start + chunk_size],
        }

    yield {
        "type": "result",
        "assistant_id": result.get("assistant_id"),
        "input_files": result.get("input_files", {}),
        "report_length": len(report_text),
    }

# ═════════════════════════════════════════════════════════════════════════════
# Operation 1 — Transform Model  (Pattern A: File → File)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_transform(
        input_path_str: str,
        transform_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Worker: convert a building model file to RDF format via MoosasPy.transform.

    Only parameters whose names match MoosasPy.transform's own signature are
    forwarded; all others are silently ignored.

    Args:
        input_path_str:   Absolute path of the input model file (str).
        transform_params: Dict of optional conversion parameters.

    Returns:
        Sanitized dict with keys ``output_filename`` and ``metadata``.
    """
    input_path = Path(input_path_str)
    start_time = time.perf_counter()

    accepted_param_names = transform.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in transform_params.items()
        if key in accepted_param_names
    }

    converted_model = transform(str(input_path.resolve()), **filtered_params)

    if "output_filename" in transform_params:
        output_path = settings.OUTPUT_DIR / transform_params["output_filename"]
    else:
        output_path = settings.OUTPUT_DIR / f"{utils.generate_code(6)}.rdf"

    saveModel(converted_model, str(output_path))
    stored_path = save_output_file(output_path)
    elapsed_seconds = round(time.perf_counter() - start_time, 3)

    return _sanitize_for_json({
        "output_filename": stored_path.name,
        "metadata": {
            "input_file": input_path.name,
            "output_file": stored_path.name,
            "elapsed_seconds": elapsed_seconds,
            "transform_params": transform_params,
        },
    })


async def transform_model(
        input_file_path: Path,
        *,
        task_params: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Async service function for Operation 1 (Transform Model).

    Submits ``_worker_transform`` to the process pool and awaits the result.

    Returns:
        Tuple of (output_filename, metadata_dict).
    """
    result = await run_in_process(
        _worker_transform,
        str(input_file_path),
        task_params or {},
    )
    return result["output_filename"], result["metadata"]


# ═════════════════════════════════════════════════════════════════════════════
# Operation 2 — Export Model  (Pattern A: File → File)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_export(
        input_path_str: str,
        export_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Worker: load a model file and re-save it in the requested output format
    via MoosasPy.loadModel and MoosasPy.saveModel.

    The ``save_type`` key in ``export_params`` controls the output format
    (e.g. ``"rdf"``, ``"idf"``, ``"geo"``). It is consumed locally and is
    NOT forwarded to either loadModel or saveModel.

    Args:
        input_path_str: Absolute path of the source model file (str).
        export_params:  Dict of export parameters (see endpoint docstring).

    Returns:
        Sanitized dict with keys ``output_filename`` and ``metadata``.
    """
    input_path = Path(input_path_str)
    start_time = time.perf_counter()

    # Forward only params accepted by loadModel; exclude our own 'save_type' key.
    load_accepted = list(loadModel.__code__.co_varnames)
    load_params = {
        key: value
        for key, value in export_params.items()
        if key in load_accepted and key != "save_type"
    }
    model = loadModel(str(input_path.resolve()), **load_params)

    # Determine output file extension from 'save_type'.
    output_ext = export_params.get("save_type", "rdf")
    if not output_ext.startswith("."):
        output_ext = f".{output_ext}"

    if "output_filename" in export_params:
        output_path = settings.OUTPUT_DIR / export_params["output_filename"]
    else:
        output_path = settings.OUTPUT_DIR / f"{utils.generate_code(6)}{output_ext}"

    # Forward only params accepted by saveModel; exclude our own 'save_type' key.
    save_accepted = list(saveModel.__code__.co_varnames)
    save_params = {
        key: value
        for key, value in export_params.items()
        if key in save_accepted and key != "save_type"
    }
    saveModel(model, str(output_path), **save_params)

    stored_path = save_output_file(output_path)
    elapsed_seconds = round(time.perf_counter() - start_time, 3)

    return _sanitize_for_json({
        "output_filename": stored_path.name,
        "metadata": {
            "input_file": input_path.name,
            "output_file": stored_path.name,
            "elapsed_seconds": elapsed_seconds,
            "export_params": export_params,
        },
    })


async def export_model(
        input_file_path: Path | None = None,
        input_filename: str | None = None,
        *,
        task_params: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Async service function for Operation 2 (Export Model).

    Resolves the source file, optionally resolves auxiliary file references
    (``idfTemplate``, ``iddFile``) in task_params, then submits
    ``_worker_export`` to the process pool.

    Returns:
        Tuple of (output_filename, metadata_dict).
    """
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    params = task_params or {}
    if "idfTemplate" in params:
        params["idfTemplate"] = str(_resolve_storage_path(input_filename=params["idfTemplate"]))
    if "iddFile" in params:
        params["iddFile"] = str(_resolve_storage_path(input_filename=params["iddFile"]))
    result = await run_in_process(
        _worker_export,
        str(effective_path),
        params,
    )
    return result["output_filename"], result["metadata"]


# ═════════════════════════════════════════════════════════════════════════════
# Operation 3 — Energy Analysis  (Pattern B: File → Dict)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_energy_analysis(
        model_path_str: str,
        task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Worker: load an RDF model, attach weather data, and run
    MoosasPy.energyAnalysis.

    Only parameters whose names match MoosasPy.energyAnalysis's own signature
    are forwarded; all others (e.g. ``station_id``) are consumed locally.

    Args:
        model_path_str: Absolute path of the RDF model file (str).
        task_params:    Dict of analysis parameters.

    Returns:
        Sanitized dict with keys ``analysis_results`` and ``metadata``.
    """
    model_path = Path(model_path_str)
    start_time = time.perf_counter()

    model = loadModel(str(model_path.resolve()))
    station_id = task_params.get("station_id", "545110")
    model.loadWeatherData(station_id)

    accepted_param_names = energyAnalysis.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in task_params.items()
        if key in accepted_param_names
    }

    analysis_results: Dict[str, Any] = energyAnalysis(model, **filtered_params)
    elapsed_seconds = round(time.perf_counter() - start_time, 3)
    analysis_results['area'] = sum([spc.area for spc in model.spaceList])
    return _sanitize_for_json({
        "analysis_results": analysis_results,
        "metadata": {
            "model_file": model_path.name,
            "station_id": station_id,
            "elapsed_seconds": elapsed_seconds,
        },
    })


async def run_energy_analysis(
        input_file_path: Path | None = None,
        input_filename: str | None = None,
        *,
        task_params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Async service function for Operation 3 (Energy Analysis).

    Resolves the source file, optionally resolves the ``schedulePath``
    auxiliary file reference in task_params, then submits
    ``_worker_energy_analysis`` to the process pool.

    Returns:
        Sanitized result dict from the worker.
    """
    params = task_params or {}
    station_id = task_params.get("station_id", "545110")
    station_lat = task_params.get("station_lat")
    station_lon = task_params.get("station_lon")
    resolved_station_id = resolve_weather(station_id, station_lat, station_lon)
    params["station_id"] = resolved_station_id  # Ensure the resolved station ID is used in the worker
    if "schedulePath" in params:
        params["schedulePath"] = str(_resolve_storage_path(input_filename=params["schedulePath"]))
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    return await run_in_process(
        _worker_energy_analysis,
        str(effective_path),
        params,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Operation 4 — PV Generation Analysis  (Pattern B: File → Dict)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_PV_analysis(
        model_path_str: str,
        task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Worker: load an RDF model, attach cumsky weather data, and run
    MoosasPy.roofAnnualGeneration or MoosasPy.facadeAnnualGeneration
    depending on the ``target`` parameter.

    Args:
        model_path_str: Absolute path of the RDF model file (str).
        task_params:    Dict of analysis parameters. Key ``target`` selects
                        the analysis surface: ``"roof"`` (default) or
                        ``"facade"``.

    Returns:
        Sanitized dict with keys ``analysis_results`` and ``metadata``.
    """
    model_path = Path(model_path_str)
    start_time = time.perf_counter()

    model = loadModel(str(model_path.resolve()))
    station_id = resolve_weather(task_params.get("station_id", "545110"))
    target = task_params.get("target", "roof")
    model.loadWeatherData(station_id)

    analysis_method = roofAnnualGeneration if target == "roof" else facadeAnnualGeneration
    accepted_param_names = analysis_method.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in task_params.items()
        if key in accepted_param_names
    }

    analysis_results: Dict[str, Any] = {target: list(analysis_method(model, **filtered_params))}
    elapsed_seconds = round(time.perf_counter() - start_time, 3)

    return _sanitize_for_json({
        "analysis_results": analysis_results,
        "metadata": {
            "model_file": model_path.name,
            "station_id": station_id,
            "elapsed_seconds": elapsed_seconds,
        },
    })


async def run_PV_analysis(
        input_file_path: Path | None = None,
        input_filename: str | None = None,
        *,
        task_params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Async service function for Operation 4 (PV Generation Analysis).

    Submits ``_worker_PV_analysis`` to the process pool and awaits the result.

    Returns:
        Sanitized result dict from the worker.
    """
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    params = task_params or {}
    station_id = params.get("station_id", "545110")
    station_lat = params.get("station_lat")
    station_lon = params.get("station_lon")
    resolved_station_id = resolve_weather(station_id, station_lat, station_lon)
    params["station_id"] = resolved_station_id
    return await run_in_process(
        _worker_PV_analysis,
        str(effective_path),
        params,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Operation 5 — Update Space Settings  (Pattern B: File → Dict)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_update_space_settings(
        rdf_path_str: str,
        task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Worker: update RDF triples for one or more spaces and overwrite the
    source file in place.

    Each entry in ``space_settings`` must contain:
      - ``space_id``  (str): the literal value used to identify the space node.
      - ``namespace`` (str): the predicate (as a string literal) to update.
      - ``value``     (any): the new value to assign.

    Spaces or predicates that cannot be located are silently skipped (a
    warning is printed to stdout).

    Args:
        rdf_path_str: Absolute path of the RDF file to update (str).
        task_params:  Dict containing ``space_settings`` (list) and
                      optionally ``rdf_format`` (str, default ``"xml"``).

    Returns:
        Sanitized dict with keys ``status``, ``updated_space_id``, and
        ``updated_fields``.
    """
    rdf_path = Path(rdf_path_str)
    rdf_format: str = task_params.get("rdf_format", "xml")
    all_space_settings = task_params.get("space_settings", [])

    graph = Graph()
    graph.parse(str(rdf_path), format=rdf_format)

    space_ids: list = []
    updated_fields: list = []

    for space_settings in all_space_settings:
        space_id = space_settings.get("space_id")
        space_ids.append(space_id)
        settings_to_update = space_settings.get("namespace", {})
        value_to_update = space_settings.get("value", {})

        if not space_id:
            log_custom("WARNING: Missing 'space_id' in space_settings entry — skipping.", "warning")
            continue

        # Locate the space subject by matching its ID as a literal value.
        space_subject = None
        for s, p, o in graph.triples((None, None, Literal(space_id))):
            space_subject = s
            break

        if not space_subject:
            log_custom(f"WARNING: Space '{space_id}' not found in RDF model — skipping.", "warning")
            continue

        predicate = Literal(settings_to_update)
        graph.remove((space_subject, predicate, None))
        graph.add((space_subject, predicate, Literal(value_to_update)))
        updated_fields.append(settings_to_update)

    graph.serialize(destination=str(rdf_path), format=rdf_format)

    return _sanitize_for_json({
        "status": "success",
        "updated_space_id": space_ids,
        "updated_fields": updated_fields,
    })


async def update_space_settings(
        input_file_path: Path | None = None,
        input_filename: str | None = None,
        *,
        task_params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Async service function for Operation 5 (Update Space Settings).

    Submits ``_worker_update_space_settings`` to the process pool and awaits
    the result.

    Returns:
        Sanitized result dict from the worker.
    """
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    return await run_in_process(
        _worker_update_space_settings,
        str(effective_path),
        task_params or {},
    )


# ═════════════════════════════════════════════════════════════════════════════
# Operation 6 — Download Weather Data  (Pattern C: Params → Dict)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_download_weather_data(station_id: str = "545110", station_lat: float = None, station_lon: float = None) -> Dict[str, Any]:
    """
    Worker: resolve a weather station by id or coordinates and return weather data as a dict.

    Args:
        station_id: Requested station id from API.
        station_lat: Latitude for nearest station lookup.
        station_lon: Longitude for nearest station lookup.

    Returns:
        Sanitized dict containing station metadata and hourly weather arrays.
    """

    try:
        resolved_station_id = resolve_weather(station_id, station_lat, station_lon)
        weather = MoosasWeather(resolved_station_id)
        location = weather.location

        weather_data = {
            key: value.tolist() if hasattr(value, "tolist") else list(value)
            for key, value in weather.weatherData.items()
        }

        return _sanitize_for_json({
            "station_id": resolved_station_id,
            "location": {
                "stationId": location.stationId,
                "city": location.city,
                "state": location.state,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "altitude": location.altitude,
                "pressure": location.pressure,
            },
            "weather_file": weather.weatherFile,
            "weather_data": weather_data,
        })
    except Exception as exc:
        tb_str = traceback.format_exc()
        log_error(f"_worker_download_weather_data failed: {exc}", tb_str)
        raise


async def download_weather_data(
    station_id: str = "545110",
    station_lat: float = None,
    station_lon: float = None
) -> Dict[str, Any]:
    """
    Async service function for Operation 6 (Download Weather Data).

    Resolves weather station by id or coordinates and returns weather data with
    the same key structure as ``loadWeatherData``.

    Args:
        station_id: Weather station id (optional if lat/lon provided).
        station_lat: Latitude for nearest station lookup.
        station_lon: Longitude for nearest station lookup.

    Returns:
        Sanitized weather payload dict.
    """
    return await run_in_process(
        _worker_download_weather_data,
        station_id,
        station_lat,
        station_lon,
    )


async def run_green_building_analysis(
        rdf_file_path: Path | None = None,
        rdf_filename: str | None = None,
        weather_file_path: Path | None = None,
        weather_filename: str | None = None,
        energy_file_path: Path | None = None,
        energy_filename: str | None = None,
) -> Dict[str, Any]:
    """
    Compatibility wrapper around ``run_GBAssistant``.

    This method keeps the previous signature (including weather file inputs)
    but delegates execution to ``run_GBAssistant``. If weather file/path is
    provided, station id is inferred from the weather filename stem.
    """
    station_id = "545110"
    if weather_file_path is not None or weather_filename is not None:
        weather_path = _resolve_storage_path(weather_file_path, weather_filename)
        station_id = weather_path.stem

    return await run_GBAssistant(
        energy_json_path=energy_file_path,
        energy_json_filename=energy_filename,
        rdf_path=rdf_file_path,
        rdf_file_name=rdf_filename,
        station_id=station_id,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Operation 7 — Multi-File Task Template  (Pattern A: File → Zip)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_multi_file_task(
        input_path_str: str,
        task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Worker template: process an input file into multiple output files and
    return a single ZIP archive containing all results.

    Replace the placeholder block between the SIMULATION START / END markers
    with your actual module calls.

    Args:
        input_path_str: Absolute path of the input file (str).
        task_params:    Dict of task parameters (passed through as-is).

    Returns:
        Sanitized dict with keys ``output_filename`` and ``metadata``.
    """
    input_path = Path(input_path_str)
    start_time = time.perf_counter()

    # ▼▼▼ REPLACE THIS PLACEHOLDER WITH YOUR MODULE CALLS ▼▼▼
    out_file1 = settings.OUTPUT_DIR / f"result_part1_{utils.generate_code(4)}.txt"
    out_file2 = settings.OUTPUT_DIR / f"result_part2_{utils.generate_code(4)}.json"
    out_file1.write_text(f"Processed content from {input_path.name}")
    out_file2.write_text('{"status": "ok", "parts": 2}')
    zip_path = _create_zip_archive([out_file1, out_file2])
    # ▲▲▲ REPLACE THIS PLACEHOLDER WITH YOUR MODULE CALLS ▲▲▲

    stored_path = save_output_file(zip_path)
    elapsed_seconds = round(time.perf_counter() - start_time, 3)

    return _sanitize_for_json({
        "output_filename": stored_path.name,
        "metadata": {
            "input_file": input_path.name,
            "output_file": stored_path.name,
            "elapsed_seconds": elapsed_seconds,
            "files_included": [out_file1.name, out_file2.name],
        },
    })


async def run_multi_file_task(
        input_file_path: Path,
        *,
        task_params: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Async service function for Operation 6 (Multi-File Task Template).

    Submits ``_worker_multi_file_task`` to the process pool and awaits the
    result.

    Returns:
        Tuple of (output_filename, metadata_dict).
    """
    result = await run_in_process(
        _worker_multi_file_task,
        str(input_file_path),
        task_params or {},
    )
    return result["output_filename"], result["metadata"]
