from __future__ import annotations
from rdflib import Graph, Namespace, Literal, URIRef
from ..models import *
from ..utils import np, pygeos, mixItemListToList, mixItemListToObject, searchBy, generate_code, path
from ..utils.constant import geom
from rdflib.namespace import RDF, RDFS, GEO, BRICK, WGS


class MoosasGraph(Graph):
    def __init__(self, model: MoosasModel = None, dumpUseless=True,ExportIFC=False):
        super(MoosasGraph, self).__init__()
        # create namespace
        self.bot = Namespace("https://w3id.org/bot#")
        self.moosas = Namespace("https://moosas#")
        self.pgd = Namespace("http://www.hkust.edu.hk/zhaojiwu/performance_based_generative_design#")
        self.ifc = Namespace("http://www.buildingsmart-tech.org/mvd/IFC4Add1/DTV/1.0/html/")
        self.rdf = RDF
        self.rdfs = RDFS
        self.geo = GEO
        self.brick = BRICK
        self.wgs = WGS
        self.bind("moosas", self.moosas)
        self.bind("bot", self.bot)
        self.bind("bes", self.pgd)
        self.bind("rdf", RDF)
        self.bind("rdfs", RDFS)
        self.bind("geo", GEO)
        self.bind("brick", BRICK)
        self.bind("wgs", WGS)
        self.bind("ifc", self.ifc)
        bld = URIRef("Building" + generate_code(4))
        self.add((URIRef("Site"), self.rdf.type, self.bot.Site))
        self.add((URIRef("Site"), self.bot.hasBuilding, bld))
        self.add((bld, self.rdf.type, self.bot.Building))
        if model:
            self.encodeModel(model, dumpUseless,ExportIFC)

    @classmethod
    def load(cls, filePath, fileFormat='turtle'):
        g = cls()
        g.parse(filePath, format=fileFormat)
        return g

    def encodeModel(self, model: MoosasModel, dumpUseless=True,ExportIFC=False):
        self.buildOntology(model)
        self.encodeStorey(model)
        if model.weather:
            self.encodeWeather(model)
        for tmp in model.buildingTemplate.keys():
            self.encodeProgram(tmp, model.buildingTemplate[tmp])
        for geo in model.geometryList:
            self.encodeGeo(geo)
        for space in model.spaceList + model.voidList:
            self.encodeSpace(space,ExportIFC)
        if dumpUseless:
            mElements = model.getAllFaces(True)
        else:
            mElements = {"MoosasFace": set(model.faceList), "MoosasWall": set(model.wallList),
                         "MoosasSkylight": set(model.skylightList), "MoosasGlazing": set(model.glazingList)}
        uidSet = mElements['MoosasFace'] | mElements['MoosasWall'] | mElements['MoosasSkylight'] | mElements[
            'MoosasGlazing']
        uidSet = [ele.Uid for ele in uidSet]

        for face in mElements['MoosasFace']:
            self.encodeElement(face, "Face", uidSet,ExportIFC)
        for face in mElements['MoosasWall']:
            self.encodeElement(face, "Wall", uidSet,ExportIFC)
        for face in mElements['MoosasGlazing']:
            if face.category == 2:
                self.encodeElement(face, "AirWall", uidSet,ExportIFC)
            else:
                self.encodeElement(face, "Glazing", uidSet,ExportIFC)
        for face in mElements['MoosasSkylight']:
            if face.category == 2:
                self.encodeElement(face, "AirSkylight", uidSet,ExportIFC)
            else:
                self.encodeElement(face, "Skylight", uidSet,ExportIFC)

    def buildOntology(self, model: MoosasModel):
        """constructing hierarchy for class in moosas
        """
        # program
        item = list(model.buildingTemplate.keys())[0]
        for zInfo in model.buildingTemplate[item].keys():
            self.add((self.moosas.term(zInfo), self.rdfs.subPropertyOf, self.moosas.Program))
            self.add((self.moosas.term(zInfo), self.rdf.type, self.moosas.ZoneInfo))
            self.add((self.moosas.term(zInfo), self.moosas.Uid, Literal(zInfo)))

        # geometry
        self.add((self.geo.hasGeometry, self.rdfs.subPropertyOf, self.moosas.Geometry))
        self.add((self.moosas.Category, self.rdfs.subPropertyOf, self.moosas.Geometry))
        self.add((self.moosas.hasHole, self.rdfs.subPropertyOf, self.moosas.Geometry))
        self.add((self.moosas.hasHole, self.rdfs.range, self.geo.Geometry))

        # face Element
        self.add((self.moosas.Uid, self.rdfs.subPropertyOf, self.bot.Element))
        self.add((self.moosas.Offset, self.rdfs.subPropertyOf, self.bot.Element))
        self.add((self.moosas.hasNeighborElement, self.rdfs.subClassOf, self.bot.hasSubElement))
        # self.add((self.moosas.hasNeighborElement, self.rdfs.range, self.bot.Element))
        self.add((self.pgd.hasSurfaceType, self.rdfs.range, self.moosas.surfaceType))
        self.add((self.moosas.rawElement, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.rawElement, self.rdfs.comment, Literal(f"Unclassified element")))
        self.add((self.moosas.Wall, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Wall, self.rdfs.comment,
                  Literal(
                      f"Opaque vertical Element the dot value with (0,0,1) bigger than {geom.HORIZONTAL_ANGLE_THRESHOLD}")))
        self.add((self.moosas.Face, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Face, self.rdfs.comment, Literal(
            f"Opaque horizontal Element the dot value with (0,0,1) smaller than {geom.HORIZONTAL_ANGLE_THRESHOLD}")))
        self.add((self.moosas.AirWall, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.AirWall, self.rdfs.comment,
                  Literal(
                      f"air boundary Element the dot value with (0,0,1) bigger than {geom.HORIZONTAL_ANGLE_THRESHOLD}")))
        self.add((self.moosas.AirSkylight, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.AirSkylight, self.rdfs.comment,
                  Literal(
                      f"air boundary Element the dot value with (0,0,1) smaller than {geom.HORIZONTAL_ANGLE_THRESHOLD}")))
        self.add((self.moosas.Glazing, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Glazing, self.rdfs.comment, Literal(
            f"Transparent vertical Element the dot value with (0,0,1) bigger than {geom.HORIZONTAL_ANGLE_THRESHOLD}")))
        self.add((self.moosas.Skylight, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Skylight, self.rdfs.comment, Literal(
            f"Transparent horizontal Element the dot value with (0,0,1) smaller than {geom.HORIZONTAL_ANGLE_THRESHOLD}")))

        self.add((self.moosas.hasLevel, self.rdfs.subPropertyOf, self.bot.Element))
        self.add((self.moosas.hasLevel, self.rdfs.range, self.bot.Storey))
        self.add((self.moosas.hasFace, self.rdfs.subPropertyOf, self.bot.Element))
        self.add((self.moosas.hasFace, self.rdfs.range, self.moosas.Geometry))

        # space
        self.add((self.moosas.Uid, self.rdfs.subPropertyOf, self.bot.Space))
        self.add((self.moosas.TopoElement, self.rdfs.subClassOf, self.bot.Element))
        self.add((self.moosas.TopoElement, self.rdfs.comment,
                  Literal(
                      f"1LSB element of the space which used to show the topology")))
        self.add((self.moosas.Ceiling, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Ceiling, self.rdfs.comment,
                  Literal(
                      f"1LSB of the space, composed by multi horizontal faces cap the 99% of area of the top projection space")))
        self.add((self.moosas.Edge, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Edge, self.rdfs.comment,
                  Literal(
                      f"1LSB of the space, composed by ordered vertical walls in a close loop")))
        self.add((self.moosas.Floor, self.rdf.type, self.moosas.surfaceType))
        self.add((self.moosas.Floor, self.rdfs.comment,
                  Literal(
                      f"1LSB of the space, composed by multi horizontal faces cap the 99% of area of the bottom projection space")))
        self.add((self.moosas.subElementOrder, self.rdfs.subPropertyOf, self.bot.Element))
        self.add((self.moosas.subElementOrder, self.rdfs.comment,
                  Literal(f"the loop order of the sub elements if supported")))

        # level
        self.add((self.moosas.altitute, self.rdfs.subPropertyOf, self.bot.Storey))

    def ifcOntology(self):
        # adding ifc definition for future data coupling and transition
        self.add((self.ifc.IfcExternalSpatialElement, self.rdfs.comment,
                  Literal(f"representing external of the building according to IFC4.0")))
        self.add(
            (self.ifc.IfcSpace, self.rdfs.comment, Literal(f"representing spaces of the building according to IFC4.0")))
        self.add((self.moosas.refSpace, self.rdfs.subPropertyOf, self.ifc.IfcSpace))
        self.add((self.moosas.refSpace, self.rdfs.range, self.bot.Space))

        self.add(
            (self.ifc.IfcBuildingElement, self.rdfs.comment, Literal(f"elements of the building according to IFC4.0")))
        self.add((self.ifc.GlobalID, self.rdfs.subPropertyOf, self.ifc.IfcBuildingElement))
        self.add((self.moosas.refElement, self.rdfs.subPropertyOf, self.ifc.IfcBuildingElement))
        self.add((self.moosas.refElement, self.rdfs.range, self.bot.Element))

        self.add((self.ifc.IfcWall, self.rdfs.subClassOf, self.ifc.IfcBuildingElement))
        self.add((self.ifc.IfcCurtainWall, self.rdfs.subClassOf, self.ifc.IfcBuildingElement))
        self.add((self.ifc.IfcWindow, self.rdfs.subClassOf, self.ifc.IfcBuildingElement))
        self.add((self.ifc.IfcRoof, self.rdfs.subClassOf, self.ifc.IfcBuildingElement))
        self.add((self.ifc.IfcSlab, self.rdfs.subClassOf, self.ifc.IfcBuildingElement))
        self.add((self.ifc.IfcVirtualElement, self.rdfs.subClassOf, self.ifc.IfcBuildingElement))

        self.add(
            (self.ifc.IfcRelSpaceBoundary2ndLevel, self.rdfs.comment, Literal(f"2LSB element according to IFC4.0")))
        self.add((self.ifc.GlobalID, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        # 2a: heat transfer face; 2b: adiabatic face; shading: shading
        self.add((self.ifc.Description, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        # reference to the Space
        self.add((self.ifc.RelatingSpace, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        self.add((self.ifc.RelatingSpace, self.rdfs.range, self.ifc.IfcSpace))
        # reference to the buildingElement
        self.add((self.ifc.RelatedBuildingElement, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        self.add((self.ifc.RelatedBuildingElement, self.rdfs.range, self.ifc.IfcBuildingElement))
        # reference to the moosas.geometry
        self.add((self.ifc.connectionGeometry, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        self.add((self.ifc.connectionGeometry, self.rdfs.range, self.moosas.Geometry))
        # Whether an air boundary
        self.add((self.ifc.PhysicalOrVirtualBoundary, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        # in or out surface
        self.add((self.ifc.InternalOrExternalBoundary, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        # if this is a window it should have parent boundary
        self.add((self.ifc.ParentBoundary, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        self.add((self.ifc.ParentBoundary, self.rdfs.range, self.ifc.IfcRelSpaceBoundary2ndLevel))
        # the boundary object on the other side
        self.add((self.ifc.CorrespondingBoundary, self.rdfs.subPropertyOf, self.ifc.IfcRelSpaceBoundary2ndLevel))
        self.add((self.ifc.CorrespondingBoundary, self.rdfs.range, self.ifc.IfcRelSpaceBoundary2ndLevel))

    def encodeWeather(self, model: MoosasModel):
        wea = URIRef(model.weather.location.stationId)
        site = self.getSubject(self.rdf.type, self.bot.Site)
        self.add((wea, self.rdf.type, self.pgd.Weather))
        self.add((wea, self.pgd.fileStoreAt, Literal(model.weather.weatherFile)))
        self.add((wea, self.pgd.stationId, Literal(model.weather.location.stationId)))
        self.add((wea, self.pgd.hasCumSky,
                  Literal(os.path.join(path.dataBaseDir, f'cum_sky\\cumsky_{model.weather.location.stationId}.csv'))))
        self.add((wea, self.pgd.hasLocation, URIRef(str(site))))
        self.add((wea, self.pgd.pressure, Literal(model.weather.location.pressure)))
        self.add((URIRef(str(site)), self.wgs.lat, Literal(model.weather.location.latitude)))
        self.add((URIRef(str(site)), self.wgs.long, Literal(model.weather.location.longitude)))
        self.add((URIRef(str(site)), self.wgs.alt, Literal(model.weather.location.altitude)))
        self.add((URIRef(str(site)), self.pgd.city, Literal(model.weather.location.city)))
        self.add((URIRef(str(site)), self.pgd.state, Literal(model.weather.location.state)))

    def encodeProgram(self, pgName: str, pgDict: dict):
        self.add((self.moosas.term(pgName), self.rdf.type, self.moosas.Program))
        self.add((self.moosas.term(pgName), self.moosas.Uid, Literal(pgName)))
        for zInfo in pgDict.keys():
            self.add((self.moosas.term(pgName), self.moosas.term(zInfo), Literal(pgDict[zInfo])))

    def encodeGeo(self, geo: MoosasGeometry):
        self.add((URIRef(geo.faceId), self.rdf.type, self.moosas.Geometry))
        self.add((URIRef(geo.faceId), self.moosas.Category, Literal(geo.category)))
        self.add((URIRef(geo.faceId), self.moosas.faceId, Literal(geo.faceId)))
        self.add((URIRef(geo.faceId), self.geo.hasGeometry, URIRef(geo.faceId + "fv")))
        self.add((URIRef(geo.faceId + "fv"), self.geo.asWKT,
                  Literal(pygeos.polygons(geo.boundary).__str__(), datatype=self.geo.wktLiteral)))
        if len(geo.holes) > 0:
            for hi, hole in enumerate(geo.holes):
                self.add((URIRef(geo.faceId), self.moosas.hasHole, URIRef(geo.faceId + f"fh{hi}")))
                self.add((URIRef(geo.faceId + f"fh{hi}"), self.geo.asWKT,
                          Literal(pygeos.polygons(hole).__str__(), datatype=self.geo.wktLiteral)))

    def encodeElement(self, Element: MoosasElement, typeName: str = "rawElement", mask=None, ExportIFC=False):
        self.add((URIRef(f"element_{Element.Uid}"), self.rdf.type, self.bot.Element))
        self.add((URIRef(f"element_{Element.Uid}"), self.moosas.Uid, Literal(Element.Uid)))
        self.add((URIRef(f"element_{Element.Uid}"), self.moosas.Offset, Literal(Element.offset)))
        self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasSurfaceType, self.moosas.term(typeName)))
        self.add((URIRef(f"element_{Element.Uid}"), self.moosas.hasLevel, URIRef(f"Level_{Element.level}")))
        self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasArea_m2, Literal(Element.area)))
        self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasNormalVectorX_m, Literal(Element.normal[0])))
        self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasNormalVectorY_m, Literal(Element.normal[1])))
        self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasNormalVectorZ_m, Literal(Element.normal[2])))
        condition = "Outdoors" if Element.isOuter else "Indoors"
        self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasOutsideBoundaryCondition, Literal(condition)))
        for fid in mixItemListToList(Element.faceId):
            self.add((URIRef(f"element_{Element.Uid}"), self.moosas.hasFace, URIRef(fid)))
        for gid in mixItemListToList(Element.glazingId):
            self.add((URIRef(f"element_{Element.Uid}"), self.bot.hasSubElement, URIRef(f"element_{gid}")))
        for key in Element.neighbor:
            for neiElement in Element.neighbor[key]:
                if mask:
                    if neiElement in mask:
                        self.add((URIRef(f"element_{Element.Uid}"), self.moosas.hasNeighborElement,
                                  URIRef(f"element_{neiElement}")))

        if len(Element.space) > 1:
            if len(Element.glazingElement) > 0:
                self.add((URIRef(f"element_{Element.Uid}"), self.pgd.hasAirFlow, URIRef(f"Space_{Element.space[0]}")))
                self.add(
                    (URIRef(f"element_{Element.Uid}"), self.pgd.hasAirFlow, URIRef(f"Space_{Element.space[1]}")))

        # ifc related objects
        if ExportIFC:
            gbID = generate_code(22)
            self.add((URIRef(f"ifcElement_{Element.Uid}"), self.ifc.GlobalID, Literal(gbID)))
            self.add((URIRef(f"ifcElement_{Element.Uid}"), self.ifc.refElement, URIRef(f"element_{Element.Uid}")))
            if typeName == 'Wall':
                self.add((URIRef(f"ifcElement_{Element.Uid}"), self.rdf.type, self.ifc.IfcWall))
            if typeName == 'Face':
                self.add((URIRef(f"ifcElement_{Element.Uid}"), self.rdf.type, self.ifc.IfcSlab))
            if typeName == 'Glazing' or typeName == 'Skylight':
                self.add((URIRef(f"ifcElement_{Element.Uid}"), self.rdf.type, self.ifc.IfcWindow))
            if typeName == 'AirWall' or typeName == 'AirSkylight':
                self.add((URIRef(f"ifcElement_{Element.Uid}"), self.rdf.type, self.ifc.IfcVirtualElement))

    def encodeStorey(self, model: MoosasModel):
        for bld_level in model.levelList:
            bld = self.getSubject(self.rdf.type, self.bot.Building)
            self.add((URIRef(f"Level_{bld_level}"), self.rdf.type, self.bot.Storey))
            self.add((URIRef(str(bld)), self.bot.hasStorey, URIRef(f"Level_{bld_level}")))
            self.add((URIRef(f"Level_{bld_level}"), self.moosas.altitute, Literal(bld_level)))
            spaces = np.array(model.spaceList)[searchBy('level', bld_level, model.spaceList)]
            for space in spaces:
                self.add((URIRef(f"Level_{bld_level}"), self.bot.hasSpace, URIRef(f"Space_{space.id}")))

    def encode2LSB(self, spaceId: str, element: MoosasElement):
        gbID = generate_code(22)
        self.add((URIRef(f"{spaceId}_{element.Uid}"), self.rdf.type, self.ifc.IfcRelSpaceBoundary2ndLevel))
        self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.GlobalID, Literal(gbID)))
        self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.Description, Literal("2a")))
        self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.RelatedBuildingElement,
                  URIRef(f"ifcElement_{element.Uid}")))
        if element.category == 2:
            self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.PhysicalOrVirtualBoundary,
                      URIRef(str('VIRTUAL'))))
        else:
            self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.PhysicalOrVirtualBoundary,
                      URIRef(str('PHYSICAL'))))
        if spaceId == 'outer':
            self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.RelatingSpace, self.ifc.IfcExternalSpatialElement))
            if element.parent.levelList.index(element.level) == 0 and Vector.parallel(element.normal, [0, 0, 1]):
                self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.InternalOrExternalBoundary,
                          Literal("EXTERNAL_EARTH")))
            else:
                self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.InternalOrExternalBoundary, Literal("EXTERNAL")))
        else:
            self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.RelatingSpace, URIRef(f"ifcSpace_{spaceId}")))
            self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.InternalOrExternalBoundary, Literal("INTERNAL")))
            if element.isOuter:
                self.encode2LSB("outer", element)
                self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.CorrespondingBoundary,
                          URIRef(f"outer_{element.Uid}")))
                self.add((URIRef(f"outer_{element.Uid}"), self.ifc.CorrespondingBoundary,
                          URIRef(f"{spaceId}_{element.Uid}")))
            else:
                otherSpace = element.space[1] if element.space.index(spaceId) == 0 else element.space[0]
                self.add((URIRef(f"{spaceId}_{element.Uid}"), self.ifc.CorrespondingBoundary,
                          URIRef(f"{otherSpace}_{element.Uid}")))

        for glsEle in element.glazingElement:
            self.encode2LSB("outer", glsEle)
            self.add((URIRef(f"{spaceId}_{glsEle.Uid}"), self.ifc.ParentBoundary, URIRef(f"{spaceId}_{element.Uid}")))

    def encodeSpace(self, space: MoosasSpace, ExportIFC=False):
        self.add((URIRef(f"Space_{space.id}"), self.rdf.type, self.bot.Space))
        self.add((URIRef(f"Space_{space.id}"), self.moosas.Uid, Literal(space.id)))
        self.add((URIRef(f"Space_{space.id}"), self.moosas.Program, self.moosas.term(space.settings["zone_template"])))
        self.add((URIRef(f"Space_{space.id}"), self.pgd.hasFloorArea_m2, Literal(space.area)))
        self.add((URIRef(f"Space_{space.id}"), self.pgd.hasVolume_m3, Literal(space.area * space.height)))
        self.add((URIRef(f"Space_{space.id}"), self.pgd.hasNorthDirection_deg, Literal(0e+00)))
        ifcElement = []
        if space.ceiling:
            self.add((URIRef(f"ceil_{space.ceiling.Uid}"), self.rdf.type, self.moosas.TopoElement))
            self.add((URIRef(f"Space_{space.id}"), self.bot.adjacentElement, URIRef(f"ceil_{space.ceiling.Uid}")))
            self.add((URIRef(f"ceil_{space.ceiling.Uid}"), self.pgd.hasSurfaceType, self.moosas.Ceiling))
            for faces in mixItemListToList(space.ceiling.face):
                self.add((URIRef(f"ceil_{space.ceiling.Uid}"), self.bot.hasSubElement, URIRef(f"element_{faces.Uid}")))
                ifcElement.append(faces)

        if space.floor:
            self.add((URIRef(f"floor_{space.floor.Uid}"), self.rdf.type, self.moosas.TopoElement))
            self.add((URIRef(f"Space_{space.id}"), self.bot.adjacentElement, URIRef(f"floor_{space.floor.Uid}")))
            self.add((URIRef(f"floor_{space.floor.Uid}"), self.pgd.hasSurfaceType, self.moosas.Floor))
            for faces in mixItemListToList(space.floor.face):
                self.add((URIRef(f"floor_{space.floor.Uid}"), self.bot.hasSubElement, URIRef(f"element_{faces.Uid}")))
                ifcElement.append(faces)

        if space.edge:
            self.add((URIRef(f"edge_{space.edge.Uid}"), self.rdf.type, self.moosas.TopoElement))
            self.add((URIRef(f"Space_{space.id}"), self.bot.adjacentElement, URIRef(f"edge_{space.edge.Uid}")))
            self.add((URIRef(f"edge_{space.edge.Uid}"), self.pgd.hasSurfaceType, self.moosas.Edge))
            loop = []
            for wall in mixItemListToList(space.edge.wall):
                self.add((URIRef(f"edge_{space.edge.Uid}"), self.bot.hasSubElement, URIRef(f"element_{wall.Uid}")))
                loop.append(wall.Uid)
                ifcElement.append(wall)
            self.add((URIRef(f"edge_{space.edge.Uid}"), self.moosas.subElementOrder, Literal(','.join(loop))))
        for void in space.void:
            self.add((URIRef(f"Space_{space.id}"), self.bot.containsZone, URIRef(f"Space_{void.id}")))

        if ExportIFC:
            self.add((URIRef(f"ifcSpace_{space.id}"), self.rdf.type, self.ifc.IfcSpace))
            self.add((URIRef(f"ifcSpace_{space.id}"), self.ifc.GlobalID, Literal(generate_code(22))))
            self.add((URIRef(f"ifcSpace_{space.id}"), self.moosas.refSpace, (URIRef(f"Space_{space.id}"))))
            for element in ifcElement:
                self.encode2LSB(space.id, element)

    def decodeGeo(self, geoUri, model: MoosasModel = None) -> MoosasGeometry:
        if isinstance(geoUri, str):
            geoUri = URIRef(str(geoUri))
        faceId = self.getObject(geoUri, self.moosas.faceId)
        if model:
            geo = model.findFace(str(faceId))
            if len(geo) > 0:
                return geo[0]
        cat = int(float(self.getObject(geoUri, self.moosas.Category)))
        face = URIRef(str(self.getObject(geoUri, self.geo.hasGeometry)))
        face = pygeos.Geometry(self.getObject(face, self.geo.asWKT))
        holes = [self.getObject(URIRef(str(hole)), self.geo.asWKT) for hole in
                 self.getObject(geoUri, self.moosas.hasHole)]
        holes = [pygeos.Geometry(str(h)) for h in holes]
        return MoosasGeometry(face=face, faceId=faceId, category=cat, holes=holes, errors="raise")

    def decodeElement(self, elementUri, model: MoosasModel = None) -> MoosasElement | None:
        if isinstance(elementUri, str):
            elementUri = URIRef(str(elementUri))
        surfaceType = URIRef(str(self.getObject(elementUri, self.pgd.hasSurfaceType)))
        Uid = str(self.getObject(elementUri, self.moosas.Uid))
        if surfaceType == self.moosas.Face:
            element = searchBy('Uid', Uid, model.faceList, earlyEnd=True, asObject=True)
        elif surfaceType == self.moosas.Wall:
            element = searchBy('Uid', Uid, model.wallList, earlyEnd=True, asObject=True)
        elif surfaceType == self.moosas.Glazing or surfaceType == self.moosas.AirWall:
            element = searchBy('Uid', Uid, model.glazingList, earlyEnd=True, asObject=True)
        elif surfaceType == self.moosas.Skylight or surfaceType == self.moosas.AirSkylight:
            element = searchBy('Uid', Uid, model.skylightList, earlyEnd=True, asObject=True)
        else:
            return None
        if len(element) > 0:
            return element[0]

        offset = float(self.getObject(elementUri, self.moosas.Offset))
        level = self.getObject(elementUri, self.moosas.hasLevel)
        level = float(self.getObject(URIRef(str(level)), self.moosas.altitute))
        geoId = str(self.getObject(elementUri, self.moosas.hasFace))
        geoId = str(self.getObject(URIRef(geoId), self.moosas.faceId))
        if surfaceType == self.moosas.Face:
            element = MoosasFace(model, geoId, level=level, uid=Uid, offset=offset)
        elif surfaceType == self.moosas.Wall:
            element = MoosasWall(model, geoId, level=level, uid=Uid, offset=offset)
        elif surfaceType == self.moosas.Glazing or surfaceType == self.moosas.AirWall:
            element = MoosasGlazing(model, geoId, level=level, uid=Uid, offset=offset)
        elif surfaceType == self.moosas.Skylight or surfaceType == self.moosas.AirSkylight:
            element = MoosasSkylight(model, geoId, level=level, uid=Uid, offset=offset)
        else:
            element = None
        return element

    def isClass(self, _from: str, _class: URIRef) -> bool:
        return self.getObject(_from, self.rdf.type) == _class

    def getObject(self, _from, _property):
        objects = set()
        for o in self.objects(_from, _property):
            objects.add(o)
        return mixItemListToObject(list(objects))

    def getSubject(self, _property, _to):
        objects = set()
        for o in self.subjects(_property, _to):
            objects.add(o)
        return mixItemListToObject(list(objects))

    def getRelate(self, node) -> list:
        related = set()
        for s, p, o in self.triples((node, None, None)):
            related.add(o)
        for s, p, o in self.triples((None, None, node)):
            related.add(s)
        return list(related)


