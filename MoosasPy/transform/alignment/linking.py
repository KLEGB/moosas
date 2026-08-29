from __future__ import annotations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from .ontology import decodeURI, edGraph, encodeURI, idf, normalize_to_list


def _first(values):
    values = normalize_to_list(values)
    return values[0] if len(values) > 0 else None


def _literal_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, Literal):
        return str(value.toPython())
    return str(value)


def _idf_class(graph: Graph, node) -> str:
    value = _first(list(graph.objects(node, idf.instanceOf)))
    return "" if value is None else str(value)


def _idf_class_name(graph: Graph, node) -> str:
    class_uri = _idf_class(graph, node)
    return decodeURI(class_uri).upper()


def _idf_name(graph: Graph, node) -> str:
    return _literal_text(_first(list(graph.objects(node, idf.name)))).strip()


def _field_value(graph: Graph, object_uri, field_name: str) -> str:
    target_field = encodeURI(field_name)
    for field_uri in graph.objects(object_uri, idf.hasField):
        if _first(list(graph.objects(field_uri, idf.instanceOf))) == target_field:
            return _literal_text(_first(list(graph.objects(field_uri, idf.hasValue)))).strip()
    return ""


def _iter_model_elements(model, dumpUseless=True):
    getter = getattr(model, "getAllFaces", None)
    if not callable(getter):
        return []
    elements = getter(dumpUseless=dumpUseless)
    if isinstance(elements, dict):
        flattened = []
        for values in elements.values():
            flattened.extend(list(values))
        return flattened
    return list(elements)


def _copy_with_subject_map(source: Graph, uri_map: dict[URIRef, URIRef]) -> edGraph:
    retval = edGraph()
    for prefix, uri in source.namespaces():
        retval.bind(prefix, uri)
    for s, p, o in source:
        retval.add((uri_map.get(s, s), p, uri_map.get(o, o) if isinstance(o, URIRef) else o))
    return retval


def _map_surface_name_to_element(model, object_name: str) -> URIRef | None:
    for element in _iter_model_elements(model, dumpUseless=True):
        uid = str(getattr(element, "Uid", ""))
        if not uid:
            continue
        if object_name == uid or object_name.endswith("-" + uid) or ("-" + uid + "-") in object_name:
            return URIRef(f"element_{uid}")
    return None


def link_idf_graph_to_moosas(idf_graph: Graph, model) -> tuple[edGraph, dict[str, str]]:
    """Rewrite selected IDF object URIs to MOOSAS Space/Element URIs and attach owner links."""
    uri_map: dict[URIRef, URIRef] = {}
    reverse_space = {str(space.id): URIRef(f"Space_{space.id}") for space in getattr(model, "spaceList", [])}

    for obj_uri in set(idf_graph.subjects(RDF.type, idf.idfObject)) | set(idf_graph.subjects(RDF.type, idf.idfUniqueObject)):
        class_name = _idf_class_name(idf_graph, obj_uri)
        object_name = _idf_name(idf_graph, obj_uri)
        if class_name == "ZONE" and object_name in reverse_space:
            uri_map[URIRef(obj_uri)] = reverse_space[object_name]
        elif class_name in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
            element_uri = _map_surface_name_to_element(model, object_name)
            if element_uri is not None:
                uri_map[URIRef(obj_uri)] = element_uri

    linked = _copy_with_subject_map(idf_graph, uri_map)

    for obj_uri in list(linked.subjects(RDF.type, idf.idfObject)):
        class_name = _idf_class_name(linked, obj_uri)
        owner = None
        zone_name = _field_value(linked, obj_uri, "Zone_Name")
        if not zone_name:
            zone_name = _field_value(linked, obj_uri, "Zone_or_ZoneList_Name")
        if not zone_name:
            zone_name = _field_value(linked, obj_uri, "Zone_or_ZoneList_or_Space_or_SpaceList_Name")
        if not zone_name:
            zone_name = _field_value(linked, obj_uri, "Zone_or_Space_Name")
        if zone_name in reverse_space:
            owner = reverse_space[zone_name]
        if owner is not None:
            linked.add((obj_uri, idf.belongsToMoosas, owner))
            linked.add((owner, idf.hasIDFObject, obj_uri))

        if class_name in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
            linked.add((obj_uri, idf.hasIDFObject, obj_uri))

    return linked, {str(k): str(v) for k, v in uri_map.items()}


def merge_moosas_and_idf_graphs(moosas_graph: Graph, idf_graph: Graph | None) -> Graph:
    if idf_graph is None:
        return moosas_graph
    merged = Graph()
    for graph in (moosas_graph, idf_graph):
        for prefix, uri in graph.namespaces():
            merged.bind(prefix, uri)
        for triple in graph:
            merged.add(triple)
    return merged


def extract_idf_graph(combined_graph: Graph) -> edGraph | None:
    idf_triples = edGraph()
    for prefix, uri in combined_graph.namespaces():
        idf_triples.bind(prefix, uri)

    idf_nodes = set()
    for s in combined_graph.subjects(RDF.type, idf.idfObject):
        idf_nodes.add(s)
    for s in combined_graph.subjects(RDF.type, idf.idfUniqueObject):
        idf_nodes.add(s)
    for s in combined_graph.subjects(RDF.type, idf.fieldInstance):
        idf_nodes.add(s)
    for s in combined_graph.subjects(RDF.type, encodeURI("OUTPUT:VARIABLE")):
        idf_nodes.add(s)

    added_count = 0
    changed = True
    while changed:
        changed = False
        for s, p, o in combined_graph:
            if str(p).startswith(str(idf)) or s in idf_nodes or (isinstance(o, URIRef) and o in idf_nodes):
                if (s, p, o) not in idf_triples:
                    idf_triples.add((s, p, o))
                    added_count += 1
                if isinstance(s, URIRef) and s not in idf_nodes and str(p).startswith(str(idf)):
                    idf_nodes.add(s)
                    changed = True
                if isinstance(o, URIRef) and o not in idf_nodes and str(p).startswith(str(idf)):
                    idf_nodes.add(o)
                    changed = True

    return idf_triples if added_count > 0 else None
