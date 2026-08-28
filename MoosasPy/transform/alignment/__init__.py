"""Multi-file semantic alignment and output boundary."""

from .editing import find_idf_field, get_idf_field_value, iter_idf_objects, set_idf_field_value
from .linking import (
    attach_idf_graph,
    extract_idf_graph,
    link_idf_graph_to_moosas,
    merge_moosas_and_idf_graphs,
)
from .ontology import (
    IDF_NAMESPACE,
    decodeURI,
    default_template_idf_path,
    edGraph,
    encodeURI,
    idf,
    normalize_to_list,
)
from .owl import IDFtoOWL, OWLtoIDF

__all__ = [
    "IDF_NAMESPACE",
    "IDFtoOWL",
    "OWLtoIDF",
    "attach_idf_graph",
    "decodeURI",
    "default_template_idf_path",
    "edGraph",
    "encodeURI",
    "extract_idf_graph",
    "find_idf_field",
    "get_idf_field_value",
    "idf",
    "iter_idf_objects",
    "link_idf_graph_to_moosas",
    "merge_moosas_and_idf_graphs",
    "normalize_to_list",
    "set_idf_field_value",
]
