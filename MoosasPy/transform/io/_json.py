from ...utils import json
from ...utils import mixItemListToList, to_dictionary, path, parseFile
import shapely
from ..geometry.element import MoosasGeometry


def build_geojson(model, mask=None) -> dict:
    """Build a GeoJSON feature collection from a model's active geometry."""
    if mask is not None:
        valid_geometry = model.findFace(mask)
    else:
        geometry_ids = set()
        for element in model.getAllFaces():
            geometry_ids.update(mixItemListToList(element.faceId))
        valid_geometry = model.findFace(list(geometry_ids))

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "normal": shapely.get_coordinates(geometry.normal, include_z=True).tolist(),
                    "id": geometry.faceId,
                    "is_glazing": geometry.category,
                },
                "geometries": {
                    "type": "Polygon",
                    "coordinates": shapely.get_coordinates(geometry.face, include_z=True).tolist(),
                },
            }
            for geometry in valid_geometry
        ],
    }

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
    from ._xml import build_xml

    dictionary = to_dictionary(build_xml(model))

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
    dictionary = build_geojson(model)

    # Serializing json
    json_object = json.dumps(dictionary, indent=4)

    # Writing to sample.json
    with open(file_path, "w") as outfile:
        outfile.write(json_object)

    return json_object


def _readGeojson(file_path) -> list[MoosasGeometry]:
    """
    Read a GeoJSON file and return a list of MoosasGeometry objects.
    
    Parameters
    ----------
    file_path : str
        Path to the GeoJSON file to be read.
    
    Returns
    -------
    list[MoosasGeometry]
        A list of MoosasGeometry objects parsed from the GeoJSON file.
    """
    raise NotImplementedError("geojson reader has not been implemented")
