import os
from difflib import SequenceMatcher

from eppy.modeleditor import IDF
from rdflib import Literal, URIRef
from rdflib.namespace import RDF

from ._rdf import MoosasGraph, encodeURI, decodeURI
from ..models import *
from ..thermal import *
from ..utils import path, mixItemListToList

def loadIDFTemplate(model: MoosasModel, idfTemplatePath=None) -> idfGeometry.ZoneTemplate:
    """
    Write an EnergyPlus Input Data File (IDF) based on a MoosasModel.

    Parameters
    ----------
    model : MoosasModel
        A model instance containing building geometry and settings to be converted into IDF format.
        Must provide methods `getAllFaces`, `spaceIdDict`, and `spaceList`, and associated attributes
        for space and surface properties.
    idfTemplatePath : str
        Path of the idf template file.

    Returns
    -------
    model : MoosasModel

    """
    # Properly handle paths for cross-platform compatibility
    if not idfTemplatePath:
        idfTemplatePath = os.path.join(path.dataBaseDir, "in.idf")
        idd = os.path.join(path.dataBaseDir, "Energy+.idd")
        IDF.setiddname(idd)

    idf = IDF(idfTemplatePath)
    zTemplate: idfGeometry.ZoneTemplate = idfGeometry.ZoneTemplate.fromIDF(idf)
    for si, space in enumerate(model.spaceList):
        print(f"\rIDF: overwriting zonal settings: {si}/{len(model.spaceList  + model.voidList)}", end='')
        space.settings['idf_template'] = zTemplate.appliedToZone(space)
        if space.is_open():
            print(f'\n******Warring: EnergyPlus do not support void space: {space.id}')
    return zTemplate


