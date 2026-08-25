"""Lifecycle management for isolated simulation workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class WorkspaceReport:
    path: str
    retained: bool


class SimulationWorkspace:
    """Create and own one simulation run directory."""

    def __init__(self, *, parent=None, root=None, prefix="moosas-simulation-", retain=False):
        if parent is not None and root is not None:
            raise ValueError("parent and root are mutually exclusive")
        self.parent = Path(parent).resolve() if parent is not None else None
        self._requested_root = Path(root).resolve() if root is not None else None
        self.prefix = prefix
        self.retain = bool(retain or root is not None)
        self.path: Path | None = None
        self._temporary_directory: tempfile.TemporaryDirectory | None = None

    def __enter__(self):
        if self.path is not None:
            return self
        if self.parent is not None:
            self.parent.mkdir(parents=True, exist_ok=True)
        if self._requested_root is not None:
            self.path = self._requested_root
            self.path.mkdir(parents=True, exist_ok=True)
        elif self.retain:
            self.path = Path(tempfile.mkdtemp(prefix=self.prefix, dir=self.parent)).resolve()
        else:
            self._temporary_directory = tempfile.TemporaryDirectory(prefix=self.prefix, dir=self.parent)
            self.path = Path(self._temporary_directory.name).resolve()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None

    def child(self, *parts: str, directory: bool = False) -> Path:
        if self.path is None:
            raise RuntimeError("SimulationWorkspace must be entered before use")
        target = self.path.joinpath(*parts)
        target.resolve().relative_to(self.path)
        if directory:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
        return target

    @property
    def report(self):
        if self.path is None:
            raise RuntimeError("SimulationWorkspace must be entered before use")
        return WorkspaceReport(str(self.path), self.retain)
