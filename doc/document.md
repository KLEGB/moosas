# MoosasPy Documentation

## Overview

MoosasPy is a Python toolkit for building geometry processing and building-performance analysis. It provides geometry transformation, model I/O, weather and sky models, radiation and sunlight calculations, simplified energy analysis, and airflow-network preparation.

This repository is Python-only. It does not contain the previous SketchUp plugin, Ruby sources, or browser UI compatibility layer.

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
from MoosasPy.transformation import save_model, transform

model = transform("example.obj", output_path="model.xml", stdout=None)
save_model(model, "model.rdf")
```

`transform()` accepts geometry input such as OBJ, XML, GEO, and STL according to the active I/O implementation. It can clean duplicate or redundant faces, resolve overlaps, split wall surfaces, generate spaces, and write the result when an output path is supplied.

## Public API

The top-level `MoosasPy` package exposes these primary functions:

| API | Purpose |
| --- | --- |
| `transform` | Transform source geometry into a structured building model. |
| `loadModel` / `saveModel` | Load and save `MoosasModel` instances. |
| `energyAnalysis` | Run the simplified building-energy workflow. |
| `positionRadiation` | Calculate radiation at one or more positions. |
| `positionSunHour` | Calculate average direct-sun hours for one or more rays. |
| `includeEpw` | Import weather data from an EPW file. |

## Package Layout

| Path | Contents |
| --- | --- |
| `MoosasPy/models.py` | Shared `MoosasModel` domain model and its building templates, schedules, and weather state. |
| `MoosasPy/transformation/` | Public transformation pipeline and model conversion boundary. |
| `MoosasPy/transformation/alignment/` | Geometric alignment and coordinate-processing helpers. |
| `MoosasPy/transformation/geometry/` | Geometry primitives, topology cleansing, contours, and space generation. |
| `MoosasPy/transformation/io/` | File-format adapters and dispatch for GEO, XML, JSON, RDF, IFC, IDF, GBXML, OBJ, and graph formats. |
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

`MoosasPy.transformation.io` provides model loading, saving, and format conversion functions. Common entry points include:

```python
from MoosasPy.transformation.io import load_model, save_model, writeGeo, writeIDF

model = load_model("model.xml")
save_model(model, "model.rdf")
writeGeo("model.geo", model)
writeIDF("model.idf", model)
```

Available helpers cover GEO, XML, JSON/GeoJSON, RDF, IFC, GBXML, IDF, and OBJ conversion. Format support can depend on optional dependencies and the input model content.

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
python tools/check_docs.py
python -m pytest -q
```

## Packaging and Release

Package metadata is defined in the repository-level `pyproject.toml`. Build distributions from the repository root:

```bash
python tools/check_docs.py
python -m build
python -m twine check dist/*
```

The version is derived from tags in the form `moosaspy-vMAJOR.MINOR.PATCH`. The GitHub Actions release workflow validates documentation, builds distributions, checks package metadata, and publishes release assets when such a tag is pushed.
