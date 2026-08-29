"""Strict file-format dispatch for complete ``MoosasModel`` objects."""

from __future__ import annotations

from pathlib import Path
import tempfile

from .result import SaveResult
from ...utils import path as path_utils


def _model_format(file_path: str | Path) -> str:
    path = Path(file_path)
    name = path.name.lower()
    if name.endswith(".graph.json"):
        return "graph"
    return path.suffix.lower().lstrip(".")


def _geo_sidecar(file_path: Path) -> Path:
    return file_path.with_suffix(".geo")


def load_model(file_path: str | Path):
    """Load RDF, XML, JSON, or IDF into a complete ``MoosasModel``."""
    source = Path(file_path)
    model_format = _model_format(source)

    if model_format in {"rdf", "ttl"}:
        from .rdf import loadRDF

        return loadRDF(str(source), fileFormat="turtle")
    if model_format == "xml":
        from .xml import loadXml

        return loadXml(str(source), str(_geo_sidecar(source)))
    if model_format == "json":
        from .json import loadJson

        return loadJson(str(source), str(_geo_sidecar(source)))
    if model_format == "idf":
        from .idf import readIDF

        return readIDF(str(source)).model

    raise ValueError(f"Unsupported model load format: {model_format or source}")


def save_model(model, file_path: str | Path) -> SaveResult:
    """Save a model using the capabilities defined for the target format."""
    target = Path(file_path)
    model_format = _model_format(target)
    supported_formats = {"rdf", "ttl", "xml", "json", "idf", "graph", "gbxml"}
    if model_format not in supported_formats:
        raise ValueError(f"Unsupported model save format: {model_format or target}")
    path_utils.checkBuildDir(str(target))

    if model_format in {"rdf", "ttl"}:
        from .rdf import writeRDF

        writeRDF(model, str(target), fileFormat="turtle")
        generated = (target,)
    elif model_format == "xml":
        from .xml import writeXml
        from ...transform.importers.geo import writeGeo

        sidecar = _geo_sidecar(target)
        writeXml(str(target), model)
        writeGeo(str(sidecar), geoList=model.geometryList)
        generated = (target, sidecar)
    elif model_format == "json":
        from .json import writeJson
        from ...transform.importers.geo import writeGeo

        sidecar = _geo_sidecar(target)
        writeJson(str(target), model)
        writeGeo(str(sidecar), geoList=model.geometryList)
        generated = (target, sidecar)
    elif model_format == "idf":
        from .idf import writeIDF

        writeIDF(model, str(target))
        generated = (target,)
    elif model_format == "graph":
        from .graph import writeGraph

        writeGraph(str(target), model)
        generated = (target,)
    elif model_format == "gbxml":
        from .gbxml import convert_rdf_to_gbxml
        from .rdf import writeRDF

        with tempfile.TemporaryDirectory(prefix="moosas_gbxml_") as directory:
            rdf_path = Path(directory) / "model.ttl"
            writeRDF(model, str(rdf_path), fileFormat="turtle")
            convert_rdf_to_gbxml(rdf_path, target, rdf_format="turtle")
        generated = (target,)
    return SaveResult(primary_path=target, generated_paths=generated)
