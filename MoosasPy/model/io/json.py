import os
import tempfile

from ...utils import ET, json
from ...utils import to_dictionary, path

def writeJson(file_path, model) -> str:
    """Get a json file describe the space topology.
    we have 3 different level of data:

    faces:{
        Uid: unique id, which is random generated.
        faceId: the faceId of the faces in the geo data or file.
        level: building level where the element locates.
        offset: the element's offset from the building level.
        area: the total surface area.
        glazingId: glazing faceId in the geo data or file.
        height: level + offset
        normal: element's normal, point to exterior.
        external: whether the element is connected to exterior.
        space: the space id which this element belongs to.
        }

    topology:{
        floor:{faces:[{faces}..]}
        edge:{faces:[{faces}..]}
        ceiling:{faces:[{faces}..]}
    }

    space:{
        id: unique space id, which is calculated based on the shape & location of the space. It is the same in each we call transfrom()
        area: space area
        height: space height
        boundary: space 1 level space boundary (1LSB){pt:[[x,y,z]...]}
        internalMass: the internalMass in the space {faces:[{faces}..]}
        topology:{topology}
        neighbor: the neighborhood space share the same 2 level space boundary (2LSB)
            [{
                faceId: the faceId of the 2LSB in the geo file,
                id: the neighbor space id
            }]
        settings: thermal settings of the space in dictionary, defined by transformation.io.idf.model
        void: the void inside the space, also formatted in space[{space}..]
    }

    Args:
        file_path(str): output space json file path
        model(MoosasModel): model to export

    Returns:
        json string of the file
    """
    path.checkBuildDir(file_path)
    from .xml import build_xml

    dictionary = to_dictionary(build_xml(model))

    # Serializing json
    json_object = json.dumps(dictionary, indent=4)

    # Writing to sample.json
    with open(file_path, "w") as outfile:
        outfile.write(json_object)

    return json_object


def _append_xml_value(parent, tag, value) -> None:
    if isinstance(value, list):
        for item in value:
            _append_xml_value(parent, tag, item)
        return
    element = ET.SubElement(parent, tag)
    if isinstance(value, dict):
        for child_tag, child_value in value.items():
            _append_xml_value(element, child_tag, child_value)
    else:
        element.text = "" if value is None else str(value)


def loadJson(file_path: str, geo_path: str):
    """Load the JSON form of the XML model serialization and its GEO companion."""
    from .xml import loadXml

    with open(file_path, encoding="utf-8") as source:
        document = json.load(source)
    if not isinstance(document, dict):
        raise ValueError("JSON model must be an object.")

    if len(document) == 1 and "model" in document:
        root_tag, root_value = "model", document["model"]
    else:
        root_tag, root_value = "model", document
    root = ET.Element(root_tag)
    if isinstance(root_value, dict):
        for tag, value in root_value.items():
            _append_xml_value(root, tag, value)
    else:
        root.text = "" if root_value is None else str(root_value)

    handle = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    try:
        handle.close()
        ET.ElementTree(root).write(handle.name)
        return loadXml(handle.name, geo_path)
    finally:
        if os.path.exists(handle.name):
            os.remove(handle.name)