def writeIDF(model: MoosasModel, outputPath: str, idfTemplatePath=None):
    """
    Write an EnergyPlus Input Data File (IDF) based on a MoosasModel.

    Parameters
    ----------
    model : MoosasModel
        A model instance containing building geometry and settings to be converted into IDF format.
        Must provide methods `getAllFaces`, `spaceIdDict`, and `spaceList`, and associated attributes
        for space and surface properties.
    outputPath : str
        Path to save the generated IDF file. The directory must be writable.

    Returns
    -------
    None
        This function does not return any value. It writes the IDF file to the specified path and prints progress information.
    """
    print('IDF: initialization from IDF file...')
    moElements = model.getAllFaces(dumpUseless=True)
    zTemplate:idfGeometry.ZoneTemplate = loadIDFTemplate(model, idfTemplatePath)
    # remote existing zone-related objects
    removeHint = []
    removeHint += list(zTemplate.objectList.keys()) + ['Zone', 'WaterUse:Equipment', 'BuildingSurface:Detailed',
                                                       'FenestrationSurface:Detailed', 'Space','SpaceList','ZoneMixing','DesignSpecification:OutdoorAir:SpaceList']
    idf = zTemplate.idf
    for h in removeHint:
        idf.idfobjects[h] = []
        print(f"\rIDF: cleaning existing objects: {h}", end='')
    print()
    
    # add moosas defines objects
    # get type limits
    typeLimitsName = [idfobj['Name'] for idfobj in idf.idfobjects['ScheduleTypeLimits']]
    for typeLimit in schedule.typeLimitSettings:
        if typeLimit.params['Name'] not in typeLimitsName:
            typeLimit.applyToIDF(idf)
    airboundary = settings.MoosasSettings(construction.airBoundaryDefault)
    airboundary.applyToIDF(idf)

    # check space boundary condition
    removeSpace = [space.id for space in model.spaceList if space.is_open()]
    while len(removeSpace)>0:
        for inValidSpaceId in removeSpace:
            print(f"\rIDF: removing invalid space: {inValidSpaceId}", end='')
            model.removeSpace(inValidSpaceId)
        removeSpace = [space.id for space in model.spaceList if space.is_open()]
    print()

    # encoding geometries
    for wi, wall in enumerate(moElements['MoosasWall']):
        if len(wall.space) > 0:
            print(f"\rIDF: encoding walls: {wi+1}/{len(moElements['MoosasWall'])}", end='')
            space = model.spaceIdDict[wall.space[0]]
            wallU, winU, SHGC = space.settings['zone_wallU'], space.settings['zone_winU'], space.settings[
                'zone_win_SHGC']
            wallConstruction = zTemplate.getConstruction('opaque', wallU)
            windowConstruction = zTemplate.getConstruction('window', winU, SHGC)
            if wall.category == 2:
                idfGeometry.createThermalSurface(idf, wall, 'Wall', "Generic Air Boundary",
                                                 None,encodeWindow=False)
            else:
                idfGeometry.createThermalSurface(idf, wall, 'Wall', wallConstruction.params['Name'],
                                                 windowConstruction.params['Name'])
    print()
    for fi, face in enumerate(moElements['MoosasFace']):
        if len(face.space) > 0:
            print(f"\rIDF: encoding faces: {fi+1}/{len(moElements['MoosasFace'])}", end='')
            faceType = 'Floor'
            space = model.spaceIdDict[face.space[0]]
            if len(face.space) == 1:
                if face in model.spaceIdDict[face.space[0]].ceiling.face:
                    faceType = 'Roof'
            wallU, winU, SHGC = space.settings['zone_wallU'], space.settings['zone_winU'], space.settings[
                'zone_win_SHGC']
            wallConstruction = zTemplate.getConstruction('opaque', wallU)
            windowConstruction = zTemplate.getConstruction('window', winU, SHGC)
            if face.category == 2:
                idfGeometry.createThermalSurface(idf, face, faceType, "Moosas Air Boundary",
                                                 None,encodeWindow=False)
            else:
                idfGeometry.createThermalSurface(idf, face, faceType, wallConstruction.params['Name'],
                                                 windowConstruction.params['Name'])
    print()

    # writing zonal settings
    for si, space in enumerate(model.spaceList):
        print(f"\rIDF: encoding zones: {si+1}/{len(model.spaceList)}", end='')
        space.settings['idf_template'].applyToIDF(idf)
        # if space.is_void():
        #     print('***Warring: EnergyPlus do not support void space')
        # else:
        #     space.settings['idf_template'].applyToIDF(idf)

    # writing zone mixing
    mixing = set()
    for space in model.spaceList:
        for moElement in space.getAllFaces(False):
            if moElement.category == 2:
                mixing.add('~~'.join(moElement.space))

    for zoneTwins in mixing:
        zoneTwins = zoneTwins.split("~~")
        zoneMixing = settings.MoosasSettings(settings.ZoneMixingDefault)
        zoneMixing.updateParams(**{
            'Name':zoneTwins[0]+"_"+zoneTwins[1],
            'Zone_or_Space_Name': zoneTwins[0],
            'Source_Zone_or_Space_Name': zoneTwins[1],
        })
        zoneMixing.applyToIDF(idf)
        zoneMixing.updateParams(**{
            'Name':zoneTwins[1]+"_"+zoneTwins[0],
            'Zone or Space Name': zoneTwins[1],
            'Source Zone or Space Name': zoneTwins[0],
        })
        zoneMixing.applyToIDF(idf)

    idf.save(outputPath)
    print()


def find_closest_field(field_list: list, target_field: str) -> str:
    """
    从字符串列表中找到与目标字段最接近的匹配项（结合正则+相似度）
    :param field_list: 待匹配的字符串列表
    :param target_field: 目标字段名称
    :return: 最接近的匹配项（无匹配时返回空字符串）
    """
    # 步骤1：正则预处理（模糊匹配核心关键词，提升候选准确性）
    # 转义目标字段中的正则元字符，避免语法错误
    escaped_target = re.escape(target_field)
    # 构建模糊匹配正则：允许目标字段前后有其他字符，且忽略大小写
    pattern = re.compile(f".*{escaped_target}.*", re.IGNORECASE)

    # 步骤2：筛选候选项（至少包含目标字段核心字符的项）
    candidates = [field for field in field_list if pattern.match(str(field))]

    # 若无正则匹配的候选项，直接基于全列表计算相似度
    if not candidates:
        candidates = field_list

    # 步骤3：计算候选项与目标字段的相似度（编辑距离），排序
    def similarity(a: str, b: str) -> float:
        """计算两个字符串的相似度（0-1，1为完全一致）"""
        return SequenceMatcher(None, str(a).strip(), str(b).strip()).ratio()

    # 按相似度降序排序，相似度相同则按字符串长度接近度排序
    sorted_candidates = sorted(
        candidates,
        key=lambda x: (
            similarity(x, target_field),  # 优先按相似度
            -abs(len(str(x)) - len(target_field))  # 次优先按长度接近度
        ),
        reverse=True
    )

    # 步骤4：返回最接近的项（无列表元素时返回空）
    return sorted_candidates[0] if sorted_candidates else ""


