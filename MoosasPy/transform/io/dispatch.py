"""This is the input and output method for the transformation module
MoosasModel should be imported inside the function to avoid circular import.
please use the general import func modelFromFile() instead of any private funcs.
"""
from __future__ import annotations
import os
import uuid

from ._geo import _readGeo, writeGeo, preClassified
from ._graph import writeGraph
from ._gbxml import convert_rdf_to_gbxml, convert_gbxml_to_rdf
from ._idf import writeIDF, readIDF
from ._json import _readGeojson, writeJson, writeGeojson
from ._obj import _readObj, writeObj
from ._ifc import loadIfc, rdf_to_ifc
from ._stl import _readStl
from ._rdf import writeRDF, loadRDF
from ._xml import writeXml, loadXml
from ...utils import path


def _temp_rdf_path(prefix: str) -> str:
    return os.path.join(path.tempDir, f"{prefix}_{uuid.uuid4().hex}.rdf")


def _remove_temp_file(file_path: str):
    if not file_path or not os.path.exists(file_path):
        return
    try:
        os.remove(file_path)
    except PermissionError:
        pass


def _scalarize_offset(value):
    if value is None:
        return 0.0
    if isinstance(value, (list, tuple)):
        if not value:
            return 0.0
        return _scalarize_offset(value[0])
    try:
        if hasattr(value, "flatten"):
            flat = value.flatten()
            if len(flat) == 0:
                return 0.0
            return float(flat[0])
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return value


def _normalize_offsets_for_rdf(model):
    restored = []
    getter = getattr(model, "getAllFaces", None)
    if not callable(getter):
        return restored
    for element in getter(False):
        if element is None or not hasattr(element, "offset"):
            continue
        old_value = getattr(element, "offset", None)
        new_value = _scalarize_offset(old_value)
        if new_value != old_value:
            restored.append((element, old_value))
            element.offset = new_value
    return restored


def _restore_offsets(restored):
    for element, old_value in restored:
        try:
            element.offset = old_value
        except Exception:
            pass


def loadModel(file_path: str, save_type: str = None, **kwargs):
    """
    Loading MoosasModel from the supported interchange formats.

    Parameters
    ----------
    file_path : str
        Input model file path.
    save_type : str, optional
        Input format switch. Supported values:
        `gbxml`, `ifc`, `idf`, `xml`, `rdf`.
        If omitted, the format is inferred from `file_path`.
    **kwargs
        Format-specific extra parameters:
        - `gbxml`: `rdf_format` for the temporary RDF file.
        - `idf`: `temp_geo` (geoPath), `temp_xml` (xmlPath), `idd_file` (iddPath).
        - `xml`: `geo_path` for the companion geometry file.
        - `rdf`: `rdf_format` for :func:`loadRDF`.
        Backward-compatible aliases are accepted: `fileFormat`, `geoPath`,
        `xmlPath`, `iddPath`.

    Returns
    -------
    MoosasModel
        The model for further transformation or analysis.
    """
    fileFormat = kwargs.pop("fileFormat", None)
    geo_path = kwargs.pop("geo_path", None)
    if geo_path is None:
        geo_path = kwargs.pop("geoPath", None)
    temp_xml = kwargs.pop("temp_xml", None)
    if temp_xml is None:
        temp_xml = kwargs.pop("xmlPath", None)
    temp_geo = kwargs.pop("temp_geo", None)
    if temp_geo is None:
        temp_geo = kwargs.pop("geoPath", None)
    idd_file = kwargs.pop("idd_file", None)
    if idd_file is None:
        idd_file = kwargs.pop("iddPath", None)
    rdf_format = kwargs.pop("rdf_format", None)
    if rdf_format is None:
        rdf_format = kwargs.pop("rdfFormat", None)

    formatHint = (save_type or fileFormat or '').lower()
    if formatHint == '' or formatHint == 'turtle':
        suffix = file_path.lower().split('.')[-1] if '.' in file_path else ''
        if suffix == 'xml':
            formatHint = 'xml'
        elif suffix == 'gbxml':
            formatHint = 'gbxml'
        elif suffix == 'ifc':
            formatHint = 'ifc'
        elif suffix == 'idf':
            formatHint = 'idf'
        elif suffix in {'rdf', 'ttl', 'turtle'}:
            formatHint = 'rdf'
    elif formatHint == 'rdf':
        formatHint = 'turtle'

    if formatHint == 'xml':
        if geo_path is None:
            geo_path = os.path.splitext(file_path)[0] + '.geo'
        model = loadXml(file_path, geo_path)
    elif formatHint == 'gbxml':
        temp_rdf_path = _temp_rdf_path("gbxml_load")
        try:
            convert_gbxml_to_rdf(file_path, temp_rdf_path, rdf_format=rdf_format or "turtle")
            model = loadModel(temp_rdf_path, "rdf", rdf_format=rdf_format or "turtle")
        finally:
            _remove_temp_file(temp_rdf_path)
    elif formatHint == 'ifc':
        model = loadIfc(file_path)
    elif formatHint == 'idf':
        model = readIDF(file_path, geoPath=temp_geo, xmlPath=temp_xml, iddPath=idd_file)
    elif formatHint == 'rdf':
        model = loadRDF(file_path, fileFormat=rdf_format or "turtle")
    else:
        model = loadRDF(file_path, fileFormat=formatHint)

    return model


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
    from ...models import MoosasModel
    model = MoosasModel()
    if inputPath[len(inputPath) - 4:len(inputPath)] == '.geo' or inputType == 'geo':
        model.geometryList = _readGeo(inputPath)
    # elif inputPath[len(inputPath) - 4:len(inputPath)] == '.xml' or inputType == 'xml':
    #     model.geometryList = _readXml(inputPath)
    elif inputPath[len(inputPath) - 4:len(inputPath)] == '.obj' or inputType == 'obj':
        model.geometryList = _readObj(inputPath)
    elif inputPath[len(inputPath) - 4:len(inputPath)] == '.stl' or inputType == 'stl':
        model.geometryList = _readStl(inputPath)
        model = preClassified(model)
        # STL is usually triangulated; run co-planar merge to remove redundant edges.
        if len(model.geometryList) > 0:
            from .preprocess import coPlanner

            temp_geo_path = os.path.join(path.tempDir, f"stl_coplanner_{uuid.uuid4().hex}.geo")
            try:
                coPlanner(model, temp_geo_path)
                model.geometryList = _readGeo(temp_geo_path)
            finally:
                if os.path.exists(temp_geo_path):
                    os.remove(temp_geo_path)
    elif inputPath[len(inputPath) - 4:len(inputPath)] == 'json' or inputType == 'json':
        model.geometryList = _readGeojson(inputPath)
    else:
        raise ImportError('***Error: Wrong file type(.geo,.xml,.obj,.stl,.json) Please check:', inputPath)

    return preClassified(model)





