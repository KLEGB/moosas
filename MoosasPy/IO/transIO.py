"""This is the input and output method for the transformation module
MoosasModel should be imported inside the function to avoid circular import.
please use the general import func modelFromFile() instead of any private funcs.
"""
from ._geo import _readGeo, writeGeo , preClassified
from ._idf import writeIDF
from ._json import _readGeojson, writeJson, writeGeojson
from ._obj import _readObj
from ._rdf import writeRDF
from ._xml import writeXml
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

    return preClassified(model)





def saveModel(model, out_path: str, save_type: str = None, idfTemplate=None, iddFile=None, dumpUseless=True):
    """
        Save the model into any format.

        Parameters
        ----------
        model : MoosasModel
            the model includes space and face topology, and other weather or material issues.
        out_path : str
            output rdf file path
        save_type : str, optional
            rdf format, following the definition of rdf module, I/O possible file.
            xml format, following the definition of xml module, I/O possible file.
            geo format, following the definition of geo specific for Moosas, I/O possible file.
            idf format, following the definition of EnergyPlus input file, I/O possible file.

            spc format, following the definition of legacy spc module.
            geojson format, following the definition of geojson.
        idfTemplate: str, optional
            optional idf template for writing idf file
        iddFile: str, optional
            optional idd file path for writing idd file
        dumpUseless : bool, optional
            cut out the unuse nodes (elements and faces)

        Returns
        -------
        None
    """
    path.checkBuildDir(out_path)
    if save_type is None:
        save_type = out_path.lower().split('.')[-1]
    if save_type.lower() == 'idf':
        writeIDF(model, out_path, idfTemplate, iddFile)
    elif save_type.lower() == 'rdf':
        writeRDF(model, out_path, fileFormat="turtle", dumpUseless=dumpUseless)
    elif save_type.lower() == 'geo':
        writeGeo(out_path, model)
    elif save_type.lower() == 'geojson':
        writeGeojson(out_path, model)
    elif save_type.lower() == 'spc':
        writeSpc(out_path, model)
    elif save_type.lower() == 'xml':
        writeXml(out_path, model)
    elif save_type.lower() == 'json':
        writeJson(out_path, model)


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
