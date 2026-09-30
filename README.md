# MOOSAS

MOOSAS is a building-performance analysis and optimization toolkit for the
early design stage. This repository contains **MoosasPy**, its Python package
for geometry transformation, model exchange, and building-performance
simulation workflows.

## Features

- Transform GEO, OBJ, and STL geometry into a structured `MoosasModel`.
- Load and save RDF/Turtle, XML, JSON, and EnergyPlus IDF models.
- Export graph JSON and gbXML, with dedicated IFC conversion utilities.
- Save a selected room as an OpenFOAM volume mesh through model.save.
- Prepare weather data and cumulative sky models from user-provided EPW files.
- Run rapid energy, solar-radiation, sunlight, Radiance daylight, and CONTAM
  airflow analyses.
- Coordinate weather, radiation, photovoltaic, energy, and airflow domains
  through explicit coupling workflows.
- Isolate native simulations in managed workspaces with structured results and
  command diagnostics.

## Requirements

- Python 3.10 or newer
- EnergyPlus 26.1 IDF input when using the IDF adapters
- A supported platform for workflows that invoke packaged native executables

Bundled CONTAM tools support Windows x86-64 and Linux x86-64. Native-tool
availability should be validated on the target platform before deployment.

## Installation

Install MoosasPy from the repository root:

```bash
python -m pip install .
```

For development, tests, and distribution tooling:

```bash
python -m pip install -e ".[dev]"
```

Verify the installation:

```bash
python -c "import MoosasPy; print(MoosasPy.__version__)"
```

## Quick Start

Transform geometry and save the resulting model:

```python
from MoosasPy.transform import TransformOptions, transform

options = TransformOptions(attach_shading=True)
model = transform("building.geo", options=options, stdout=None)

print(len(model.spaceList))
model.save("building.ttl")
```

Load a complete model without rerunning geometry transformation:

```python
from MoosasPy import MoosasModel

model = MoosasModel.load("building.ttl")
model.summary()
```

Prepare an EPW file, then run energy analysis with the resulting weather object:

```python
from MoosasPy.simulation.energy import EnergyRunner
from MoosasPy.simulation.weather import load_epw

weather = load_epw("custom.epw", "analysis-input/weather")
result = EnergyRunner(model=model, weather=weather).run()
print(result.data["total"])
```

## OpenFOAM Volume Mesh Export

Save a selected constant-section room using the same entry point as IDF:

```python
from MoosasPy.transform import transform

model = transform("test/caseFile/test0_6spacesIntersection.geo", input_type="geo")
result = model.save("cases/room/room.foam", space_index=0, grid_size=0.5, layers=12)
print(result.primary_path)  # cases/room/room.foam
```

This writes a ParaView marker, five mesh files and a `constant/moosasGrid.json`
cell-to-grid mapping. The volume covers the complete footprint, including
clipped perimeter cells and holes; its base is the source face, independent of
the sampling height. All boundary patches default to walls. Use metres for
geometry and supply your own field boundary conditions and solver settings.

This exporter supports a single horizontal floor and constant room height.
It does not support arbitrary room solids, varying ceiling heights, internal obstacles,
or automatic window/door patches. Existing meshes are not overwritten.
See [OpenFOAM export details](doc/openfoam.md) for parameters, mapping semantics,
and `checkMesh` validation.

For an isothermal indoor or outdoor CFD simulation, use the same `model.save`
entry point with `scenario="indoor"` or `scenario="outdoor"` and explicit
`conditions`. It writes a complete OpenFOAM Foundation 12 case:

```python
from MoosasPy.simulation.airflow import OpenFoamRunner

conditions = {
    "viscosity": 1.5e-5,
    "turbulence_intensity": 0.05,
    "turbulence_length": 1.0,
    "iterations": 1000,
    "velocity": [2.0, 0.0, 0.0],
    "domain": [[-100.0, 120.0, 0.0], [0.0, 240.0, 45.0]],
    "inside_point": [-90.0, 130.0, 5.0],
}
saved = model.save("cases/wind/case.foam", scenario="outdoor",
                   grid_size=4, conditions=conditions)
result = OpenFoamRunner(saved.primary_path.parent).run()
print(result.successful, result.converged, result.relative_flow_imbalance)
```

See the [GEO-to-CFD guide](doc/openfoam.md) for runnable indoor/outdoor examples,
environment setup, opening IDs, physical assumptions, and real-GEO verification.
The runner preserves mesh/solver logs and reports nonconvergence explicitly.

## Model and Simulation Domains

| Area | Public entry point |
| --- | --- |
| Geometry transformation | `MoosasPy.transform` |
| Complete model I/O | `MoosasPy.MoosasModel` |
| Energy | `MoosasPy.simulation.energy` |
| Radiation and daylight | `MoosasPy.simulation.radiation` |
| Airflow and CONTAM | `MoosasPy.simulation.airflow` |
| Weather and sky models | `MoosasPy.simulation.weather` |
| Cross-domain workflows | `MoosasPy.simulation.coupling` |

Raw GEO, OBJ, and STL files enter through `transform()`. Complete RDF/Turtle,
XML, JSON, and IDF models enter through `MoosasModel.load()`. MoosasPy reads and
writes EnergyPlus 26.1 IDFs with its bundled 26.1 `Energy+.idd`; older IDFs must
be migrated with the official EnergyPlus Transition chain first.

See the [MoosasPy documentation](doc/document.md) for transformation options,
supported model formats, thermal settings, simulation APIs, native resources,
and release instructions.

## Development

Run the test suite from the repository root:

```bash
python -m pytest -q
```

Build and validate distributions:

```bash
python -m build
python -m twine check dist/*
```

Versions are derived from Git tags matching `moosaspy-vMAJOR.MINOR.PATCH`.
Pushing a matching tag triggers the GitHub Actions release workflow, which
builds the wheel and source distribution and uploads them to a GitHub Release.

## License

MoosasPy is distributed under the Apache License 2.0. See [LICENSE](LICENSE).

## Credits and Contact

Developed by the research team directed by **Prof. Borong Lin** at the Key
Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua
University.

For collaboration: linbr@tsinghua.edu.cn

For technical questions: junx026@gmail.com, liyihui23@mails.tsinghua.edu.cn
