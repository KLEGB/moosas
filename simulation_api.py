import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from moosas.app.core.config import settings
from moosas.simulation_service import run_energy_analysis

app = FastAPI(title="Moosas Simulation Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/energy-analysis")
async def energy_analysis(
    file: UploadFile = File(...),
    input_filename: str | None = Form(default=None),
    task_params: str | None = Form(default=None),
) -> dict:
    if not file.filename and not input_filename:
        raise HTTPException(status_code=400, detail="Missing input filename")

    filename = input_filename or file.filename or "input.rdf"
    destination = settings.INPUT_DIR / Path(filename).name

    try:
        content = await file.read()
        destination.write_bytes(content)

        params = json.loads(task_params) if task_params else {}
        result = await run_energy_analysis(
            input_file_path=destination,
            task_params=params,
        )
        return result
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid task_params JSON: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
