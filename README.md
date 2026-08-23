# MOOSAS

MOOSAS is a building performance analysis and optimization toolkit for the
early design stage.

This repository contains:

- `MoosasPy`: core Python package for geometry transformation, I/O, weather,
  energy, radiation, and ventilation workflows.

## Version

Current Python package release target: `MoosasPy v1.2.2`.

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
2. Push tag `moosaspy-v*` (for example `moosaspy-v1.1.0`).
3. GitHub Actions workflow `.github/workflows/moosaspy-release.yml` uploads
   wheel/sdist to GitHub Release assets.

## Documentation

- Transformation and module docs: `MoosasPy/doc/document.md`

## Contact

Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.  
**For colaboration, Please contact:**  
linbr@tsinghua.edu.cn  
**If you have any technical problems, Please reach to:**  
junx026@gmail.com
liyihui23@mails.tsinghua.edu.cn
