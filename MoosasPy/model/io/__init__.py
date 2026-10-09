"""Model I/O through a single format-dispatched save interface."""

from .dispatch import load_model, save_model
from .result import SaveResult

__all__ = ["SaveResult", "load_model", "save_model"]
