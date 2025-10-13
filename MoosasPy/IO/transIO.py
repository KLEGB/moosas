"""This is the input and output method for the transformation module
MoosasModel should be imported inside the function to avoid circular import.
please use the general import func modelFromFile() instead of any private funcs.
"""
from ._geo import _readGeo,writeGeo
from ._obj import _readObj
from ._xml import writeXml
from ._json import _readGeojson,writeJson,writeGeojson
from ._idf import writeIDF
from ..utils import path

def modelFromFile(inputPath: str, inputType=None):
    """Get a MoosasModel from geometry file *.geo,*.xml,*.obj,*.json(geoJson)

    please check the file requirement in each function:
    _readGeo,_readXml,_readObj,readGeoJson
    this can be used to generate a model to test whether your geometries are read corectly.

    Args:
        inputPath(str): input geometry file.
        inputType(str): input file type. If None the type will be interpreted from the file directly (default: None)

    Returns:
        model(MoosasModel): the MoosasModel contain the geometry data.

    Raises:
        ImportError: get an unsupport file

    Examples:
        >>> model = modelFromFile(r'test.geo')
    """
    from ..models import MoosasModel
    model = MoosasModel()
    if inputPath[len(inputPath) - 4:len(inputPath)] == '.geo' or inputType == 'geo':
        model.geometryList = _readGeo(inputPath)
    # elif inputPath[len(inputPath) - 4:len(inputPath)] == '.xml' or inputType == 'xml':
    #     model.geometryList = _readXml(inputPath)
    elif inputPath[len(inputPath) - 4:len(inputPath)] == '.obj' or inputType == 'obj':
        model.geometryList = _readObj(inputPath)
    elif inputPath[len(inputPath) - 4:len(inputPath)] == 'json' or inputType == 'json':
        model.geometryList = _readGeojson(inputPath)
    else:
        raise ImportError('***Error: Wrong file type(.geo,.xml,.obj,.json) Please check:', inputPath)
    model.geoId = [geo.faceId for geo in model.geometryList]
    model.newIndex = len(model.geometryList)
    return model


def modelToFile(model, outputPath, outputType=None, geoPath=None, geoType=None):
    """write the space topology data or geometry data to the file

    please check the file description in each function:
    _readGeo,_readXml,_readObj,readGeoJson

    Args:
        model(MoosasModel): model to write the space data and geometries data
        outputPath(str): input geometry file.
        geoPath(str): output geometry file.
        outputType(str): input file type. If None the type will be interpreted from the file directly (default: None)
        geoType(str): output geometry file.


    Returns:
        None

    Examples:
        >>> modelToFile(model,r'test.json')
    """
    if outputPath[-4:len(outputPath)] == '.spc' or outputType == 'spc':
        writeSpc(outputPath, model)
    elif outputPath[-4:len(outputPath)] == '.xml' or outputType == 'xml':
        writeXml(outputPath, model)
    elif outputPath[-4:len(outputPath)] == 'json' or outputType == 'json':
        writeJson(outputPath, model)
    elif outputPath[-4:len(outputPath)] == '.idf' or outputType == 'idf':
        writeIDF(outputPath, model)
    else:
        print('***Error: Wrong file type(.spc,.xml,.json) Please check:', outputPath)

    if geoPath is not None:
        if geoPath[-4:len(geoPath)] == '.geo' or geoType == '.geo':
            writeGeo(geoPath, model)
        if geoPath[-4:len(geoPath)] == 'json' or geoType == 'json':
            writeGeojson(geoPath, model)



def writeSpc(file_path, model) -> str:
    """write the string of each space.

    we get the string from space.to_string method instead of __str__() method
    since the string output is too long.

    Args:
        file_path(str): output space string file path
        model(MoosasModel): model to export
    Returns:
        None
    """
    path.checkBuildDir(file_path)
    with open(file_path, "w", encoding='utf-8') as f:
        for space in model.spaceList:
            out_string = space.to_string(model)
            f.write(out_string)

    return out_string
