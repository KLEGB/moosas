"""Run model.save-generated OpenFOAM Foundation 12 cases in an active FOAM environment."""

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

import numpy as np

from ..contracts import SimulationResult
from ..runner import Runner, CommandError, CommandTimeoutError


@dataclass(frozen=True)
class OpenFoamResult(SimulationResult):
    time_directory: Path | None = None
    converged: bool = False
    patch_flows: dict[str, float] = field(default_factory=dict)
    relative_flow_imbalance: float = float("inf")

    @property
    def successful(self):
        return super().successful and self.converged and self.relative_flow_imbalance < 0.01


class OpenFoamRunner(Runner):
    """Mesh, check, and solve one exported case; preserve command logs in the case."""

    def __init__(self, case_dir, *, timeout_seconds=300.0, engine=None):
        super().__init__(timeout_seconds=timeout_seconds, engine=engine)
        self.case_dir = Path(case_dir).resolve()

    def run(self):
        manifest = json.loads((self.case_dir / "constant/moosasCase.json").read_text())
        if manifest["openfoam_version"] != 12:
            raise ValueError("This runner requires an OpenFOAM Foundation 12 case")
        if any(_time_value(p) > 0 for p in self.case_dir.iterdir() if p.is_dir()):
            raise FileExistsError("Case already contains solution times; save a fresh case")
        commands = []
        for executable, args in (
            ("surfaceCheck", ("constant/geometry/model.stl",)),
            ("blockMesh", ()),
            ("snappyHexMesh", ("-overwrite",)),
            ("checkMesh", ("-allTopology", "-meshQuality")),
            ("foamRun", ("-solver", "incompressibleFluid")),
        ):
            try:
                result = self.run_command((executable, *args), cwd=self.case_dir)
            except (CommandError, CommandTimeoutError) as error:
                (self.case_dir / f"log.{executable}").write_text(
                    error.stdout + error.stderr, encoding="utf-8")
                raise
            commands.append(result)
            output = result.stdout + result.stderr
            (self.case_dir / f"log.{executable}").write_text(output, encoding="utf-8")
            if executable == "surfaceCheck" and (
                    "Surface is closed" not in output or "Surface has no illegal triangles" not in output):
                raise ValueError("Building/room surface is not closed; see log.surfaceCheck")
            if executable == "checkMesh" and "Mesh OK" not in output:
                raise ValueError("OpenFOAM mesh checks failed; see log.checkMesh")
        times = [p for p in self.case_dir.iterdir() if p.is_dir() and _time_value(p) > 0]
        if not times:
            raise ValueError("Solver did not write a solution time")
        latest = max(times, key=_time_value)
        field_sizes = [_check_field(latest / name) for name in ("U", "p", "k", "epsilon")]
        if len({size for size in field_sizes if size is not None}) > 1:
            raise ValueError("Solution fields have inconsistent cell counts")
        flows = {}
        for name in manifest["flow_patches"]:
            files = sorted((self.case_dir / "postProcessing" / f"flow_{name}").glob("*/surfaceFieldValue.dat"))
            if len(files) != 1:
                raise ValueError(f"Expected one flow report for patch {name}")
            rows = [line.split() for line in files[0].read_text().splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
            if not rows or float(rows[-1][0]) != _time_value(latest):
                raise ValueError(f"Flow report and solution time disagree for {name}")
            flows[name] = float(rows[-1][1])
        if not flows or not np.isfinite(list(flows.values())).all():
            raise ValueError("Missing or non-finite boundary fluxes")
        inflow = -sum(value for value in flows.values() if value < 0)
        imbalance = abs(sum(flows.values())) / inflow if inflow > 0 else float("inf")
        converged = "solution converged" in commands[-1].stdout.lower()
        warnings = []
        if not converged:
            warnings.append("Solver reached its iteration limit without meeting residual tolerances")
        if imbalance >= 0.01:
            warnings.append("Boundary flow imbalance is at least 1 percent")
        return OpenFoamResult(commands=tuple(commands), warnings=tuple(warnings),
                              time_directory=latest, converged=converged,
                              patch_flows=flows, relative_flow_imbalance=imbalance)


def _time_value(path):
    try:
        return float(path.name)
    except ValueError:
        return -1.0


def _check_field(path):
    document = path.read_text()
    match = re.search(r"internalField\s+(?:nonuniform\s+List<(\w+)>\s+(\d+)\s*\((.*?)\)\s*;|uniform\s+(.*?);)",
                      document, re.S)
    if not match:
        raise ValueError(f"Missing internal field in {path}")
    numbers = (match[3] if match[3] is not None else match[4]).replace("(", " ").replace(")", " ").split()
    if not numbers or not np.isfinite([float(number) for number in numbers]).all():
        raise ValueError(f"Non-finite solution in {path}")
    if match[2] is not None:
        count = int(match[2])
        if len(numbers) != count * (3 if match[1] == "vector" else 1):
            raise ValueError(f"Truncated solution in {path}")
        return count
    return None
