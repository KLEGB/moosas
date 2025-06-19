from ..utils import json
from ..utils import to_dictionary, path, parseFile
from ..geometry.element import MoosasGeometry

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
        settings: thermal settings of the space in dictionary, you can find their names in .thermal.settings
        void: the void inside the space, also formatted in space[{space}..]
    }

    Args:
        file_path(str): output space json file path
        model(MoosasModel): model to export

    Returns:
        json string of the file
    """
    path.checkBuildDir(file_path)
    dictionary = to_dictionary(model.buildXml())

    # Serializing json
    json_object = json.dumps(dictionary, indent=4)

    # Writing to sample.json
    with open(file_path, "w") as outfile:
        outfile.write(json_object)

    return json_object


def writeGeojson(file_path, model) -> str:
    """Get a geojson file for the geometry library in the model

    features = [
        {
            "type": "Feature",
            "properties": {
                "normal": geometries' normal,
                "id": geometries' faceId,
                "is_glazing": geo.category
            },

            "geometries": {
                "type": "Polygon",
                "coordinates": coordinates for each polygon
            }
        }
    ]

    Args:
        file_path(str): output geojson file path
        model(MoosasModel): model to export

    Returns:
        json file string
    """
    path.checkBuildDir(file_path)
    dictionary = model.buildGeojson()

    # Serializing json
    json_object = json.dumps(dictionary, indent=4)

    # Writing to sample.json
    with open(file_path, "w") as outfile:
        outfile.write(json_object)

    return json_object


def _readGeojson(file_path) -> list[MoosasGeometry]:
    raise NotImplementedError("geojson reader has not been implemented")
