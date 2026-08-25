# MoosasPy Documentation

## Overview

MoosasPy is a Python toolkit for building geometry processing and building-performance analysis. It provides geometry transformation, model I/O, weather and sky models, radiation and sunlight calculations, simplified energy analysis, and airflow-network preparation.

This repository is Python-only. It does not contain the previous SketchUp plugin, Ruby sources, or browser UI compatibility layer.

## Architecture

```mermaid
flowchart TB
	User[User code] --> API[MoosasPy public API]

	API --> Transform[Transform pipeline]
	API --> IO[Model I/O]
	API --> Simulation[Simulation workflows]

	Transform --> Geometry[Geometry and topology]
	Transform --> Model[MoosasModel]
	IO --> Model

	Simulation --> Energy[Energy]
	Simulation --> Radiation[Radiation and sunlight]
	Simulation --> Weather[Weather and sky]
	Simulation --> Airflow[Airflow and CONTAM]
	Simulation --> Coupling[Energy-airflow coupling]

	Energy --> Model
	Radiation --> Model
	Airflow --> Model
	Coupling --> Energy
	Coupling --> Airflow
	Weather --> Energy
	Weather --> Radiation

	Model --> Utils[Shared utilities]
	Transform --> Utils
	Simulation --> Utils
	Energy --> Resources[Runtime resources: data, db, libs]
	Radiation --> Resources
	Airflow --> Resources
```

## Requirements and Installation

MoosasPy requires Python 3.10 or newer. Install the package from the repository root:

```bash
python -m pip install .
```

For tests and release tooling, install the development extras:

```bash
python -m pip install -e ".[dev]"
```

Verify the package import:

```bash
python -c "import MoosasPy; print(MoosasPy.__version__)"
```

## Quick Start

Convert a supported geometry file into a structured `MoosasModel`:

```python
from MoosasPy.transform import save, transform

model = transform("example.obj", output_path="model.xml", stdout=None)
save(model, "model.rdf")
```

`transform()` accepts geometry input such as OBJ, XML, GEO, and STL according to the active I/O implementation. It can clean duplicate or redundant faces, resolve overlaps, split wall surfaces, generate spaces, and write the result when an output path is supplied.

## Public API

The top-level `MoosasPy` package has three operational API areas:

| API | Purpose |
| --- | --- |
| `transform` | Transform source geometry into a structured building model. |
| `load` / `save` | Load and save complete `MoosasModel` serializations. |
| `simulation` | Access energy, radiation, airflow, weather, and coupled simulation domains. |

```python
from MoosasPy import load, save, simulation, transform

model = transform.transform("example.obj", stdout=None)
energy = simulation.energy.EnergyRunner(model=model).run()
save(model, "model.rdf")
```

Domain-level APIs are accessed from `simulation`, for example
`simulation.radiation.positionRadiation` and `simulation.weather.includeEpw`.

## Package Layout

| Path | Contents |
| --- | --- |
| `MoosasPy/models.py` | Shared `MoosasModel` domain model and its building templates, schedules, and weather state. |
| `MoosasPy/transform/` | Public transformation pipeline and model conversion boundary. |
| `MoosasPy/transform/alignment/` | Geometric alignment and coordinate-processing helpers. |
| `MoosasPy/transform/geometry/` | Geometry primitives, topology cleansing, contours, and space generation. |
| `MoosasPy/transform/io/` | File-format adapters and dispatch for complete RDF, XML, JSON, and IFC models. |
| `MoosasPy/simulation/airflow/` | Airflow-network and CONTAM project preparation, execution, and iteration. |
| `MoosasPy/simulation/coupling/` | Cross-domain workflows such as coupled energy and airflow analysis. |
| `MoosasPy/simulation/energy/` | Simplified energy analysis, photovoltaic calculations, and thermal-load helpers. |
| `MoosasPy/simulation/radiation/` | Radiation geometry export, ray tests, sunlight, and Radiance daylight workflows. |
| `MoosasPy/simulation/weather/` | Weather locations, EPW import, direct sky, and cumulative sky models. |
| `MoosasPy/utils/` | Shared paths, constants, errors, date utilities, and support functions. |
| `MoosasPy/data/` | Legacy runtime example data. New test fixtures belong under `test/`. |
| `MoosasPy/db/` | Building templates, material libraries, schedules, weather data, and EnergyPlus resources. |
| `MoosasPy/libs/` | Native executables and resources used by simulation providers. |
| `MoosasPy/__temp__/` | Runtime workspace excluded from distributions. |

## Model I/O

`MoosasPy.transform.io` provides model loading, saving, and format conversion functions. Common entry points include:

```python
from MoosasPy.transform.io import load, save

model = load("model.xml")
save(model, "model.rdf")
writeGeo("model.geo", model)
writeIDF("model.idf", model)
```

GEO, OBJ, and STL contain only geometric faces and must enter through `transform()`. `load()` accepts complete RDF, XML, JSON, and IFC models; XML and JSON use a same-named `.geo` companion for geometry. RDF is the standard interchange format for simulation adapters, which generate IDF or gbXML when required by an engine.

## Analysis Modules

### Energy

`MoosasPy.simulation.energy.energyAnalysis` performs rapid energy analysis using the native tools under `MoosasPy/libs/energy`. `EnergyRunner` returns structured command diagnostics; `getEnergyInput` and `parseEnergyOutput` remain available for lower-level input and result handling.

### Radiation and Sunlight

`MoosasPy.simulation.radiation` provides `modelRadiation`, `spaceRadiation`, `faceRadiation`, `positionRadiation`, `writeRadGeo`, and `rayTest`. `RadianceRunner` performs isolated Radiance daylight calculations from a model and `RadianceSky`; each run uses a temporary work directory and returns structured daylight metrics and command diagnostics. `positionSunHour` calculates direct sunlight duration using a `Location` or `MoosasDirectSky` instance and either a model or a GEO scene.

### Weather

`MoosasPy.simulation.weather` exports `Location`, `MoosasWeather`, `MoosasCumSky`, `MoosasDirectSky`, and `includeEpw`. These utilities create or import the weather and sky data required by energy, radiation, and sunlight workflows.

### Ventilation

`MoosasPy.simulation.airflow` provides functions to construct airflow-network and CONTAM project files: `buildPrj`, `buildNetworkFile`, `buildZoneInfoFile`, `iterateFile`, `iterateProjects`, `contam_iteration`, and `sensible_heat_iteration`. `MoosasPy.simulation.coupling.EnergyAirflowCoupler` coordinates cross-domain workflows.

## Runtime Resources

The package expects `libs`, `db`, `data`, and `__temp__` to remain adjacent to the Python modules in an installed distribution. Native executables are platform-specific; validate target-platform support before deploying to a non-Windows environment.

## Testing

Keep tests and fixtures under the repository-level `test/` directory. Example data currently located in `MoosasPy/data` is legacy content and should be moved into the relevant test fixture directory when it is no longer needed at runtime.

Run validation from the repository root:

```bash
python -m pytest -q
```

## Packaging and Release

Package metadata is defined in the repository-level `pyproject.toml`. Build distributions from the repository root:

```bash
python -m build
python -m twine check dist/*
```

The version is derived from tags in the form `moosaspy-vMAJOR.MINOR.PATCH`. The GitHub Actions release workflow builds distributions, checks package metadata, and publishes release assets when such a tag is pushed.