def saveModel(model, out_path: str, save_type: str = None, **kwargs):
    """
        Save the model into one of the supported interchange formats.

        Parameters
        ----------
        model : MoosasModel
            the model includes space and face topology, and other weather or material issues.
        out_path : str
            Output file path.
        save_type : str, optional
            Output format. Supported values:
            `gbxml`, `idf`, `ifc`, `obj`, `xml`, `rdf`, `geo`, `graph`,
            `spc`, `geojson`, `json`.
            `rdf` uses Turtle serialization by default.
        **kwargs
            Format-specific extra parameters.

                        - `idf`: `idfTemplate`, `idd_file`, `zoneNameToSpaceDict`, `dumpUseless`.
                        - `graph`: `clean_isolated`, `clean_airwall`,
                            `outer_layer_edge_embedding`.
                        - `gbxml`, `ifc`, `rdf`, `xml`, `geo`, `obj`, `spc`, `geojson`,
                            `json`: no additional parameters are required.

            Backward-compatible aliases are accepted for IDF:
            `idfTemplate`, `iddFile`, `zoneNameToSpaceDict`, `dumpUseless`.

        Returns
        -------
        None
    """
    path.checkBuildDir(out_path)
    if save_type is None:
        save_type = out_path.lower().split('.')[-1]
    idf_template = kwargs.pop("idfTemplate", None)
    idd_file = kwargs.pop("idd_file", None)
    if idd_file is None:
        idd_file = kwargs.pop("iddFile", None)
    zone_name_to_space_dict = kwargs.pop("zoneNameToSpaceDict", None)
    dump_useless = kwargs.pop("dumpUseless", None)
    if dump_useless is None:
        dump_useless = kwargs.pop("dump_useless", True)
    else:
        dump_useless = bool(dump_useless)
    clean_isolated = bool(kwargs.pop("clean_isolated", True))
    clean_airwall = bool(kwargs.pop("clean_airwall", True))
    outer_layer_edge_embedding = bool(
        kwargs.pop("outer_layer_edge_embedding", True)
    )
    if kwargs:
        pass
    if save_type.lower() == 'idf':
        writeIDF(model, out_path, idf_template, idd_file, zoneNameToSpaceDict=zone_name_to_space_dict)
    elif save_type.lower() == 'rdf':
        writeRDF(model, out_path, fileFormat="turtle", dumpUseless=dump_useless)
    elif save_type.lower() == 'ifc':
        restored_offsets = _normalize_offsets_for_rdf(model)
        temp_rdf_path = _temp_rdf_path("ifc_save")
        try:
            saveModel(model, temp_rdf_path, save_type='rdf', dumpUseless=dump_useless)
            rdf_to_ifc(temp_rdf_path, out_path, rdf_format="turtle")
        finally:
            _restore_offsets(restored_offsets)
            _remove_temp_file(temp_rdf_path)
    elif save_type.lower() == 'gbxml':
        temp_rdf_path = _temp_rdf_path("gbxml_save")
        try:
            saveModel(model, temp_rdf_path, save_type='rdf', dumpUseless=dump_useless)
            convert_rdf_to_gbxml(temp_rdf_path, out_path, rdf_format="turtle")
        finally:
            _remove_temp_file(temp_rdf_path)
    elif save_type.lower() == 'geo':
        writeGeo(out_path, model)
    elif save_type.lower() == 'obj':
        writeObj(out_path, model)
    elif save_type.lower() == 'geojson':
        writeGeojson(out_path, model)
    elif save_type.lower() == 'spc':
        writeSpc(out_path, model)
    elif save_type.lower() == 'xml':
        writeXml(out_path, model)
        geo_path = os.path.splitext(out_path)[0] + '.geo'
        writeGeo(geo_path, model)
    elif save_type.lower() == 'graph':
        writeGraph(
            out_path,
            model,
            clean_isolated=clean_isolated,
            clean_airwall=clean_airwall,
            outer_layer_edge_embedding=outer_layer_edge_embedding,
        )
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
