"""Model file conversion boundary.

Format-specific adapters and their model-level dispatch belong here.
"""

from .dispatch import loadModel as load_model
from .dispatch import modelFromFile as model_from_file
from .dispatch import saveModel as save_model
from ._gbxml import convert_gbxml_to_rdf, convert_rdf_to_gbxml, gbxml_to_rdf, rdf_to_gbxml
from ._geo import geoLegacyToGeo, objToGeo, writeGeo
from ._graph import buildGraph, graph_from_dict, graph_to_dict, loadGraph, writeGraph
from ._idf import IDFtoGeo, IDFtoXml, readIDF, writeIDF
from ._ifc import loadIfc, writeIfc
from ._json import writeGeojson, writeJson
from ._rdf import loadRDF, writeRDF
from ._xml import loadXml, writeXml

__all__ = [
	"IDFtoGeo",
	"IDFtoXml",
	"convert_gbxml_to_rdf",
	"convert_rdf_to_gbxml",
	"gbxml_to_rdf",
	"geoLegacyToGeo",
	"graph_from_dict",
	"graph_to_dict",
	"loadGraph",
	"loadIfc",
	"loadRDF",
	"loadXml",
	"load_model",
	"model_from_file",
	"objToGeo",
	"rdf_to_gbxml",
	"readIDF",
	"save_model",
	"writeGeo",
	"writeGeojson",
	"writeGraph",
	"writeIDF",
	"writeIfc",
	"writeJson",
	"writeRDF",
	"writeXml",
]