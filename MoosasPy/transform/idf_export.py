"""Asynchronous SketchUp-side IDF export entrypoint.

This module deliberately owns all IDF conversion work so the SketchUp Ruby
layer only needs to launch Python and report completion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from MoosasPy.model.io import load_model
from MoosasPy.model.io.idf import exportIDF


def export_idf_batch(
    rdf_paths: Iterable[str], output_dir: str, template_path: str | None = None
) -> str:
    """Convert one or more Moosas Turtle models to IDF files.

    Returns the path of a JSON manifest containing the generated IDF paths.
    Exceptions are intentionally allowed to propagate so the Ruby async runner
    can surface the full Python traceback in ``error.log``.
    """

    sources = [Path(path).resolve() for path in rdf_paths]
    if not sources:
        raise ValueError("No RDF/Turtle sources were supplied for IDF export.")
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing RDF/Turtle source(s): " + ", ".join(missing))

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    for index, source in enumerate(sources, start=1):
        output_path = destination / f"{source.stem}.idf"
        print(f"IDF export {index}/{len(sources)}: {source.name} -> {output_path.name}")
        model = load_model(source)
        exportIDF(model, str(output_path), idfTemplatePath=template_path)
        generated.append(str(output_path))

    manifest_path = destination / "idf_export_manifest.json"
    manifest_path.write_text(
        json.dumps({"sources": [str(path) for path in sources], "idf_files": generated}, indent=2),
        encoding="utf-8",
    )
    print(f"IDF export complete: {manifest_path}")
    return str(manifest_path)
