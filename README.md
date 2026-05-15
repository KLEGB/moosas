# MOOSAS

MOOSAS is a building performance analysis and optimization toolkit for the
early design stage.

This repository contains:

- `MoosasPy`: core Python package for geometry transformation, I/O, weather,
  energy, radiation, and ventilation workflows.
- `MoosasPy/src`: SketchUp plugin Ruby scripts.
- `setup`: bundled runtime assets used by the desktop/plugin workflow.

## Version

Current Python package release target: `MoosasPy 1.0.0`.

## Quick Start

Install Python dependencies for local development:

```bash
pip install -r requirements.txt
```

Run a basic import check:

```bash
python -c "import MoosasPy; print(MoosasPy.__version__)"
```

## MoosasPy Packaging and Release

Packaging metadata is managed from repository root via `pyproject.toml`.

Read:

- [MoosasPy README](MoosasPy/README.md)
- [MoosasPy publish guide](MoosasPy/PUBLISH_GITHUB_PACKAGES.md)

Current release workflow:

1. Build and validate distributions (`python -m build`, `python -m twine check dist/*`).
2. Push tag `moosaspy-v*` (for example `moosaspy-v1.0.0`).
3. GitHub Actions workflow `.github/workflows/moosaspy-release.yml` uploads
   wheel/sdist to GitHub Release assets.

## SketchUp Plugin Notes

SketchUp plugin source is under `src`.

If you need plugin packaging/deployment, use the repository scripts (for
example `toSketchUp.py`) and follow local environment assumptions documented in
project docs.

## Documentation

- User manual PDF: `MoosasPy/doc/Users Manual.pdf`
- Transformation and module docs: `MoosasPy/doc/document.md`


## Contact

Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.  
**For colaboration, Please contact:**  
linbr@tsinghua.edu.cn  
**If you have any technical problems, Please reach to:**  
junx026@gmail.com
