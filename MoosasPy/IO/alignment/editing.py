from __future__ import annotations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from .ontology import IDF_NAMESPACE, decodeURI, idf, normalize_to_list


def _first(values):
    values = normalize_to_list(values)
    return values[0] if len(values) > 0 else None


def _local_name(value) -> str:
    text = str(value)
    if text.startswith(IDF_NAMESPACE):
        text = text[len(IDF_NAMESPACE) :]
    return decodeURI(text)


def _class_name(graph: Graph, object_uri) -> str:
    class_uri = _first(list(graph.objects(object_uri, idf.instanceOf)))
    return "" if class_uri is None else _local_name(class_uri).upper()


def _field_name(graph: Graph, field_uri) -> str:
    field_uri = _first(list(graph.objects(field_uri, idf.instanceOf)))
    return "" if field_uri is None else _local_name(field_uri).upper()


def iter_idf_objects(graph: Graph, class_name: str | None = None, owner_uri=None):
    """Yield existing IDF object URIs, optionally filtered by class and owner."""
    expected_class = class_name.upper() if class_name is not None else None
    owner = URIRef(owner_uri) if owner_uri is not None else None
    candidates = set(graph.subjects(RDF.type, idf.idfObject)) | set(graph.subjects(RDF.type, idf.idfUniqueObject))
    if owner is not None:
        candidates &= set(graph.objects(owner, idf.hasIDFObject)) | set(graph.subjects(idf.belongsToMoosas, owner))
    for object_uri in candidates:
        if expected_class is None or _class_name(graph, object_uri) == expected_class:
            yield object_uri


def find_idf_field(graph: Graph, object_uri, field_name: str):
    """Return an existing IDF field URI on an object, or None."""
    expected_field = field_name.upper()
    object_uri = URIRef(object_uri)
    for field_uri in graph.objects(object_uri, idf.hasField):
        if _field_name(graph, field_uri) == expected_field:
            return field_uri
    return None


def get_idf_field_value(graph: Graph, object_uri, field_name: str):
    """Return the current value of an existing IDF field, or None."""
    field_uri = find_idf_field(graph, object_uri, field_name)
    if field_uri is None:
        return None
    value = _first(list(graph.objects(field_uri, idf.hasValue)))
    return None if value is None else value.toPython() if isinstance(value, Literal) else str(value)


def set_idf_field_value(graph: Graph, object_uri, field_name: str, value) -> None:
    """Update an existing IDF field value without changing object/field structure."""
    field_uri = find_idf_field(graph, object_uri, field_name)
    if field_uri is None:
        raise KeyError(f"IDF field not found: {object_uri} / {field_name}")
    graph.remove((field_uri, idf.hasValue, None))
    graph.add((field_uri, idf.hasValue, Literal(value)))