def writeRDF(model: MoosasModel, out_path: str, fileFormat="turtle", dumpUseless=True,ExportIFC=False):
    g = MoosasGraph(model, dumpUseless,ExportIFC)
    g.serialize(out_path, format=fileFormat)
    return g


def loadRDF(input_path: str, fileFormat="turtle") -> MoosasModel:
    rdfGraph = MoosasGraph.load(input_path, fileFormat=fileFormat)
    model = MoosasModel()

    print(f'\rLOADING: searching Objects', end='')
    geoList = rdfGraph.getSubject(rdfGraph.rdf.type, rdfGraph.moosas.Geometry)
    levelList = rdfGraph.getSubject(rdfGraph.rdf.type, rdfGraph.bot.Storey)
    moFaceList = rdfGraph.getSubject(rdfGraph.pgd.hasSurfaceType, rdfGraph.moosas.Face)
    moWallList = rdfGraph.getSubject(rdfGraph.pgd.hasSurfaceType, rdfGraph.moosas.Wall)
    glsList = rdfGraph.getSubject(rdfGraph.pgd.hasSurfaceType, rdfGraph.moosas.Glazing)
    glsList = np.append(glsList, rdfGraph.getSubject(rdfGraph.pgd.hasSurfaceType, rdfGraph.moosas.AirWall))
    skyList = rdfGraph.getSubject(rdfGraph.pgd.hasSurfaceType, rdfGraph.moosas.Skylight)
    skyList = np.append(skyList, rdfGraph.getSubject(rdfGraph.pgd.hasSurfaceType, rdfGraph.moosas.AirSkylight))
    pgList = rdfGraph.getSubject(rdfGraph.rdf.type, rdfGraph.moosas.Program)
    spList = rdfGraph.getSubject(rdfGraph.rdf.type, rdfGraph.bot.Space)
    weather = rdfGraph.getSubject(rdfGraph.rdf.type, rdfGraph.pgd.Weather)
    if isinstance(weather, str):
        weatherPath = rdfGraph.getObject(URIRef(str(weather)), rdfGraph.pgd.fileStoreAt)
        if isinstance(weatherPath, str) and str(weatherPath).endswith('epw'):
            model.loadWeatherData(str(weatherPath))
        else:
            stationId = rdfGraph.getObject(URIRef(str(weather)), rdfGraph.pgd.stationId)
            model.loadWeatherData(str(stationId))

    print()

    # construct geometryList
    model.geometryList = []
    for i, geoUri in enumerate(geoList):
        model.geometryList.append(rdfGraph.decodeGeo(geoUri))
        print(f'\rLOADING: Geometry {i + 1}/{len(geoList)}', end='')
    model.geoId = [geo.faceId for geo in model.geometryList]
    model.newIndex = len(model.geometryList)
    print()
    # construct LevelList
    for i, levelUri in enumerate(levelList):
        levelUri = URIRef(str(levelUri))
        model.levelList.append(float(rdfGraph.getObject(levelUri, rdfGraph.moosas.altitute)))
        print(f'\rLOADING: level {i + 1}/{len(levelList)}', end='')
    model.levelList.sort()
    print()
    # construct MoosasFaceList
    for i, faceUri in enumerate(moFaceList):
        element = rdfGraph.decodeElement(faceUri, model)
        if element:
            model.faceList.append(element)
        print(f'\rLOADING: Faces {i + 1}/{len(moFaceList)}', end='')
    print()
    # construct MoosasWallList
    for i, faceUri in enumerate(moWallList):
        element = rdfGraph.decodeElement(faceUri, model)
        if element:
            model.wallList.append(element)
        print(f'\rLOADING: Wall {i + 1}/{len(moWallList)}', end='')
    print()
    # construct MoosasGlazingList
    for i, faceUri in enumerate(glsList):
        element = rdfGraph.decodeElement(faceUri, model)
        if element:
            parentFace = str(rdfGraph.getSubject(rdfGraph.bot.hasSubElement, URIRef(faceUri)))
            parentFace = rdfGraph.decodeElement(parentFace, model)
            if parentFace:
                parentFace.add_glazing(element)
            model.glazingList.append(element)
        print(f'\rLOADING: glazing {i + 1}/{len(glsList)}', end='')
    print()
    # construct MoosasSkylightList
    for i, faceUri in enumerate(skyList):
        element = rdfGraph.decodeElement(faceUri, model)
        if element:
            parentFace = str(rdfGraph.getSubject(rdfGraph.bot.hasSubElement, URIRef(faceUri)))
            parentFace = rdfGraph.decodeElement(parentFace, model)
            if parentFace:
                parentFace.add_glazing(element)
            model.skylightList.append(element)
        print(f'\rLOADING: skylight {i + 1}/{len(skyList)}', end='')
    print()
    # load Building Template
    for i, pgUri in enumerate(pgList):
        pgName = str(rdfGraph.getObject(URIRef(pgUri), rdfGraph.moosas.Uid))
        pgDict = {}
        for zInfo in rdfGraph.getSubject(rdfGraph.rdf.type, rdfGraph.moosas.ZoneInfo):
            zInfoName = rdfGraph.getObject(URIRef(zInfo), rdfGraph.moosas.Uid)
            pgDict[zInfoName] = str(rdfGraph.getObject(URIRef(pgUri), URIRef(zInfo)))
        model.includeTemplate(pgName, pgDict)
        print(f'\rLOADING: program {i + 1}/{len(pgList)}', end='')
    print()
    # load Space
    for i, spaceUri in enumerate(spList):
        spaceUri = URIRef(str(spaceUri))
        topoElements = mixItemListToList(rdfGraph.getObject(spaceUri, rdfGraph.bot.adjacentElement))
        topology = {"Floor": None, "Ceiling": None, "Edge": None}
        for topoElement in topoElements:
            topoElement = URIRef(str(topoElement))
            subElement = mixItemListToList(rdfGraph.getObject(topoElement, rdfGraph.bot.hasSubElement))
            subElement = [rdfGraph.decodeElement(URIRef(subE), model) for subE in subElement]
            subElement = {subE.Uid: subE for subE in subElement}
            topoElementType = rdfGraph.getObject(topoElement, rdfGraph.pgd.hasSurfaceType)

            if URIRef(str(topoElementType)) == rdfGraph.moosas.Edge:
                loop = str(rdfGraph.getObject(topoElement, rdfGraph.moosas.subElementOrder)).split(',')
                subElement = [subElement[w] for w in loop]
                topology["Edge"] = MoosasEdge(subElement)
            if URIRef(str(topoElementType)) == rdfGraph.moosas.Floor:
                topology["Floor"] = MoosasFloor(list(subElement.values()))
            if URIRef(str(topoElementType)) == rdfGraph.moosas.Ceiling:
                topology["Ceiling"] = MoosasFloor(list(subElement.values()))

        spc = MoosasSpace(_floor=topology["Floor"], _ceiling=topology["Ceiling"], _edge=topology["Edge"])
        if spc.is_void():
            model.voidList.append(spc)
        else:
            model.spaceList.append(spc)
        print(f'\rLOADING: space {i + 1}/{len(spList)}', end='')
    print()
    return model
