"""Export one room from a GEO fixture as an OpenFOAM case.

Run from the repository root, for example:

    python example/export_openfoam_room.py
"""

from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from MoosasPy.model.io import export_openfoam  # noqa: E402
from MoosasPy.transform import transform  # noqa: E402
from MoosasPy.transform.geometry.grid import MoosasGrid  # noqa: E402


DEFAULT_SOURCE = PROJECT_ROOT / "test" / "caseFile" / "test0_6spacesIntersection.geo"
DEFAULT_CASE = PROJECT_ROOT / "temp" / "openfoam-test0-space0"


def write_case_dictionaries(case_dir: Path) -> tuple[Path, ...]:
    """Create the minimal OpenFOAM dictionaries needed by checkMesh."""
    system = case_dir / "system"
    system.mkdir(exist_ok=False)
    header = "FoamFile\n{\n    version 2.0;\n    format ascii;\n    class dictionary;\n"
    files = {
        system / "controlDict": header
        + "    object controlDict;\n}\n"
        + "application checkMesh;\nstartFrom startTime;\nstartTime 0;\n"
        + "stopAt endTime;\nendTime 1;\ndeltaT 1;\n"
        + "writeControl timeStep;\nwriteInterval 1;\n",
        system / "fvSchemes": header
        + "    object fvSchemes;\n}\n"
        + "ddtSchemes { default steadyState; }\n"
        + "gradSchemes { default Gauss linear; }\n"
        + "divSchemes { default none; }\n"
        + "laplacianSchemes { default Gauss linear corrected; }\n"
        + "interpolationSchemes { default linear; }\n"
        + "snGradSchemes { default corrected; }\n",
        system / "fvSolution": header
        + "    object fvSolution;\n}\nsolvers {}\n",
    }
    for path, contents in files.items():
        path.write_text(contents, encoding="ascii", newline="\n")
    return tuple(files)


def export_room(
    source: Path,
    case_dir: Path,
    *,
    space_index: int,
    grid_size: float,
    layers: int,
):
    """Transform a GEO model and export one room's floor as a volume mesh."""
    model = transform(str(source), input_type="geo", stdout=StringIO())
    if not 0 <= space_index < len(model.spaceList):
        raise IndexError(
            f"space_index {space_index} is outside 0..{len(model.spaceList) - 1}"
        )

    space = model.spaceList[space_index]
    if space.floor is None or len(space.floor.face) != 1:
        raise ValueError("The selected room must have exactly one floor face")

    grid = MoosasGrid(space.floor.face[0], gird_size=grid_size, grid_offset=0.78)
    result = export_openfoam(
        grid,
        case_dir,
        height=space.height,
        layers=layers,
    )
    write_case_dictionaries(case_dir)

    # ParaView recognizes an empty .foam marker and reads constant/polyMesh.
    marker = case_dir / f"{case_dir.name}.foam"
    marker.touch(exist_ok=False)
    return model, space, grid, result, marker


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--space", type=int, default=0, dest="space_index")
    parser.add_argument("--grid-size", type=float, default=1.0)
    parser.add_argument("--layers", type=int, default=8)
    args = parser.parse_args()

    model, space, grid, result, marker = export_room(
        args.source.resolve(),
        args.case.resolve(),
        space_index=args.space_index,
        grid_size=args.grid_size,
        layers=args.layers,
    )
    print(f"Spaces in model: {len(model.spaceList)}")
    print(f"Exported space: {args.space_index} ({space.id})")
    print(f"Floor area: {space.area:.3f} m2")
    print(f"Height: {space.height:.3f} m")
    print(f"Valid MoosasGrid samples: {len(grid.gridPoints)}")
    print(f"OpenFOAM mesh: {result.primary_path}")
    print(f"ParaView marker: {marker}")


if __name__ == "__main__":
    main()
