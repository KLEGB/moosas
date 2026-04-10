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
from pathlib import Path
from typing import Any, Dict, List

from rdflib import Graph, Literal, URIRef

from app.core.config import settings
from app.core.process_pool import run_in_process
from app.core.storage import save_output_file
from app.core.logger import log_custom
from .MoosasPy.utils import generate_code
from .MoosasPy import loadModel, saveModel, transform
from .MoosasPy import energyAnalysis
from .MoosasPy.energy import facadeAnnualGeneration, roofAnnualGeneration
from .MoosasPy.weather import includeEpw,MoosasWeather


# ═════════════════════════════════════════════════════════════════════════════
# Shared Helper Functions
# ═════════════════════════════════════════════════════════════════════════════
def resolve_weather(station_id: str) -> str:
    def extract_epw_from_zip(zip_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.epw'):
                        return os.path.join(root, file)

        return None
    station_id = str(station_id)
    if station_id in MoosasWeather.loadStation():
        return station_id

    else:
        EPWs = os.listdir(str(settings.EPW_FOLDER))
        target_zip = [epw for epw in EPWs if station_id in epw][0]
        target_epw = extract_epw_from_zip(target_zip)
        if target_epw:
            station_id_rev = includeEpw(target_epw)
            return station_id_rev

    raise FileNotFoundError(f'Station ID {station_id} not found in global epw file.')




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
        archive_name = f"result_{generate_code()}.zip"
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
        output_path = settings.OUTPUT_DIR / f"{generate_code(6)}.rdf"

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
        output_path = settings.OUTPUT_DIR / f"{generate_code(6)}{output_ext}"

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
    station_id = resolve_weather(task_params.get("station_id", "545110"))
    params["station_id"] = station_id  # Ensure the resolved station ID is used in the worker
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
    return await run_in_process(
        _worker_PV_analysis,
        str(effective_path),
        task_params or {},
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
# Operation 6 — Multi-File Task Template  (Pattern A: File → Zip)
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
    out_file1 = settings.OUTPUT_DIR / f"result_part1_{generate_code(4)}.txt"
    out_file2 = settings.OUTPUT_DIR / f"result_part2_{generate_code(4)}.json"
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
