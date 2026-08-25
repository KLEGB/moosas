"""Shared public contracts for building-performance simulations.

New simulation APIs use ``snake_case`` for modules, functions, parameters, and
result fields. Request and result types use ``PascalCase``. Each runner returns
a ``SimulationResult`` subclass and retains diagnostics for native commands.
"""

from __future__ import annotations

from dataclasses import dataclass

from .runner import CommandResult
from .workspace import WorkspaceReport


@dataclass(frozen=True)
class SimulationResult:
    """Common diagnostics returned by every simulation runner.

    Domain-specific result types extend this class with their calculated data.
    Empty tuples indicate that a simulation did not invoke a native command or
    completed without warnings.
    """

    commands: tuple[CommandResult, ...] = ()
    warnings: tuple[str, ...] = ()
    workspace: WorkspaceReport | None = None

    @property
    def successful(self) -> bool:
        """Whether all native commands completed successfully."""
        return all(command.returncode == 0 for command in self.commands)
