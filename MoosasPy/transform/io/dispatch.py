"""Semantic-model file adapters selected by file suffix."""
from __future__ import annotations

import os
import uuid

from ._geo import writeGeo
from ._ifc import loadIfc, rdf_to_ifc
from ._json import loadJson, writeJson
from ._rdf import loadRDF, writeRDF
from ._xml import loadXml, writeXml
from ...utils import path


def _temp_rdf_path(prefix: str) -> str:
    return os.path.join(path.tempDir, f"{prefix}_{uuid.uuid4().hex}.rdf")


def _remove_temp_file(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)


def _scalarize_offset(value):
    if value is None:
        return 0.0
    if isinstance(value, (list, tuple)):
        return _scalarize_offset(value[0]) if value else 0.0
    if hasattr(value, "flatten"):
        flat = value.flatten()
        return float(flat[0]) if len(flat) else 0.0
    return float(value)


def _normalize_offsets_for_rdf(model) -> list[tuple[object, object]]:
    restored = []
    for element in model.getAllFaces(False):
        if not hasattr(element, "offset"):
            continue
        previous = element.offset
        normalized = _scalarize_offset(previous)
        if normalized != previous:
            restored.append((element, previous))
            element.offset = normalized
    return restored


def _restore_offsets(restored: list[tuple[object, object]]) -> None:
    for element, offset in restored:
        element.offset = offset


def load(file_path: str):
    """Load a complete :class:`MoosasModel` from RDF, XML, JSON, or IFC."""
    suffix = os.path.splitext(file_path)[1].lower()
    geo_path = os.path.splitext(file_path)[0] + ".geo"
    if suffix in {".rdf", ".ttl"}:
        return loadRDF(file_path, fileFormat="turtle")
    if suffix == ".xml":
        return loadXml(file_path, geo_path)
    if suffix == ".json":
        return loadJson(file_path, geo_path)
    if suffix == ".ifc":
        return loadIfc(file_path)
    raise ValueError(f"Unsupported model format: {suffix or file_path}")


def save(model, out_path: str) -> None:
    """Save a complete :class:`MoosasModel` as RDF, XML, JSON, or IFC."""
    suffix = os.path.splitext(out_path)[1].lower()
    path.checkBuildDir(out_path)
    if suffix in {".rdf", ".ttl"}:
        writeRDF(model, out_path, fileFormat="turtle")
    elif suffix == ".xml":
        writeXml(out_path, model)
        writeGeo(os.path.splitext(out_path)[0] + ".geo", geoList=model.geometryList)
    elif suffix == ".json":
        writeJson(out_path, model)
        writeGeo(os.path.splitext(out_path)[0] + ".geo", geoList=model.geometryList)
    elif suffix == ".ifc":
        restored_offsets = _normalize_offsets_for_rdf(model)
        temp_rdf_path = _temp_rdf_path("ifc_save")
        try:
            writeRDF(model, temp_rdf_path, fileFormat="turtle")
            rdf_to_ifc(temp_rdf_path, out_path, rdf_format="turtle")
        finally:
            _restore_offsets(restored_offsets)
            _remove_temp_file(temp_rdf_path)
    else:
        raise ValueError(f"Unsupported model format: {suffix or out_path}")
