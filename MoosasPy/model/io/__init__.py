"""Semantic model I/O and explicit grid-based OpenFOAM export."""

from .dispatch import load_model, save_model
from .openfoam import export_openfoam
from .result import SaveResult

__all__ = ["SaveResult", "load_model", "save_model", "export_openfoam"]
