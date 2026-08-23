# MoosasPy Documentation

## Overview

MoosasPy is a Python toolkit for building geometry processing and building-performance analysis. It provides geometry transformation, model I/O, weather and sky models, radiation and sunlight calculations, simplified energy analysis, and airflow-network preparation.

This repository is Python-only. It does not contain the previous SketchUp plugin, Ruby sources, or browser UI compatibility layer.

## Requirements and Installation

MoosasPy requires Python 3.10 or newer. Install the development dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

Verify the package import:

```bash
python -c "import MoosasPy; print(MoosasPy.__version__)"
```

## Quick Start

Convert a supported geometry file into a structured `MoosasModel`:

```python
from MoosasPy import loadModel, saveModel, transform

model = transform("example.obj", output_path="model.xml", stdout=None)
saveModel(model, "model.rdf")
loaded_model = loadModel("model.rdf")
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
| `geometry/` | Geometry primitives, topology, cleansing, grids, contours, and space generation. |
| `IO/` | Model readers and writers for GEO, XML, JSON, RDF, IFC, IDF, GBXML, OBJ, and related formats. |
| `encoding/` | Encoding and graph utilities, including geometry convexification support. |
| `simulation/energy/` | Simplified energy analysis, photovoltaic calculations, and thermal-load helpers. |
| `simulation/rad/` | Radiation geometry export, ray tests, cumulative-sky calculations, Radiance daylight workflows, and quick daylight-factor estimates. |
| `simulation/weather/` | Weather locations, EPW import, direct sky, and cumulative sky models. |
| `simulation/vent/` | Airflow-network and CONTAM project preparation and iteration helpers. |
| `simulation/thermal/` | Thermal constructions, zones, schedules, and IDF geometry support. |
| `visual/` | Geometry visualization helpers. |
| `utils/` | Shared paths, constants, errors, date utilities, and support functions. |
| `libs/` | Native executables and resources used by energy, radiation, ventilation, and weather workflows. |
| `db/` | Building templates, material libraries, schedules, weather data, and EnergyPlus resources. |
| `data/` | Legacy example inputs. New test fixtures should be kept under `test/`. |
| `__temp__/` | Runtime workspace cleared during package import; it is excluded from distributions. |

## Model I/O

The `MoosasPy.IO` module provides model loading, saving, and format conversion functions. Common entry points include:

```python
from MoosasPy import IO

model = IO.loadModel("model.xml")
IO.saveModel(model, "model.rdf")
IO.writeGeo("model.geo", model)
IO.writeIDF("model.idf", model)
```

Available helpers cover GEO, XML, JSON/GeoJSON, RDF, IFC, GBXML, IDF, and OBJ conversion. Format support can depend on optional dependencies and the input model content.

## Analysis Modules

### Energy

`MoosasPy.simulation.energy.energyAnalysis` performs rapid energy analysis using the native tools under `MoosasPy/libs/energy`. Use `getEnergyInput` and `parseEnergyOutput` for lower-level input and result handling.

### Radiation and Sunlight

`MoosasPy.simulation.rad` provides `modelRadiation`, `spaceRadiation`, `faceRadiation`, `positionRadiation`, `writeRadGeo`, and `rayTest`. `RadianceRunner` performs isolated Radiance daylight calculations from a model and `RadianceSky`; each run uses a temporary work directory and returns structured daylight metrics and command diagnostics. `positionSunHour` calculates direct sunlight duration using a `Location` or `MoosasDirectSky` instance and either a model or a GEO scene.

### Weather

`MoosasPy.simulation.weather` exports `Location`, `MoosasWeather`, `MoosasCumSky`, `MoosasDirectSky`, and `includeEpw`. These utilities create or import the weather and sky data required by energy, radiation, and sunlight workflows.

### Ventilation

`MoosasPy.simulation.vent` provides functions to construct airflow-network and CONTAM project files: `buildPrj`, `buildNetworkFile`, `buildZoneInfoFile`, `iterateFile`, `iterateProjects`, `contam_iteration`, and `sensible_heat_iteration`.

## Runtime Resources

The package expects `libs`, `db`, `data`, and `__temp__` to remain adjacent to the Python modules in an installed distribution. Native executables are platform-specific; validate target-platform support before deploying to a non-Windows environment.

## Testing

Keep tests and fixtures under the repository-level `test/` directory. Example data currently located in `MoosasPy/data` is legacy content and should be moved into the relevant test fixture directory when it is no longer needed at runtime.

Run the available test suite from the repository root with the project test command used by your environment. For a fast syntax check:

```bash
python -m compileall -q MoosasPy
```

## Packaging and Release

Package metadata is defined in the repository-level `pyproject.toml`. Build distributions from the repository root:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

The version is derived from tags in the form `moosaspy-vMAJOR.MINOR.PATCH`. The GitHub Actions release workflow builds and publishes release assets when such a tag is pushed.
