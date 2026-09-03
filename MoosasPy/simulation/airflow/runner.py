"""Model-driven CONTAM airflow simulation."""

from dataclasses import dataclass
import os
import platform
import re
import shutil
import sys

import numpy as np

from ...model import MoosasModel
from ...utils.tools import path
from ..contracts import SimulationResult
from ..engine import NativeEngine
from ..runner import Runner
from ..workspace import SimulationWorkspace, WorkspaceReport
from .network import VENT_EXE_SUFFIX, buildNetworkFile, getZoneAndPath, pathTopology
from .parser import (
    AIR_DENSITY,
    build_matrix,
    read_file,
    read_flowpath,
    read_topology,
    write_file,
)


def _contam_platform(system=None, machine=None):
    """Return the bundled CONTAM directory and executable suffix for this host."""
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    if machine not in {"amd64", "x86_64"}:
        raise OSError(f"Bundled CONTAM tools do not support architecture: {machine}")
    if system == "win32":
        return "windows-x86_64", ".exe"
    if system.startswith("linux"):
        return "linux-x86_64", ""
    raise OSError(f"Bundled CONTAM tools do not support platform: {system}")


@dataclass(frozen=True)
class VentPaths:
    """Native CONTAM resources and isolated runtime paths for one run."""

    workspace: str
    contamx: str
    simread: str
    response: str
    contam_dir: str
    project_dir: str
    result_dir: str

    @classmethod
    def create(cls, work_dir=None):
        with SimulationWorkspace(parent=work_dir, prefix="moosas-vent-", retain=True) as workspace:
            return cls.from_workspace(workspace.path)

    @classmethod
    def from_workspace(cls, workspace):
        workspace = os.path.abspath(workspace)
        platform_dir, executable_suffix = _contam_platform()
        contam_root = os.path.join(path.libDir, "vent", "contam")
        bundled_dir = os.path.join(contam_root, platform_dir)
        contam_dir = os.path.join(workspace, "contam")
        project_dir = os.path.join(workspace, "project")
        result_dir = os.path.join(workspace, "result")
        os.makedirs(contam_dir, exist_ok=True)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)
        contamx_name = f"contamx3{executable_suffix}"
        simread_name = f"simread{executable_suffix}"
        for executable_name in (contamx_name, simread_name):
            target = os.path.join(contam_dir, executable_name)
            shutil.copy2(os.path.join(bundled_dir, executable_name), target)
            if not executable_suffix:
                os.chmod(target, 0o755)
        return cls(
            workspace=workspace,
            contamx=os.path.join(contam_dir, contamx_name),
            simread=os.path.join(contam_dir, simread_name),
            response=os.path.join(contam_root, "response.txt"),
            contam_dir=contam_dir,
            project_dir=project_dir,
            result_dir=result_dir,
        )


@dataclass(frozen=True)
class AirflowZoneResult:
    """Temperature and air-change histories for one model zone."""

    user_name: str
    project_name: str
    heat_load: float
    volume: float
    temperatures: tuple[float, ...]
    ach_values: tuple[float, ...]


@dataclass(frozen=True)
class AirflowResult(SimulationResult):
    """Structured output from one iterative CONTAM airflow calculation."""

    airflow_matrix: np.ndarray | None = None
    zones: tuple[AirflowZoneResult, ...] = ()
    converged: bool = False
    iteration_count: int = 0
    residual: float = float("inf")


