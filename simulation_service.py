"""
Simulation service layer.
This file contains all worker functions and their corresponding async service
functions. It implements operations provided by the MoosasPy module.

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

import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Union

from rdflib import Graph, Literal, URIRef

# Assuming MoosasPy is a local package in the same directory or installed


from .MoosasPy.utils import generate_code


from app.core.config import settings
from app.core.process_pool import run_in_process
from app.core.storage import save_output_file


# ═════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═════════════════════════════════════════════════════════════════════════════

def _resolve_storage_path(
    input_file_path: Path | None = None,
    input_filename: str | None = None,
) -> Path:
    """
    Resolve the effective file path from either a direct Path or a filename.
    """
    if input_file_path:
        return input_file_path

    if not input_filename:
        raise ValueError("Either input_file_path or input_filename must be provided.")

    # Search in output storage first, then input storage
    output_path = settings.OUTPUT_DIR / input_filename
    if output_path.exists():
        return output_path

    input_path = settings.INPUT_DIR / input_filename
    if input_path.exists():
        return input_path

    raise FileNotFoundError(f"File '{input_filename}' not found in storage.")


def _create_zip_archive(file_paths: List[Path], archive_name: str | None = None) -> Path:
    """
    Create a ZIP archive containing the specified files.
    The archive is saved to the output directory.
    """
    if not archive_name:
        archive_name = f"result_{generate_code()}.zip"
    
    if not archive_name.endswith(".zip"):
        archive_name += ".zip"
        
    zip_path = settings.OUTPUT_DIR / archive_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            if file_path.exists():
                # Add file to zip, using its name as the arcname (no directory structure)
                zipf.write(file_path, arcname=file_path.name)
                
    return zip_path


def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert non-standard JSON types (like custom classes, Path, etc.)
    into standard JSON-serializable types (str, dict, list, etc.).
    This prevents PydanticSerializationError when returning MoosasPy results.
    """
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(i) for i in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, Path):
        return str(obj)
    elif hasattr(obj, "__dict__"):
        # For custom objects, try to convert their __dict__
        return _sanitize_for_json(vars(obj))
    else:
        # Fallback to string representation
        return str(obj)


