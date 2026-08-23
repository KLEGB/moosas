"""Isolated execution support for Radiance daylight calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import tempfile
from typing import TYPE_CHECKING, TextIO

from ...utils import path
from ..contracts import SimulationResult
from ..runner import CommandError, CommandResult, CommandTimeoutError, Runner
from .scene import modelToRad, writeGrid

if TYPE_CHECKING:
    from ...models import MoosasModel
    from ...transformation.geometry.element import MoosasElement


@dataclass(frozen=True)
class RadianceSky:
    """Parameters used to generate a Radiance sky description."""

    date: datetime
    sky_type: str
    latitude: float = 39.93
    longitude: float = 116.28
    diffuse_illuminance: float = 15000.0


RadianceCommandResult = CommandResult


@dataclass(frozen=True)
class DaylightFloorResult:
    """Daylight metrics for one model floor element."""

    uid: str
    element: MoosasElement
    grid_point_count: int
    illuminances: tuple[float, ...]
    daylight_factor: float
    satisfied_fraction: float


@dataclass(frozen=True)
class RadianceDaylightResult(SimulationResult):
    """Structured output from an isolated Radiance daylight run."""

    floors: tuple[DaylightFloorResult, ...] = ()

    def as_legacy(self) -> list[dict]:
        """Return the dictionary payload historically produced by ``simModel``."""
        return [
            {
                "Uid": floor.uid,
                "element": floor.element,
                "gridLength": floor.grid_point_count,
                "df": floor.daylight_factor,
                "satisfied": floor.satisfied_fraction,
            }
            for floor in self.floors
        ]


class RadianceCommandError(CommandError):
    """Raised when a Radiance executable exits with a non-zero status."""

class RadianceTimeoutError(CommandTimeoutError):
    """Raised when a Radiance executable exceeds the configured timeout."""

class RadianceRunner(Runner):
    """Run a daylight calculation in an isolated temporary work directory."""

    result_type = RadianceCommandResult
    error_type = RadianceCommandError
    timeout_error_type = RadianceTimeoutError

    _RTRACE_ARGUMENTS = (
        "-w", "-h", "-I+", "-u", "-aa", "0.15", "-ab", "4", "-ad", "256",
        "-ar", "32", "-as", "20", "-st", "1", "-lw", "0.05", "-dc", "0",
        "-dj", "0.7", "-dp", "32", "-dr", "0", "-ds", "0",
    )

    def __init__(
        self,
        model: MoosasModel,
        sky: RadianceSky,
        work_dir: str | Path | None = None,
        timeout_seconds: float = 300.0,
        executable_dir: str | Path | None = None,
    ):
        super().__init__(timeout_seconds=timeout_seconds)
        self.model = model
        self.sky = sky
        self.work_dir = Path(work_dir) if work_dir is not None else None
        self.executable_dir = Path(executable_dir) if executable_dir is not None else Path(path.libDir) / "rad"

    def run(self) -> RadianceDaylightResult:
        """Generate inputs, run Radiance, and return parsed daylight metrics."""
        if self.work_dir is not None:
            self.work_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="moosas-radiance-", dir=self.work_dir) as temporary_dir:
            run_dir = Path(temporary_dir)
            rad_path = run_dir / "model.rad"
            grid_path = run_dir / "grid.input"
            octree_path = run_dir / "model.oct"
            output_path = run_dir / "illuminance.output"

            floors = self._write_inputs(rad_path, grid_path)
            if not floors:
                return RadianceDaylightResult(floors=(), commands=())

            oconv_result = self._compile_scene(rad_path, octree_path, run_dir)
            rtrace_result, illuminances = self._trace_illuminance(octree_path, grid_path, output_path, run_dir)
            floor_results = self._summarize_floors(floors, illuminances)
            return RadianceDaylightResult(
                floors=tuple(floor_results),
                commands=(oconv_result, rtrace_result),
            )

    def _write_inputs(self, rad_path: Path, grid_path: Path) -> list[tuple[MoosasElement, int]]:
        modelToRad(
            self.model,
            self.sky.date,
            self.sky.sky_type,
            self.sky.latitude,
            self.sky.longitude,
            self.sky.diffuse_illuminance,
            str(rad_path),
        )
        floors = []
        for space in self.model.spaceList:
            for floor in space.getAllFaces(to_dict=True)["MoosasFloor"]:
                grid_lines = writeGrid(
                    floor,
                    gridPath=str(grid_path),
                    normal=[0, 0, 1],
                    append=bool(floors),
                )
                floors.append((floor, len(grid_lines)))
        return floors

    def _compile_scene(self, rad_path: Path, octree_path: Path, run_dir: Path) -> RadianceCommandResult:
        command = (str(self._executable("oconv")), str(rad_path))
        with octree_path.open("wb") as octree_file:
            return self._run_command(command, run_dir, stdout=octree_file)

    def _trace_illuminance(
        self,
        octree_path: Path,
        grid_path: Path,
        output_path: Path,
        run_dir: Path,
    ) -> tuple[RadianceCommandResult, tuple[float, ...]]:
        command = (str(self._executable("rtrace")), *self._RTRACE_ARGUMENTS, str(octree_path))
        with grid_path.open("r", encoding="utf-8") as grid_file:
            command_result = self._run_command(command, run_dir, stdin=grid_file)

        illuminances = self._parse_illuminances(command_result.stdout)
        output_path.write_text("\n".join(str(value) for value in illuminances) + "\n", encoding="utf-8")
        return command_result, illuminances

    def _summarize_floors(
        self,
        floors: list[tuple[MoosasElement, int]],
        illuminances: tuple[float, ...],
    ) -> list[DaylightFloorResult]:
        expected_count = sum(grid_count for _, grid_count in floors)
        if len(illuminances) != expected_count:
            raise ValueError(f"Radiance returned {len(illuminances)} values for {expected_count} grid points.")

        floor_results = []
        offset = 0
        for floor, grid_count in floors:
            values = illuminances[offset:offset + grid_count]
            offset += grid_count
            average = sum(values) / grid_count
            floor_results.append(
                DaylightFloorResult(
                    uid=floor.Uid,
                    element=floor,
                    grid_point_count=grid_count,
                    illuminances=values,
                    daylight_factor=average / self.sky.diffuse_illuminance,
                    satisfied_fraction=sum(value > 300.0 for value in values) / grid_count,
                )
            )
        return floor_results

    def _run_command(
        self,
        command: tuple[str, ...],
        run_dir: Path,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
    ) -> RadianceCommandResult:
        return self.run_command(command, cwd=run_dir, stdin=stdin, stdout=stdout)

    def _executable(self, name: str) -> Path:
        executable_name = f"{name}.exe" if os.name == "nt" else name
        executable = self.executable_dir / executable_name
        if not executable.exists():
            raise RadianceCommandError((str(executable),), -1, "", "Radiance executable was not found.")
        return executable

    @staticmethod
    def _parse_illuminances(output: str) -> tuple[float, ...]:
        values = []
        for line_number, line in enumerate(output.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                red, green, blue = (float(value) for value in line.split()[:3])
            except ValueError as error:
                raise ValueError(f"Invalid rtrace output on line {line_number}: {line!r}") from error
            values.append((red * 0.265 + green * 0.670 + blue * 0.065) * 179)
        return tuple(values)

    _decode_output = staticmethod(Runner._decode_output)