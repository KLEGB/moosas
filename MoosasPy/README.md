# MoosasPy

MoosasPy is the core Python package of MOOSAS for building-geometry processing
and performance analysis workflows.

It includes:

- geometry transformation and space generation
- file I/O (`.geo`, `.xml`, `.rdf`, `.idf`, `.obj`, `.json`)
- weather, radiation, sunlight, and energy-related helpers
- native tool integrations under `MoosasPy/libs`

## Python Version

Use Python `>=3.10`.

## Installation

### Option A: install from GitHub Release asset (current default flow)

Public repository:

```bash
pip install "https://github.com/<OWNER>/<REPO>/releases/download/moosaspy-v1.1.0/moosaspy-1.1.0-py3-none-any.whl"
```

Private repository:

```bash
pip install "https://<USERNAME>:<TOKEN>@github.com/<OWNER>/<REPO>/releases/download/moosaspy-v1.1.0/moosaspy-1.1.0-py3-none-any.whl"
```

### Option B: install by package name

`pip install moosaspy` works only when this package is uploaded to a PyPI-compatible
index (for example PyPI/TestPyPI or a private PyPI service).

## Release (for maintainers)

From repository root:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

Package version is resolved from git tag automatically (`setuptools_scm`).
Tag format must be:

```text
moosaspy-vMAJOR.MINOR.PATCH
```

For example:

```bash
<<<<<<< Updated upstream
git tag -a moosaspy-v1.1.0 -m "MoosasPy 1.1.0"
git push origin moosaspy-v1.1.0
=======
git tag -a moosaspy-v1.0.1 -m "MoosasPy 1.0.1"
git push origin moosaspy-v1.0.1
>>>>>>> Stashed changes
```

The workflow `.github/workflows/moosaspy-release.yml` will build distributions
and upload them as GitHub Release assets.

## Quick Start

```python
from MoosasPy import transform, loadModel, saveModel, energyAnalysis

model = transform("example.geo", input_type="geo", stdout=None)
print(len(model.spaceList))
```

## Notes

- `MoosasPy` is path-sensitive and expects sibling directories such as `libs`,
  `db`, `data`, and `__temp__` inside the installed package.
- importing `MoosasPy` clears files under `MoosasPy/__temp__`.