def IDFtoOWL(idfTemplatePath):
    """
    Translate an IDF (Input Data File) knowledge base into an OWL (Web Ontology Language) RDF graph.

        Parameters
        ----------
        idfTemplatePath : str
            Path to the IDF template file to be converted. The file contains building energy model input data
            structured according to EnergyPlus Input/Output Reference definitions.

        Returns
        -------
        Graph
            An RDFlib Graph object representing the IDF data as an OWL ontology. The graph includes classes,
            properties, and instances derived from the IDF file, with semantics aligned to the EnergyPlus
            InputOutputReference documentation. Subjects are defined under the 'idf' namespace.
    """
    idd = os.path.join(path.dataBaseDir, "Energy+.idd")
    IDF.setiddname(idd)
    rootFile = IDF(idfTemplatePath)
    rootGraph = MoosasGraph()

    def encodedObject(objectName, className, obj, objectType):
        if "memo" in obj.objidd[0]:
            memo = ' '.join(obj.objidd[0]['memo'])
        else:
            memo = "This class has no comment"
        ent = rootGraph.encode_entity(name=">".join([className, objectName]),
                                      label=" ".join([className, objectName]),
                                      entityType=objectType,
                                      description=memo)
        rootGraph.add((ent, rootGraph.idf.instanceOf, encodeURI(className)))

        # embedding field and field value
        for idx, fieldIdd in enumerate(obj.objidd[1:len(obj.obj)]):
            # fieldName = fieldIdd['field'][0]
            fieldName = obj.objls[idx + 1]
            description = f'{fieldName} instance for the object {objectName} in class {className}'
            fieldEnt = rootGraph.encode_entity(name=">".join([className, objectName, fieldName]),
                                               label=" ".join([className, objectName, fieldName]),
                                               entityType=rootGraph.idf.fieldInstance,
                                               description=description)
            rootGraph.add((ent, rootGraph.idf.hasField, fieldEnt))
            rootGraph.add((fieldEnt, rootGraph.idf.instanceOf, encodeURI(fieldName)))
            fieldValue = obj.obj[idx + 1]
            if fieldValue != '':
                if "type" in fieldIdd:
                    if fieldIdd['type'][0] == 'object-list':
                        rootGraph.add((fieldEnt, rootGraph.idf.hasValue, encodeURI(fieldValue)))
                    else:
                        rootGraph.add((fieldEnt, rootGraph.idf.hasValue, Literal(fieldValue)))
                else:
                    rootGraph.add((fieldEnt, rootGraph.idf.hasValue, Literal(fieldValue)))

    for objHint in rootFile.idfobjects.keys():
        # serialized Processing idf class
        if len(rootFile.idfobjects[objHint]) > 0:

            # serialized Processing idf object
            for obj in rootFile.idfobjects[objHint]:

                # encoding normal objects
                if len(obj.obj) >= 2 and re.search('name', str(obj.objidd[1]['field']), re.IGNORECASE) is not None:
                    encodedObject(obj.obj[1], objHint, obj, rootGraph.idf.idfObject)

                # encoding output variables
                elif objHint == 'OUTPUT:VARIABLE':
                    encodedObject(obj.obj[2], objHint, obj, encodeURI(objHint))

                # encoding unique object
                else:
                    encodedObject(objHint + '_instance', objHint, obj, rootGraph.idf.idfUniqueObject)

    return rootGraph