# ═════════════════════════════════════════════════════════════════════════════
# Operation 1 — Transform Model  (Pattern A: File → File)
# ═════════════════════════════════════════════════════════════════════════════
from .MoosasPy import loadModel, saveModel, transform
def _worker_transform(
    input_path_str: str,
    transform_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert a building model file to RDF format using MoosasPy.transform.
    """
    input_path = Path(input_path_str)
    start_time = time.perf_counter()

    # Filter params to only those accepted by MoosasPy.transform
    accepted_param_names = transform.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in transform_params.items()
        if key in accepted_param_names
    }

    # Run model conversion
    converted_model = transform(str(input_path.resolve()), **filtered_params)

    # Determine output path
    if "output_filename" in transform_params:
        output_path = settings.OUTPUT_DIR / transform_params["output_filename"]
    else:
        output_path = settings.OUTPUT_DIR / f"{generate_code(6)}.rdf"

    saveModel(converted_model, str(output_path))

    # Persist to output storage
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
    Convert a saved model file to any supported format using MoosasPy.loadModel and saveModel.
    """
    input_path = Path(input_path_str)
    start_time = time.perf_counter()

    # Filter params to only those accepted by MoosasPy.loadModel
    # Note: 'format' is our own param for output, not for loadModel
    accepted_param_names = loadModel.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in export_params.items()
        if key in accepted_param_names and key != "format"
    }

    # Run model loading
    model = loadModel(str(input_path.resolve()), **filtered_params)

    # Determine output path and format
    output_ext = export_params.get("format", "rdf")
    if not output_ext.startswith("."):
        output_ext = f".{output_ext}"

    if "output_filename" in export_params:
        output_path = settings.OUTPUT_DIR / export_params["output_filename"]
    else:
        output_path = settings.OUTPUT_DIR / f"{generate_code(6)}{output_ext}"

    # Save model in requested format
    saveModel(model, str(output_path))

    # Persist to output storage
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
    """
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    result = await run_in_process(
        _worker_export,
        str(effective_path),
        task_params or {},
    )
    return result["output_filename"], result["metadata"]


# ═════════════════════════════════════════════════════════════════════════════
# Operation 3 — Energy Analysis  (Pattern B: File → Dict)
# ═════════════════════════════════════════════════════════════════════════════

from .MoosasPy import energyAnalysis
def _worker_energy_analysis(
    model_path_str: str,
    task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Load an RDF model, attach weather data, and run MoosasPy.energyAnalysis.
    """
    model_path = Path(model_path_str)
    start_time = time.perf_counter()

    # Load model and weather data
    model = loadModel(str(model_path.resolve()))
    station_id = task_params.get("station_id", "545110")
    model.loadWeatherData(station_id)

    # Filter params to only those accepted by energyAnalysis
    accepted_param_names = energyAnalysis.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in task_params.items()
        if key in accepted_param_names
    }

    # Run energy analysis
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
    """
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    return await run_in_process(
        _worker_energy_analysis,
        str(effective_path),
        task_params or {},
    )


# ═════════════════════════════════════════════════════════════════════════════
# Operation 4 — PV generation analysis  (Pattern B: File → Dict)
# ═════════════════════════════════════════════════════════════════════════════

from .MoosasPy.energy import facadeAnnualGeneration,roofAnnualGeneration
def _worker_PV_analysis(
        model_path_str: str,
        task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Load an RDF model, attach weather data, and run MoosasPy.roofAnnualGeneration.
    """
    model_path = Path(model_path_str)
    start_time = time.perf_counter()

    # Load model and weather data
    model = loadModel(str(model_path.resolve()))
    station_id = task_params.get("station_id", "545110")
    target = task_params.get("target", "roof")
    model.loadWeatherData(station_id)

    # Filter params to only those accepted by energyAnalysis
    analysis_method = roofAnnualGeneration if target == "roof" else facadeAnnualGeneration
    accepted_param_names = analysis_method.__code__.co_varnames
    filtered_params = {
        key: value
        for key, value in task_params.items()
        if key in accepted_param_names
    }

    # Run energy analysis
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
    Async service function for Operation 3 (Energy Analysis).
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
    Update existing RDF triples for a given space and overwrite the source file.
    """
    rdf_path = Path(rdf_path_str)
    rdf_format: str = task_params.get("rdf_format", "xml")
    space_settings: Dict[str, Any] = task_params.get("space_settings", {})

    # Validate inputs
    if not rdf_path.exists():
        raise FileNotFoundError(f"RDF file not found: {rdf_path}")
    if not isinstance(space_settings, dict):
        raise TypeError("task_params['space_settings'] must be a dict.")
    
    space_id = space_settings.get("space_id")
    settings_to_update = space_settings.get("settings", {})
    
    if not space_id:
        raise ValueError("Missing 'space_id' in space_settings.")

    # Load RDF graph
    graph = Graph()
    graph.parse(str(rdf_path), format=rdf_format)

    # Find the space subject (assuming it's a URIRef or BNode based on ID)
    # This logic depends on how MoosasPy/RDF identifies spaces.
    # Here we search for any subject that has the given ID as a literal value.
    space_subject = None
    for s, p, o in graph.triples((None, None, Literal(space_id))):
        space_subject = s
        break
    
    if not space_subject:
        raise ValueError(f"Space with ID '{space_id}' not found in RDF model.")

    updated_fields = []
    for predicate_uri, new_value in settings_to_update.items():
        predicate = URIRef(predicate_uri)
        # Remove old triples for this predicate
        graph.remove((space_subject, predicate, None))
        # Add new triple
        graph.add((space_subject, predicate, Literal(new_value)))
        updated_fields.append(predicate_uri)

    # Overwrite the file
    graph.serialize(destination=str(rdf_path), format=rdf_format)

    return _sanitize_for_json({
        "status": "success",
        "updated_space_id": space_id,
        "updated_fields": updated_fields,
    })


async def update_space_settings(
    input_file_path: Path | None = None,
    input_filename: str | None = None,
    *,
    task_params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Async service function for Operation 4 (Update Space Settings).
    """
    effective_path = _resolve_storage_path(input_file_path, input_filename)
    return await run_in_process(
        _worker_update_space_settings,
        str(effective_path),
        task_params or {},
    )


# ═════════════════════════════════════════════════════════════════════════════
# Operation 5 — Multi-File Task  (Pattern A: File → Zip)
# ═════════════════════════════════════════════════════════════════════════════

def _worker_multi_file_task(
    input_path_str: str,
    task_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process an input file into multiple output files and return a ZIP archive.
    """
    input_path = Path(input_path_str)
    start_time = time.perf_counter()
    
    # --- SIMULATION START ---
    # In a real scenario, you would call your module here.
    # For this template, we'll just create two dummy files.
    
    out_file1 = settings.OUTPUT_DIR / f"result_part1_{generate_code(4)}.txt"
    out_file2 = settings.OUTPUT_DIR / f"result_part2_{generate_code(4)}.json"
    
    out_file1.write_text(f"Processed content from {input_path.name}")
    out_file2.write_text('{"status": "ok", "parts": 2}')
    
    # Pack them into a ZIP
    zip_path = _create_zip_archive([out_file1, out_file2])
    # --- SIMULATION END ---

    # Persist to output storage
    stored_path = save_output_file(zip_path)
    elapsed_seconds = round(time.perf_counter() - start_time, 3)

    return _sanitize_for_json({
        "output_filename": stored_path.name,
        "metadata": {
            "input_file": input_path.name,
            "output_file": stored_path.name,
            "elapsed_seconds": elapsed_seconds,
            "files_included": [out_file1.name, out_file2.name]
        },
    })


async def run_multi_file_task(
    input_file_path: Path,
    *,
    task_params: Dict[str, Any] | None = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Async service function for Operation 5 (Multi-File Task).
    """
    result = await run_in_process(
        _worker_multi_file_task,
        str(input_file_path),
        task_params or {},
    )
    return result["output_filename"], result["metadata"]
