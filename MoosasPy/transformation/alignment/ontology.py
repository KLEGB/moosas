from __future__ import annotations

import os

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

from ...utils import path
from ..io._rdf import decodeURI, encodeURI

IDF_NAMESPACE = "https://energyplus.net#"
idf = Namespace(IDF_NAMESPACE)


def default_idd_path(idd_path: str | None = None) -> str:
    return idd_path or os.path.join(path.dataBaseDir, "Energy+.idd")


def default_template_idf_path(template_idf_path: str | None = None) -> str:
    return template_idf_path or os.path.join(path.dataBaseDir, "in.idf")


def normalize_to_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


class edGraph(Graph):
    """EnergyPlus IDF RDF graph used as MOOSAS' parallel IDF settings graph."""

    def __init__(self):
        super(edGraph, self).__init__()
        self.bind("idf", idf)
        self.idf = idf
        self.rdf = RDF
        self.rdfs = RDFS
        self.add((idf.idfClass, RDFS.comment,
                  Literal("Normal idf classes which can be referred in the InputOutputReference")))
        self.add((idf.idfUniqueClass, RDFS.subClassOf, idf.idfClass))
        self.add((idf.idfUniqueClass, RDFS.comment,
                  Literal("Unique classes with only one object and no NAME as a field")))

    @classmethod
    def from_graph(cls, graph: Graph) -> "edGraph":
        retval = cls()
        for prefix, uri in graph.namespaces():
            retval.bind(prefix, uri)
        for triple in graph:
            retval.add(triple)
        return retval

    @classmethod
    def merge(cls, *graphs: Graph) -> "edGraph":
        retval = cls()
        for graph in graphs:
            for prefix, uri in graph.namespaces():
                retval.bind(prefix, uri)
            for triple in graph:
                retval.add(triple)
        return retval

    def getObject(self, _from, _property) -> list:
        return list(set(self.objects(_from, _property)))

    def getSubject(self, _property, _to) -> list:
        return list(set(self.subjects(_property, _to)))

    def encode_entity(self, name: str, entityType: URIRef, description: str, label: str | None = None):
        label = name if label is None else label
        entity = encodeURI(name)
        self.add((entity, RDFS.label, Literal(label)))
        self.add((entity, RDF.type, entityType))
        self.add((entity, RDFS.comment, Literal(description)))
        return entity

    def get_entity(self, entityURI, check=False):
        entity = entityURI if isinstance(entityURI, URIRef) else encodeURI(entityURI)
        entJson = {"uri": decodeURI(entity)}
        label = self.getObject(entity, RDFS.label)
        if len(label) > 0:
            entJson["label"] = str(label[0])
        elif check:
            print("Skipping entity " + str(entity) + " empty label")

        description = self.getObject(entity, RDFS.comment)
        if len(description) > 0:
            entJson["comment"] = str(description[0])
        elif check:
            print("Skipping entity " + str(entity) + " empty comment")

        objType = self.getObject(entity, RDF.type)
        if len(objType) > 0:
            entJson["type"] = decodeURI(objType[0])[len(IDF_NAMESPACE):]
        elif check:
            print("Skipping entity " + str(entity) + " empty type")
        return entJson