class AirflowRunner(Runner):
    """Build and iteratively solve a CONTAM airflow model."""

    def __init__(
        self,
        model: MoosasModel,
        outdoor_temperature=25.0,
        heat_loads: dict[str, float] | None = None,
        max_iterations=50,
        convergence_tolerance=0.01,
        flow_multiplier=1.0,
        contam_exe=None,
        simread_exe=None,
        response_file=None,
        paths: VentPaths | None = None,
        work_dir=None,
        timeout_seconds=300.0,
        engine: NativeEngine | None = None,
    ):
        super().__init__(timeout_seconds=timeout_seconds, engine=engine)
        if int(max_iterations) <= 0:
            raise ValueError("max_iterations must be positive.")
        if float(convergence_tolerance) < 0:
            raise ValueError("convergence_tolerance must be non-negative.")
        self.model = model
        self.outdoor_temperature = float(outdoor_temperature)
        self.heat_loads = heat_loads
        self.max_iterations = int(max_iterations)
        self.convergence_tolerance = float(convergence_tolerance)
        self.flow_multiplier = float(flow_multiplier)
        self.paths = paths
        self.work_dir = work_dir
        self.contam_exe = contam_exe
        self.simread_exe = simread_exe
        self.response_file = response_file

    def run(self) -> AirflowResult:
        """Build the project and iterate airflow and zone sensible heat balance."""
        if self.paths is not None:
            return self._run()

        with SimulationWorkspace(parent=self.work_dir, prefix="moosas-airflow-") as workspace:
            self.paths = VentPaths.from_workspace(workspace.path)
            try:
                return self._run(workspace.report)
            finally:
                self.paths = None

    def _run(self, workspace_report=None) -> AirflowResult:
        network_file = os.path.join(self.paths.project_dir, "model.json")
        project_file = os.path.join(self.paths.project_dir, "model.prj")
        zones, airflow_paths = getZoneAndPath(self.model)
        zones, airflow_paths = self._apply_heat_loads(zones, airflow_paths)
        buildNetworkFile(
            model=self.model,
            pathList=airflow_paths,
            zoneList=zones,
            networkFilePath=network_file,
        )
        afn_result = self.run_command((
            os.path.join(path.libDir, "vent", f"MoosasAFN{VENT_EXE_SUFFIX}"),
            "-p", "model",
            "-d", self.paths.project_dir,
            "-t", str(self.outdoor_temperature),
            "-s", "0",
            network_file,
        ))
        commands = [afn_result]
        temperature_history = [[] for _ in zones]
        ach_history = [[] for _ in zones]
        previous_temperature = None
        previous_ach = None
        residual = float("inf")
        airflow_matrix = None

        for iteration_count in range(1, self.max_iterations + 1):
            iteration_result = self._run_project(project_file)
            commands.extend(iteration_result.commands)
            airflow_matrix = np.asarray(iteration_result.airflow_matrix, dtype=float) * self.flow_multiplier
            temperature = _solve_sensible_heat(
                airflow_matrix.copy(),
                np.array([zone.heatLoad for zone in zones]),
                self.outdoor_temperature,
            )
            temperature_values = (np.asarray(temperature, dtype=float) - 273.15).flatten()
            ach_values = np.maximum(airflow_matrix[-1, :-1], airflow_matrix[:-1, -1])
            for index in range(len(zones)):
                temperature_history[index].append(float(temperature_values[index]))
                ach_history[index].append(float(ach_values[index]))

            if previous_temperature is not None:
                temperature_residual = _relative_residual(temperature_values, previous_temperature)
                ach_residual = _relative_residual(ach_values, previous_ach)
                residual = float(np.mean(np.concatenate((temperature_residual, ach_residual))))

            _write_project_temperatures(temperature, project_file)
            if residual <= self.convergence_tolerance:
                break
            previous_temperature = temperature_values
            previous_ach = ach_values

        converged = residual <= self.convergence_tolerance
        return AirflowResult(
            airflow_matrix=airflow_matrix,
            zones=tuple(
                AirflowZoneResult(
                    user_name=zone.userName,
                    project_name=zone.prjName,
                    heat_load=float(zone.heatLoad),
                    volume=float(zone.volume),
                    temperatures=tuple(temperature_history[index]),
                    ach_values=tuple(ach_history[index]),
                )
                for index, zone in enumerate(zones)
            ),
            converged=converged,
            iteration_count=iteration_count,
            residual=residual,
            commands=tuple(commands),
            warnings=() if converged else ("Airflow iteration did not converge.",),
            workspace=workspace_report or WorkspaceReport(self.paths.workspace, True),
        )

    def _apply_heat_loads(self, zones, airflow_paths):
        if self.heat_loads is None:
            return zones, airflow_paths
        known_zones = {zone.userName for zone in zones}
        unknown_zones = set(self.heat_loads) - known_zones
        if unknown_zones:
            raise ValueError(f"Unknown airflow zones: {sorted(unknown_zones)}")
        zones = [zone for zone in zones if zone.userName in self.heat_loads]
        if not zones:
            raise ValueError("heat_loads must select at least one airflow zone.")
        for index, zone in enumerate(zones, start=1):
            zone.prjIndex = index
            zone.prjName = f"z{index:03d}"
            zone.heatLoad = float(self.heat_loads[zone.userName])
        return zones, pathTopology(airflow_paths, zones)

    def _run_project(self, project_file):
        contam_exe = self.contam_exe or self.paths.contamx
        simread_exe = self.simread_exe or self.paths.simread
        response_path = self.response_file or self.paths.response
        contam_result = self.run_command((contam_exe, project_file))
        with open(response_path, "r", encoding="utf-8") as response_file:
            simread_result = self.run_command(
                (simread_exe, project_file),
                stdin=response_file,
            )
        return AirflowResult(
            airflow_matrix=build_matrix(file_path=project_file),
            commands=(contam_result, simread_result),
            workspace=WorkspaceReport(self.paths.workspace, True),
        )


