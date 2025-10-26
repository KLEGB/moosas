from ..thermal import idfGeometry, construction
from ._rdf import MoosasGraph
from ..utils import path

from eppy.modeleditor import IDF
import re, os
from rdflib.namespace import RDF, RDFS
from rdflib import Graph, Namespace, Literal, URIRef
import re
global _ENERGYPLUS_DIR
_ENERGYPLUS_DIR = r"C:/EnergyPlusV23-1-0"
idd = os.path.join(_ENERGYPLUS_DIR, "Energy+.idd")
IDF.setiddname(idd)
def writeIDF(outputPath: str, model):
    from ..models import MoosasModel
    model: MoosasModel = model
    print('IDF: initialization from IDF file...')

    if not _ENERGYPLUS_DIR:
        print("***Warning: ENERGYPLUS_DIR is not set. Please set it to your EnergyPlus installation folder.")
        return

    # Properly handle paths for cross-platform compatibility
    idfTemplatePath = os.path.join(_ENERGYPLUS_DIR, "ExampleFiles", "Moosas.idf")

    # IDF.setiddname(r'C:\EnergyPlusV8-9-0\Energy+.idd')

    idf = IDF(idfTemplatePath)
    moElements = model.getAllFaces(dumpUseless=True)
    zTemplate = idfGeometry.ZoneTemplate(idf)
    hint = []
    zName = [obj['Name'] for obj in idf.idfobjects['Zone']]+[obj['Name'] for obj in idf.idfobjects['Space']]
    for key in idf.idfobjects:
        print(f"\rIDF: cleaning existing objects: {key}", end='')
        if len(idf.idfobjects[key]) > 0:
            for objName in idf.idfobjects[key][0].obj:
                if objName in zName:
                    hint.append(key)
                    break
    hint +=zTemplate.objectHint+['Zone','WaterUse:Equipment','BuildingSurface:Detailed','FenestrationSurface:Detailed','Space']
    for h in hint:
        idf.idfobjects[h] = []
        print(f"\rIDF: cleaning existing objects: {h}", end='')
    print()
    for wi, wall in enumerate(moElements['MoosasWall']):
        print(f"\rIDF: encoding walls: {wi}/{len(moElements['MoosasWall'])}", end='')
        space = model.spaceIdDict[wall.space[0]]
        if not space.is_void():
            wallU, winU, SHGC = space.settings['zone_wallU'], space.settings['zone_winU'], space.settings['zone_win_SHGC']
            wallConstruction = zTemplate.getConstruction('opaque', wallU)
            windowConstruction = zTemplate.getConstruction('window', winU,SHGC)
            idfGeometry.createThermalSurface(idf,wall,'Wall',wallConstruction.params['Name'],windowConstruction.params['Name'])
    print()
    for fi, face in enumerate(moElements['MoosasFace']):
        print(f"\rIDF: encoding faces: {fi}/{len(moElements['MoosasFace'])}", end='')
        faceType = 'Floor'
        space = model.spaceIdDict[face.space[0]]
        if not space.is_void():
            if len(face.space)==1:
                if face in model.spaceIdDict[face.space[0]].ceiling.face:
                    faceType = 'Roof'
            wallU, winU, SHGC = space.settings['zone_wallU'], space.settings['zone_winU'], space.settings['zone_win_SHGC']
            wallConstruction = zTemplate.getConstruction('opaque', wallU)
            windowConstruction = zTemplate.getConstruction('window', winU,SHGC)
            idfGeometry.createThermalSurface(idf,face,faceType,wallConstruction.params['Name'],windowConstruction.params['Name'])
    print()
    for si, space in enumerate(model.spaceList):
        print(f"\rIDF: encoding zones: {si}/{len(model.spaceList)}", end='')
        if space.is_void():
            print('***Warring: EnergyPlus do not support void space')
        else:
            zTemplate.appliedToZone(space)
    idf.save(outputPath)
    print()

def encodeURI(hint):
    hint = re.sub(' ','_',str(hint).strip())
    if "!" in hint:
        raise Exception
    return URIRef(hint)

