"""OpenFOAM workspace setup for legacy airflow workflows."""

from __future__ import annotations

from pathlib import Path
import shutil


def create_openfoam_workspace(root: str | Path) -> Path:
    """Reset and create the OpenFOAM directory layout expected by ventilation tools."""
    workspace = Path(root)
    if workspace.exists():
        shutil.rmtree(workspace)

    for relative_path in ("0", "constant/triSurface", "log", "system"):
        (workspace / relative_path).mkdir(parents=True, exist_ok=True)
    (workspace / "vent.foam").touch()
    return workspace