def _relative_residual(current, previous):
    denominator = np.maximum(np.abs(previous), np.finfo(float).eps)
    return np.abs((current - previous) / denominator)


def _solve_sensible_heat(airflow_matrix, heat_loads, outdoor_temperature):
    temperature_k = _calculate_temperature(airflow_matrix, heat_loads, outdoor_temperature)
    temperature_c = np.asarray(temperature_k, dtype=float) - 273.15
    temperature_c = np.where(temperature_c < 10.0, 22.0, temperature_c)
    temperature_c = np.where(temperature_c > 30.0, 30.0, temperature_c)
    return temperature_c + 273.15


def _write_project_temperatures(temperature, project_file):
    head, temperature_block, rear = read_file(project_file)
    rows = np.array([
        re.split(r"[ ]+", line)
        for line in temperature_block.split("\n")[:-1]
    ])
    rows[:, 9] = temperature
    temperature_block = "\n".join(" ".join(row) for row in rows) + "\n"
    write_file(project_file, head, temperature_block, rear)


def _calculate_temperature(airflow_matrix, heat_loads, outdoor_temperature):
    airflow_matrix = np.array(airflow_matrix, dtype=float, copy=True)
    heat_loads = np.asarray(heat_loads, dtype=float).reshape(-1)
    for column in range(len(airflow_matrix)):
        airflow_matrix[column, column] = -np.sum(airflow_matrix[:, column])
        for row in range(len(airflow_matrix) - 1):
            if airflow_matrix[row, column] == 0:
                airflow_matrix[row, column] = -0.0001
    outdoor_heat = airflow_matrix[-1, :-1] * (outdoor_temperature * 1.2 / 3600 * 1005)
    enthalpy = heat_loads + outdoor_heat
    airflow_matrix *= 1.2 / 3600 * 1005
    return 273.15 - np.linalg.solve(airflow_matrix[:-1, :-1].T, enthalpy)


def read_path_result(project_file):
    """Return volumetric flow by path from a completed CONTAM project."""
    airflow = read_flowpath(project_file[:-4] + ".lfr") * 3600.0 / AIR_DENSITY
    topology = read_topology(project_file)
    return {
        index: {
            "from": topology[index][0],
            "to": topology[index][1],
            "flow": airflow[index][0] + airflow[index][1],
        }
        for index in range(len(topology))
    }