def IDFtoOWL(idfTemplatePath):
    """
    Translate and IDF knowledgebase into OWL graph.
    All subjects were defined under idf namespace with:
    https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v9.6.0/InputOutputReference.pdf
    """

    rootFile = IDF(idfTemplatePath)
    rootGraph = Graph()
    idf = Namespace('https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v9.6.0/InputOutputReference.pdf')
    rootGraph.bind('idf', idf)
    rootGraph.add((idf.idfClass,RDFS.comment,Literal("Normal idf classes which can be referred in the InputOutputReference")))
    rootGraph.add((idf.idfUniqueClass,RDFS.subClassOf,idf.idfClass))
    rootGraph.add((idf.idfUniqueClass, RDFS.comment, Literal("Unique classes with only one object")))
    for objHint in rootFile.idfobjects.keys():
        # serialized Processing idf class
        if len(rootFile.idfobjects[objHint])>0:

            # embedded class information
            memo = rootFile.idfobjects[objHint][0].objidd[0]['memo']
            rootGraph.add((encodeURI(objHint),RDFS.comment,Literal(' '.join(memo))))

            # serialized Processing idf object
            for obj in rootFile.idfobjects[objHint]:

                # encoding normal objects
                if len(obj.obj)>=2 and re.search('name',str(obj.objidd[1]['field']),re.IGNORECASE) is not None:
                    rootGraph.add((encodeURI(obj.obj[1]), RDF.type, idf.idfObject))
                    rootGraph.add((encodeURI(obj.obj[1]), idf.key, encodeURI(objHint)))
                    # mark as idfClass
                    rootGraph.add((encodeURI(objHint), RDF.type, idf.idfClass))

                    # embedding field and field value
                    for idx,fieldIdd in enumerate(obj.objidd[1:len(obj.obj)]):
                        if 'note' in fieldIdd:
                            rootGraph.add((encodeURI(fieldIdd['field'][0]), RDFS.comment, Literal(''.join(fieldIdd['note']))))
                        if 'type' in fieldIdd:
                            rootGraph.add((encodeURI(fieldIdd['field'][0]), idf.fieldType, encodeURI(fieldIdd['type'][0])))
                            if fieldIdd['type'][0] == 'object-list':
                                if obj.obj[idx + 1] !='':
                                    rootGraph.add((encodeURI(obj.obj[1]), encodeURI(fieldIdd['field'][0]), encodeURI(obj.obj[idx + 1])))
                            else:
                                if obj.obj[idx + 1] != '':
                                    rootGraph.add((encodeURI(obj.obj[1]), encodeURI(fieldIdd['field'][0]), Literal(obj.obj[idx + 1])))
                        else:
                            if obj.obj[idx + 1] != '':
                                rootGraph.add((encodeURI(obj.obj[1]), encodeURI(fieldIdd['field'][0]), Literal(obj.obj[idx + 1])))

                # encoding output variables
                elif objHint == 'OUTPUT:VARIABLE':
                    rootGraph.add((encodeURI(obj.obj[2]),RDF.type,encodeURI(objHint)))
                    rootGraph.add((encodeURI(obj.obj[2]), encodeURI('Key Value'), Literal(encodeURI(obj.obj[1]))))
                    rootGraph.add((encodeURI(obj.obj[2]), encodeURI('Reporting Frequency'), Literal(encodeURI(obj.obj[3]))))

                # encoding unique object
                else:
                    rootGraph.add((encodeURI(objHint), RDF.type, idf.idfUniqueClass))
                    # embedding field and field value
                    for idx, fieldIdd in enumerate(obj.objidd[1:len(obj.obj)]):
                        if 'note' in fieldIdd:
                            rootGraph.add((encodeURI(fieldIdd['field'][0]), RDFS.comment, Literal(''.join(fieldIdd['note']))))
                        if 'type' in fieldIdd:
                            rootGraph.add((encodeURI(fieldIdd['field'][0]), idf.fieldType, encodeURI(fieldIdd['type'][0])))
                            if fieldIdd['type'][0] == 'object-list':
                                if obj.obj[idx + 1] != '':
                                    rootGraph.add((encodeURI(objHint), encodeURI(fieldIdd['field'][0]), encodeURI(obj.obj[idx + 1])))
                            else:
                                if obj.obj[idx + 1] != '':
                                    rootGraph.add((encodeURI(objHint), encodeURI(fieldIdd['field'][0]), Literal(obj.obj[idx + 1])))
                        else:
                            if obj.obj[idx + 1] != '':
                                rootGraph.add((encodeURI(objHint), encodeURI(fieldIdd['field'][0]), Literal(obj.obj[idx + 1])))

    return rootGraph


def OWLtoIDF(owl:Graph,outFile):
    # copy the graph into a MoosasGraph
    if isinstance(owl,str):
        newowl = Graph()
        newowl.parse(owl)
        owl = newowl
    graph = MoosasGraph()
    for triple in owl:
        graph.add(triple)

    idfFile = IDF(path.dataBaseDir+r'\default.idf')
    for key in idfFile.idfobjects:
        idfFile.idfobjects[key]=[]
    idf = Namespace('https://energyplus.net/assets/nrel_custom/pdfs/pdfs_v9.6.0/InputOutputReference.pdf')
    # add unique objects
    for idfObject in graph.subjects(RDF.type,idf.idfUniqueClass):
        objHint = re.sub('_',' ',str(idfObject))
        uniqueObj = idfFile.newidfobject(objHint)
        for idx, fieldIdd in enumerate(uniqueObj.objidd[1:]):
            fieldValue = graph.getObject(idfObject,encodeURI(fieldIdd['field'][0]))
            if fieldValue is not None:
                uniqueObj[uniqueObj.objls[idx+1]]=str(fieldValue)

    # add normal objects
    for idfObject in graph.subjects(RDF.type,idf.idfObject):
        for validKey in graph.objects(idfObject,idf.key):
            objHint = re.sub('_', ' ', str(validKey))
            obj = idfFile.newidfobject(objHint)
            for idx, fieldIdd in enumerate(obj.objidd[1:]):
                fieldValue = graph.getObject(idfObject, encodeURI(fieldIdd['field'][0]))
                if fieldValue is not None:
                    obj[obj.objls[idx+1]] = str(fieldValue)

    # add output objects
    for outputObject in graph.subjects(RDF.type,encodeURI("OUTPUT:VARIABLE")):
        output = idfFile.newidfobject("OUTPUT:VARIABLE")
        fieldValue = graph.getObject(outputObject, encodeURI('Key Value'))
        output["Variable_Name"] = re.sub('_'," ",str(outputObject))
        if fieldValue is not None:
            output['Key_Value']=str(fieldValue)
        fieldValue = graph.getObject(outputObject, encodeURI('Reporting Frequency'))
        if fieldValue is not None:
            output['Reporting_Frequency']=str(fieldValue)

    idfFile.save(outFile)
    return idfFile