def OWLtoIDF(owl, outFile):
    """
    Convert an OWL ontology graph to an IDF (Input Data File) format used by EnergyPlus.

    Parameters
    ----------
    owl : Graph or str
        An RDFlib Graph object containing the OWL ontology data, or a string path to an OWL file.
    outFile : str
        Path to the output file where the generated IDF will be saved.

    Returns
    -------
    IDF
        An IDF object representing the EnergyPlus input data file, populated with objects
        derived from the input OWL graph and saved to the specified output path.
    """
    # copy the graph into a MoosasGraph
    if isinstance(owl, str):
        newowl = MoosasGraph()
        newowl.parse(owl)
        owl = newowl
    graph = MoosasGraph()

    # ensure the owl is an edGraph() by copying all triples to a new graph
    for triple in owl:
        graph.add(triple)

    idfFile = IDF(os.path.join(path.dataBaseDir, "in.idf"))
    for key in idfFile.idfobjects:
        idfFile.idfobjects[key] = []

    def decodeObject(objectURI):
        objHint = graph.getObject(objectURI, graph.idf.instanceOf)[0]
        obj = idfFile.newidfobject(decodeURI(objHint))
        for fieldURI in graph.getObject(objectURI, graph.idf.hasField):
            fieldName = decodeURI(graph.getObject(fieldURI, graph.idf.instanceOf)[0])
            fieldName = re.sub(' ', '_', fieldName)

            # try to match field
            if fieldName not in obj.objls:
                print(f"***Warning: {fieldName} not found in {decodeURI(objHint)}")
                fieldName = find_closest_field(obj.objls, fieldName)

            if fieldName != '':
                fieldValue = graph.getObject(fieldURI, graph.idf.hasValue)
                if fieldValue:
                    if isinstance(fieldValue, URIRef):
                        fieldValue = decodeURI(fieldValue)
                    obj[fieldName] = str(fieldValue)

        return obj

    # add unique objects
    for idfObject in graph.subjects(RDF.type, graph.idf.idfUniqueObject):
        decodeObject(idfObject)

    # add normal objects
    for idfObject in graph.subjects(RDF.type, graph.idf.idfObject):
        decodeObject(idfObject)

    # add output objects
    for outputObject in graph.subjects(RDF.type, encodeURI("OUTPUT:VARIABLE")):
        decodeObject(outputObject)

    idfFile.save(outFile)
    return idfFile


def getIdfObjects(graph: MoosasGraph, objectURI: URIRef) -> MoosasGraph:
    """
    Given an input graph and an object URI, find all objects derived from the input idfObjectURI.
    Parameters
    ----------
    graph : MoosasGraph
        An MoosasGraph containing the OWL ontology data from IDFtoOWL().
    objectURI: URIRef
        An RDFlib URI which targets to a idfObject of the input graph.

    Returns
    -------
    subGraph : MoosasGraph
        An subGraph containing the zone settings.
    """
    for typeURI in graph.objects(objectURI, graph.rdf.type):
        if typeURI != graph.idf.idfObject:
            return MoosasGraph()
    subGraph = MoosasGraph()
    for s, p, o in graph.triples((objectURI, None, None)):
        subGraph.add((s, p, o))
    for field in graph.objects(objectURI, graph.idf.hasField):
        for s, p, o in graph.triples((field, None, None)):
            subGraph.add((s, p, o))
    return subGraph


def extractZoneTemplate(graph: MoosasGraph):
    """
    Extract the first zone and all relate settings from a MoosasGraph object;
    except for the geometry information.
    Parameters
    ----------
    graph : MoosasGraph
        An MoosasGraph containing the OWL ontology data from IDFtoOWL().


    Returns
    -------
    subGraph : MoosasGraph
        An subGraph containing the zone settings.
    """
    subGraph = MoosasGraph()
    zoneURI = mixItemListToList(graph.getSubject(graph.idf.instanceOf, encodeURI("ZONE")))[0]
    zoneName = decodeURI(zoneURI).split(">")[1]
    print(zoneName)
    relateObjects = set()

    def _checkAddObj(objURI):
        idfClass = decodeURI(graph.getObject(objURI, graph.idf.instanceOf))
        if idfClass is not None:
            if idfClass == "BUILDINGSURFACE:DETAILED" or idfClass == "FENESTRATIONSURFACE:DETAILED":
                return False
            else:
                relateObjects.add(objURI)
                return True

    # find object's name contain the zone name
    for obj in graph.subjects(RDF.type, graph.idf.idfObject):
        label = str(graph.getObject(obj, graph.rdfs.label))
        if re.search(zoneName, label) is not None:
            _checkAddObj(obj)

    # find field values contain the zone name, as object-list; then add the object has this field
    for fieldURI in graph.subjects(RDF.type, graph.idf.fieldInstance):
        for fieldValue in graph.objects(fieldURI, graph.idf.hasValue):
            if isinstance(fieldValue, URIRef):
                fieldValue = decodeURI(fieldValue)
                if re.search(zoneName, fieldValue) is not None:
                    theObject = graph.getSubject(graph.idf.hasField, fieldURI)
                    if theObject is not None:
                        _checkAddObj(theObject)

    for validObj in relateObjects:
        print(decodeURI(validObj))
        objGraph = getIdfObjects(graph, validObj)
        subGraph += objGraph

    return subGraph
