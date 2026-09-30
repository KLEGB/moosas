"""Transform a GEO, save a complete OpenFOAM 12 case, mesh and solve it."""

import argparse
from io import StringIO
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from MoosasPy.simulation.airflow import OpenFoamRunner  # noqa: E402
from MoosasPy.transform import transform  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--scenario", choices=("indoor", "outdoor"), required=True)
    parser.add_argument("--conditions", type=Path, required=True)
    parser.add_argument("--space", type=int)
    parser.add_argument("--grid-size", type=float, required=True)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    conditions = json.loads(args.conditions.read_text(encoding="utf-8"))
    model = transform(str(args.source.resolve()), input_type="geo", stdout=StringIO())
    case_dir = args.case.resolve()
    saved = model.save(case_dir / "case.foam", scenario=args.scenario,
                       space_index=args.space, grid_size=args.grid_size, conditions=conditions)
    print(f"Saved {len(saved.generated_paths)} files to {case_dir}", flush=True)
    result = OpenFoamRunner(case_dir, timeout_seconds=args.timeout).run()
    report = {
        "source": str(args.source.resolve()), "scenario": args.scenario,
        "successful": result.successful, "converged": result.converged,
        "time_directory": str(result.time_directory),
        "patch_flows_m3_s": result.patch_flows,
        "relative_flow_imbalance": result.relative_flow_imbalance,
        "warnings": result.warnings,
    }
    (case_dir / "moosasResult.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if result.successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
