from __future__ import annotations

import re
from difflib import SequenceMatcher

from eppy.modeleditor import IDF
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from .ontology import (
    decodeURI,
    default_idd_path,
    default_template_idf_path,
    edGraph,
    encodeURI,
    idf,
    normalize_to_list,
)


def _safe_set_idd(idd_path: str | None) -> None:
    if not idd_path:
        return
    try:
        IDF.setiddname(idd_path)
    except Exception:
        # Eppy rejects resetting IDD in many long-lived Python processes.
        pass


def _first(value):
    values = normalize_to_list(value)
    return values[0] if len(values) > 0 else None


def find_closest_field(field_list: list, target_field: str) -> str:
    escaped_target = re.escape(target_field)
    pattern = re.compile(f".*{escaped_target}.*", re.IGNORECASE)
    candidates = [field for field in field_list if pattern.match(str(field))]
    if not candidates:
        candidates = field_list

    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, str(a).strip(), str(b).strip()).ratio()

    sorted_candidates = sorted(
        candidates,
        key=lambda x: (similarity(x, target_field), -abs(len(str(x)) - len(target_field))),
        reverse=True,
    )
    return sorted_candidates[0] if sorted_candidates else ""


def IDFtoOWL(idf_path: str, idd_path: str | None = None) -> edGraph:
    """Translate an EnergyPlus IDF into an RDF graph of IDF objects and fields."""
    _safe_set_idd(default_idd_path(idd_path))
    rootFile = IDF(idf_path)
    rootGraph = edGraph()

    def encodedObject(objectName, className, obj, objectType):
        memo = " ".join(obj.objidd[0]["memo"]) if "memo" in obj.objidd[0] else "This class has no comment"
        object_uri = rootGraph.encode_entity(
            name=str(objectName) + str(className),
            entityType=objectType,
            description=memo,
            label=f"{className} {objectName}",
        )
        rootGraph.add((object_uri, idf.instanceOf, encodeURI(className)))
        rootGraph.add((object_uri, idf.name, Literal(objectName)))

        for idx, fieldIdd in enumerate(obj.objidd[1:len(obj.obj)]):
            fieldName = obj.objls[idx + 1]
            description = f"{fieldName} instance for the object {objectName} in class {className}"
            field_uri = rootGraph.encode_entity(
                name=str(objectName) + str(fieldName),
                entityType=idf.fieldInstance,
                description=description,
                label=f"{className} {objectName} {fieldName}",
            )
            rootGraph.add((object_uri, idf.hasField, field_uri))
            rootGraph.add((field_uri, idf.instanceOf, encodeURI(fieldName)))
            rootGraph.add((field_uri, idf.name, Literal(fieldName)))
            fieldValue = obj.obj[idx + 1]
            if fieldValue != "":
                if "type" in fieldIdd and fieldIdd["type"][0] == "object-list":
                    rootGraph.add((field_uri, idf.hasValue, encodeURI(fieldValue)))
                else:
                    rootGraph.add((field_uri, idf.hasValue, Literal(fieldValue)))

    for objHint in rootFile.idfobjects.keys():
        if len(rootFile.idfobjects[objHint]) == 0:
            continue
        for obj in rootFile.idfobjects[objHint]:
            if len(obj.obj) >= 2 and re.search("name", str(obj.objidd[1]["field"]), re.IGNORECASE) is not None:
                encodedObject(obj.obj[1], objHint, obj, idf.idfObject)
            elif objHint == "OUTPUT:VARIABLE":
                encodedObject(obj.obj[2], objHint, obj, encodeURI(objHint))
            else:
                encodedObject(objHint + "_instance", objHint, obj, idf.idfUniqueObject)

    return rootGraph


def OWLtoIDF(owl: Graph | str, out_file: str, template_idf_path: str | None = None,
             idd_path: str | None = None) -> IDF:
    """Convert an IDF RDF graph back into an EnergyPlus IDF file."""
    _safe_set_idd(default_idd_path(idd_path))
    if isinstance(owl, str):
        parsed = Graph()
        parsed.parse(owl)
        owl = parsed
    graph = edGraph.from_graph(owl)

    idfFile = IDF(default_template_idf_path(template_idf_path))
    for key in idfFile.idfobjects:
        idfFile.idfobjects[key] = []

    def decodeObject(objectURI):
        objHint = _first(graph.getObject(objectURI, idf.instanceOf))
        if objHint is None:
            return None
        obj = idfFile.newidfobject(decodeURI(objHint))
        for fieldURI in graph.getObject(objectURI, idf.hasField):
            fieldNameValue = _first(graph.getObject(fieldURI, idf.instanceOf))
            if fieldNameValue is None:
                continue
            fieldName = re.sub(" ", "_", decodeURI(fieldNameValue))
            if fieldName not in obj.objls:
                print(f"***Warning: {fieldName} not found in {decodeURI(objHint)}")
                fieldName = find_closest_field(obj.objls, fieldName)
            if fieldName == "":
                continue
            fieldValue = _first(graph.getObject(fieldURI, idf.hasValue))
            if fieldValue is None:
                continue
            if isinstance(fieldValue, URIRef):
                fieldValue = decodeURI(fieldValue)
            obj[fieldName] = str(fieldValue)
        return obj

    for object_type in (idf.idfUniqueObject, idf.idfObject, encodeURI("OUTPUT:VARIABLE")):
        for idfObject in graph.subjects(RDF.type, object_type):
            decodeObject(idfObject)

    idfFile.save(out_file)
    return idfFile
