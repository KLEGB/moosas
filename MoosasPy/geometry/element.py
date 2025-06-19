"""Element definition in moosas+

we split the MoosasModel definition from geometry.element to avoid circular import.
however, we still need some method in MoosasModel,
so actually all objects named model or attributes named parent are MoosasModel object as its abstract class MoosasContainer
"""
from __future__ import annotations

from .geos import Projection, Vector, faceNormal, simplify, overlapArea, equals, selfIntersect, makeValid, bBox
from ..utils import generate_code, searchBy, mixItemListToObject, mixItemListToList, encodeParams, GeometryError
from ..utils import pygeos, np, ET, Iterable
from ..utils.constant import geom
from ..encoding.convexify import triangulate2dFace
import re
# 不做inch meter转换
INCH_METER_MULTIPLIER = 1
INCH_METER_MULTIPLIER_SQR = 1


def _getElement(*key: str, dictionary: dict, strict=True) -> np.ndarray:
    l = []
    for k in key:
        if k not in dictionary.keys():
            if strict:
                raise NameError(f'{k} not in the construct dictionary {dictionary}')
            else:
                return np.array([None])
        l = np.append(l, dictionary[k])
    return l


class MoosasGeometry(object):
    """protection for original geometry.
    the class object can only be created and never be changed.
    the is valid method is used to test whether this object can be used in moosas+.
    """
    __slots__ = ['__face', '__normal', '__faceId', '__category', '__holes', 'delete', 'flip']

    def __init__(self, face: pygeos.Geometry | np.ndarray, faceId, normal: pygeos.Geometry | Vector | np.ndarray = None,
                 category=0,
                 holes: list[pygeos.Geometry | np.ndarray] = None, errors='ignore'):
        if normal is None:
            normal = faceNormal(face)
        if not holes:
            holes = []
        # test if input is valid
        if Vector(normal).length() == 0:
            raise GeometryError(face, "zero-length normal")
        self.__face: np.ndarray = self._treatFace(face)
        self.__holes: list[np.ndarray] = [self._treatFace(hole) for hole in holes]
        self.__normal: Vector = Vector(normal)
        self.flip = False

        self.__faceId: str = str(faceId)
        self.__category: int = category
        self.delete: bool = False

        # validation
        if self.invalid() is not None:
            if errors == 'ignore':
                print(f"******Warning: GeometryError, invalid polygon received:{self.invalid()}")
            else:
                raise GeometryError(face, f"invalid polygon received:{self.invalid()}")

    @staticmethod
    def _treatFace(face) -> np.ndarray:
        """preprocess the face or holes."""
        face = pygeos.get_coordinates(face, include_z=True) if isinstance(face, pygeos.Geometry) else face
        _coordinates = []
        for point in face:
            if len(point) == 2:
                point = np.append(point, 0)
            if len(_coordinates) == 0:
                _coordinates.append(point)
            elif np.sum(np.abs(_coordinates[-1] - point)) != 0:
                _coordinates.append(point)
        if len(_coordinates) == 3:
            if np.sum(np.abs(_coordinates[-1] - _coordinates[0])) == 0:
                raise GeometryError(face, "too few points")
        if len(_coordinates) < 3:
            raise GeometryError(face, "too few points")
        return np.array(_coordinates)

    def invalid(self) -> str | None:
        geos = [self.__face] + self.__holes
        for geo in geos:
            # if not pygeos.points(geo[-1]) == pygeos.points(geo[0]):
            #             #     return f"not a closed polygon"
            if selfIntersect(pygeos.polygons(geo)):
                return f"self-intersect geo"
        # for hole in self.holes:
        #     if not pygeos.contains(pygeos.polygons(self.boundary), pygeos.polygons(hole)):
        #         return "holes outside"
        return None

    @property
    def face(self) -> pygeos.Geometry:
        holes = self.holes if len(self.__holes) > 0 else None
        return pygeos.polygons(geometries=self.boundary, holes=holes)

    @property
    def boundary(self):
        return pygeos.linearrings(self.__face)

    @property
    def normal(self) -> pygeos.Geometry:
        if self.flip:
            return (-self.__normal).geometry
        else:
            return self.__normal.geometry

    @property
    def faceId(self) -> str:
        return self.__faceId

    @property
    def category(self) -> int:
        """
        0: opaque
        1: glazing
        2: airBoundary
        """
        return self.__category

    @property
    def holes(self) -> list[pygeos.Geometry]:
        return [pygeos.linearrings(hole) for hole in self.__holes]

    def getEdgeStr(self) -> list[str]:
        """get a unique edge string of the boundary, ignore the direction of the edge."""
        faces = [self.boundary] + self.holes
        edge_str_s = {}
        for face in faces:
            coors = pygeos.get_coordinates(face, include_z=True)

            for i in range(1, len(coors)):
                str1, str2 = '', ''
                for corDim in coors[i]:
                    str1 += f'{int(corDim * 100)}_'
                for corDim in coors[i - 1]:
                    str2 += f'{int(corDim * 100)}_'
                if str1 != str2:
                    if coors[i - 1][0] + coors[i - 1][1] + coors[i - 1][2] > coors[i][0] + coors[i][1] + coors[i][2]:
                        edge_str = f'{str1}{str2}'
                    else:
                        edge_str = f'{str2}{str1}'
                    if edge_str in edge_str_s:
                        edge_str_s[edge_str] = 1
                    else:
                        edge_str_s[edge_str] = 0

        return [edgeStr for edgeStr in edge_str_s if edge_str_s[edgeStr] == 0]


class MoosasElement(object):
    """
    Base class, which expresses all geometry, loads basic methods & basic members
    new feature:
    now the geometry will be created based on _Geometry class to ensure the consistency of id and geometry
    in this case, the model is required to input.
    in the init method we will check the consistency of id and geometry.
    besides, face, faceId and normal object will be properties and get from __geometries

    -------------------------------------------
    init params:
    faceId: geometry faceId in MoosasModel, should be in the list MoosasModel.geoId
    model: MoosasModel

    optional params:
    'level': the building floor level of the geometry
    'offset': the offset from the building level
    'glazingId': a list of glazing faceId
    'space': a list of space id this geometry belongs to

    attribute:
    'parent': The model to which the face belongs
    'isOuter': whether this face is an external faces
    'Uid': unique Id of the element
    'shading': a list of shading elements.
    level,offset,space: those in optional params.

    properties:
    'face': Faces (list) of the loaded geometry
    'normal': a unique face normal
    'faceId': The identification of the face(s), defined by the id of the read geo data
    'category': category of the Geometry, 0==opaque element, 1==transparent element, 2==aperture element
    'area': total face area of the element
    'elevation': level + offset
    'wwr': Window-to-Wall ratio of this element calculated based on UV method
    'firstFaceId': the first faceId of all geometries in this element, to avoid error in some method.
    'glazingId': a list of glazing faceId
    'glazingElement': return MoosasGlazing object instead of glazingId


    -------------------------------------------

    method:
    'area3d': calculate area in 3d projection, for itself or other faces.
    'glazingUV': get UV faces of all glazing elements
    'faceUV': get UV faces of itself
    'getEdgeStr': get unique descriptions in string of all edges in this element
    'getWeightCenter': Gets the weighted center point
    'add_glazing': add glazing Element to the glazingId.

    Conceptual method:
    'force_2d': A conceptual approach to obtaining a two-dimensional representation of geometry on a floor plan
    'representation': get the simplified representation of the geometry
    'dissolve': conceptual method to merge other element
    'to_xml': Conceptual method to get the xml of the geo attribute
    fromDict: construct an element from a dictionary which may be given by toDictionary method from a xmlTree

    """
    __slots__ = ['__geometries', 'level', 'offset', 'Uid', '__glazingElement', 'parent', 'neighbor', 'isOuter', 'space','shading']

    def __init__(self, model: MoosasContainer,
                 faceId: str | list[str] | np.ndarray[str] | MoosasGeometry | list[MoosasGeometry] | np.ndarray[
                     MoosasGeometry], level: float = None,
                 offset: float = None,
                 glazingId: str | list[str] | np.ndarray[str] = None,
                 glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement] = None, space=None,
                 uid=None):
        self.parent: MoosasContainer = model  # this is MoosasModel !!!
        self.Uid: str = generate_code(6) if uid is None else uid
        self.level: float = level
        self.offset: float = offset
        self.shading=[]
        self.__glazingElement: list[MoosasElement] = mixItemListToList(
            glazingElement) if glazingElement is not None else []
        if glazingId is not None:
            self.__glazingElement += self.glazingElementFromId(glazingId)
        self.space: list[str] = mixItemListToList(space) if space is not None else []
        self.isOuter: bool = True
        self.neighbor = {}

        # get the geometry(s)
        faceId = mixItemListToList(faceId)
        self.__geometries: np.ndarray[MoosasGeometry] = np.array([])
        for idd in faceId:
            if isinstance(idd, str):
                try:
                    idd = model.geoId.index(idd)
                except ValueError as ve:
                    raise ValueError(f"index {idd} is not in the library.")
                self.__geometries: np.ndarray[MoosasGeometry] = np.append(self.__geometries, model.geometryList[idd])
            elif isinstance(idd, MoosasGeometry):
                self.__geometries: np.ndarray[MoosasGeometry] = np.append(self.__geometries, idd)
            else:
                raise TypeError("idd must be either a string or a MoosasGeometry")

    @property
    def glazingElement(self) -> list[MoosasGlazing | MoosasSkylight]:
        """protect the __glazingElement attribute"""
        return mixItemListToList(self.__glazingElement)

    @property
    def glazingId(self):
        """get glazingId from glazingElement"""
        glsId = [ids for gls in self.glazingElement for ids in mixItemListToList(gls.Uid)]
        return glsId

    @property
    def face(self) -> pygeos.Geometry | np.ndarray[pygeos.Geometry]:
        """if the element only contains one face, a pygoes.Geometry will be return
        if you want to get a list anyway,
        you can call mixItemListToList() func in utils.tools.
        """
        return mixItemListToObject([geo.face for geo in self.__geometries])

    @property
    def mergedFace(self) -> pygeos.Geometry:
        """return a single face merging all faces contained in this element"""
        if len(self.__geometries) == 1:
            return self.__geometries[0].face
        proj = Projection(origin=np.mean(pygeos.get_coordinates(self.face,include_z=True),axis=0),unitZ=self.normal)
        UVFaces = [proj.toUV(g) for g in self.face]
        mergedUVFace = pygeos.force_3d(pygeos.union_all(pygeos.force_2d(UVFaces)),z=0)
        return proj.toWorld(mergedUVFace)
    @property
    def holes(self) -> pygeos.Geometry | np.ndarray[pygeos.Geometry]:
        return [h for geo in self.__geometries for h in geo.holes]

    @property
    def normal(self) -> np.ndarray:
        """if the element contains multi faces,
        the normal has the best description of the faces will be returned"""
        if len(self.__geometries) == 1:
            return Vector(self.__geometries[0].normal).uniform.unit().array

        # PCA1: get covariance matrix
        coordinates = pygeos.get_coordinates([geo.face for geo in self.__geometries], include_z=True) - np.array(
            self.getWeightCenter())
        C = np.zeros((3, 3))
        for coor in coordinates:
            C += np.matmul(coor.reshape(3, 1), coor.reshape(1, 3))
        C /= len(coordinates)

        # PCA2: get minimum characteristic
        eig_values, eig_vectors = np.linalg.eig(C)
        return Vector(eig_vectors[np.argmin(eig_values)]).unit().array

    @property
    def faceId(self) -> str | np.ndarray[str]:
        """if the element only contains one face, a str will be return
            if you want to get a list anyway,
            you can call mixItemListToList() func in utils.tools.
        """
        return mixItemListToObject([geo.faceId for geo in self.__geometries])

    @property
    def category(self) -> int | np.ndarray[int]:
        """if the element only contains one face, a int will be return
            if you want to get a list anyway,
            you can call mixItemListToList() func in utils.tools.
        """
        return mixItemListToObject([geo.category for geo in self.__geometries])

    @property
    def area(self) -> float:
        """quick link to self.area3d"""
        return self.area3d()

    @property
    def elevation(self) -> float:
        """correct elevation of the object"""
        return self.offset + self.level

    @property
    def wwr(self) -> float:
        """calculate Window Wall Ratio based on self.area3d()
        the wwr is not based on exact surface area of the window object, but based on the projection on the wall surface.
        """
        gFace = []
        for glsFace in self.glazingElement:
            gFace = np.append(gFace, glsFace.face)
        areaGlazing = self.area3d(faces=gFace)
        surface = [pygeos.polygons(pygeos.get_exterior_ring(f)) for f in mixItemListToList(self.face)]
        areaSurface = self.area3d(faces=surface)
        return areaGlazing / areaSurface

    @property
    def firstFaceId(self):
        """give a single faceid,
        which can accelerate the calculation and avoid error sometimes.
        for example, the MoosasGlazing/MoosasSkylight/MoosasFace object are all contain only one face.
        and the searchBy() func in utils.tools only supports singe attr in searching.
        ***actually searching by list are valid in python 3.10
        """
        if type(self.faceId) != np.ndarray:
            return self.faceId
        else:
            return self.faceId[0]

    def glazingElementFromId(self, glazingIds) -> list[MoosasGlazing | MoosasSkylight]:
        """get the glazing object in a ndarray
        the glazing are searchBy firstFaceId, since all glazing only contains one face.
        """
        glsid = mixItemListToList(glazingIds)
        if len(glsid) == 0:
            return []
        gls = []
        gls = np.append(gls,
                        np.array(self.parent.glazingList)[searchBy('Uid', glsid, self.parent.glazingList)])
        gls = np.append(gls,
                        np.array(self.parent.skylightList)[searchBy('Uid', glsid, self.parent.skylightList)])
        return list(gls)

    def replaceGeo(self, geoId):
        # get the geometry(s)
        faceId = mixItemListToList(geoId)
        self.__geometries: np.ndarray[MoosasGeometry] = np.array([])
        for idd in faceId:
            try:
                idd = self.parent.geoId.index(idd)
            except:
                raise ValueError(f"index {idd} is not in the library.")
            self.__geometries: np.ndarray[MoosasGeometry] = np.append(self.__geometries, self.parent.geometryList[idd])

    def delete(self):
        for geo in self.__geometries:
            geo.delete = True

    def area3d(self, faces=None, project=None) -> float:
        """use projection to get the correct area of the object"""
        if project is None:
            trans = Projection(self.getWeightCenter(), self.normal)
        else:
            trans = project
        if faces is None:
            faces = np.array(self.face).flatten()
        # print(self.face)
        # [print(faceNormal(face), self.normal) for face in faces]
        area = np.sum([pygeos.area(trans.toUV(face)) for face in faces]).item()
        return area

    def faceUV(self, uniform=False) -> list[pygeos.Geometry]:
        """Ver1.3 The projection class is added to perform UV expression on the surface and the glass surface
        get the UV faces
        """
        trans = Projection(self.getWeightCenter(), self.normal)
        faces = np.array(self.face).flatten()
        faces = [pygeos.force_2d(trans.toUV(face)) for face in faces]
        if uniform:
            boundaryBox = pygeos.get_coordinates(faces)
            boundaryBox = [[np.min(boundaryBox.T[0]), np.min(boundaryBox.T[1])],
                           [np.max(boundaryBox.T[0]), np.max(boundaryBox.T[1])]]
            uniformFaces = []
            for face in faces:
                face = pygeos.get_coordinates(face)
                for i in range(len(face)):
                    face[i][0] = (face[i][0] - boundaryBox[0][0]) / (boundaryBox[1][0] - boundaryBox[0][0])
                    face[i][1] = (face[i][1] - boundaryBox[0][1]) / (boundaryBox[1][1] - boundaryBox[0][1])
                uniformFaces.append(pygeos.polygons(face))

            return uniformFaces
        else:
            return faces

    def glazingUV(self, uniform=False) -> list[pygeos.Geometry]:
        """Ver1.3 The projection class is added to perform UV expression on the surface and the glass surface
            get the UV glazing faces
        """
        faces = []
        gidList = []
        for gElement in self.glazingElement:
            gidList += mixItemListToList(gElement.faceId)
        for gid in gidList:
            gface = self.parent.geoFaceList[self.parent.geoId.index(gid)]
            trans = Projection(self.getWeightCenter(), self.normal)
            faces.append(trans.toUV(gface))
        if uniform:
            boundaryBox = pygeos.get_coordinates(np.array(self.face).flatten())
            boundaryBox = [[np.min(boundaryBox.T[0]), np.min(boundaryBox.T[1])],
                           [np.max(boundaryBox.T[0]), np.max(boundaryBox.T[1])]]
            uniformFaces = []
            for face in faces:
                face = pygeos.get_coordinates(face)
                for i in range(len(face)):
                    face[i][0] = (face[i][0] - boundaryBox[0][0]) / (boundaryBox[1][0] - boundaryBox[0][0])
                    face[i][1] = (face[i][1] - boundaryBox[0][1]) / (boundaryBox[1][1] - boundaryBox[0][1])
                uniformFaces.append(pygeos.polygons(face))
            return uniformFaces
        else:
            return faces

    def getEdgeStr(self) -> list[str]:
        """get a unique edge string of the boundary, ignore the direction of the edge."""
        edge_str_s = set()
        for geo in self.__geometries:
            edge_str_s = edge_str_s | set(geo.getEdgeStr())
        return list(edge_str_s)

    def getWeightCenter(self) -> np.ndarray[np.ndarray]:
        point_list = pygeos.get_coordinates(self.face, include_z=True)[:-1]
        return np.array([np.mean(point_list.T[0]), np.mean(point_list.T[1]), np.mean(point_list.T[2])])

    def add_glazing(self, glazingObject: MoosasGlazing | MoosasSkylight):
        self.__glazingElement = list(np.append(self.__glazingElement, glazingObject))
        glazingObject.parentFace = self

    def dissolve(self, others):
        """method to merge multiple elements"""
        if not (isinstance(others, list) or isinstance(others, np.ndarray)):
            others = [others]
        others = list(others)
        target = None
        for o in others:
            # find face with coEdge and merge it
            edgeStr = set(self.getEdgeStr()) & set(o.getEdgeStr())
            if len(edgeStr) > 0:
                target = o
                break
        if target:
            self._merge(target)
            # continue to merge others
            others.remove(target)
            self.dissolve(others)
        else:
            return

    def _merge(self, other):
        """flip all face to the same side normal"""
        edgeStr = list(set(self.getEdgeStr()) & set(other.getEdgeStr()))[0]
        edgeStr = np.array([int(dim) / 100 for dim in edgeStr.split('_')[:-1]])

        poi1, poi2 = edgeStr[:3], edgeStr[3:]
        trans = Projection(poi1, poi2 - poi1)
        vectors = [
            self.getWeightCenter(),
            other.getWeightCenter(),
            self.normal,
            other.normal
        ]
        vectors = [trans.toUV(Vector(v).geometry) for v in vectors]
        unitxSelf, unitxOther, unitySelf, unityOther = vectors
        if Vector.dot(Vector.cross(unitxSelf, unitySelf), Vector.cross(unitxOther, unityOther)) > 0:
            for g in range(len(other.__geometries)):
                other.__geometries[g].flip = True

        """method to merge one other elements"""
        self.__geometries = np.append(self.__geometries, other.__geometries)
        self.offset = min(self.offset + self.level, other.offset + other.level) - min(self.level, other.level)
        self.level = min(self.level, other.level)
        for gls in other.glazingElement:
            self.add_glazing(gls)

    def force_2d(self) -> pygeos.Geometry:
        """return a linestring formatted in pygeos,or an array vector object"""
        raise NotImplementedError("force_2d method should be implemented in child class")

    def representation(self) -> pygeos.Geometry:
        """return a simplified representation for the geometry"""
        raise NotImplementedError("representation method should be implemented in child class")

    @classmethod
    def fromDict(cls, elementDict, model: MoosasContainer):
        """construct an element from a dictionary
        if the faceId record in the dictionary is already occurred in the model,
        the MoosasElement contains that faceId will be returned directly.
        """
        faceId = _getElement('faceId', dictionary=elementDict)[0]
        if not hasattr(model.builtData, 'elements') or not hasattr(model.builtData, 'glazing'):
            model.update()
        if faceId in model.builtData.elements:
            return model.builtData.elements[faceId]
        else:
            element = cls(
                faceId=_getElement('faceId', dictionary=elementDict)[0].split(" "),
                model=model,
                level=_getElement('level', dictionary=elementDict, strict=False)[0],
                offset=_getElement('offset', dictionary=elementDict, strict=False)[0],
                space=_getElement('space', dictionary=elementDict, strict=False)[0],
            )
            for ids in _getElement('faceId', dictionary=elementDict)[0].split(" "):
                model.builtData.elements[ids] = element
            glazingId: str = _getElement('glazingId', dictionary=elementDict, strict=False)[0]
            if glazingId is not None:
                for ids in glazingId.split(" "):
                    if ids not in model.builtData.glazing:
                        glsGeometry: MoosasGeometry = model.findFace(ids)[0]
                        if np.abs(Vector.dot(glsGeometry.normal, Vector([0, 0, 1]))) >= geom.HORIZONTAL_ANGLE_THRESHOLD:
                            glsElement = MoosasSkylight(model, glsGeometry.faceId)
                            model.skylightList.append(glsElement)
                        else:
                            glsElement = MoosasGlazing(model, glsGeometry.faceId)
                            model.glazingList.append(glsElement)
                        element.add_glazing(glsElement)
                        model.builtData.glazing[ids] = glsElement
                    else:
                        element.add_glazing(model.builtData.glazing[ids])

    def to_xml(self, model: MoosasContainer, element_tag='geometry', writeGeometry=False) -> ET.Element:
        """get a dictionary of all information we get for this object.
        it can be translated to json by toDictionary() func in the uitls package
        """
        geometry = ET.Element(element_tag)
        idList = np.array(self.faceId).flatten()
        glsIdList = np.array(self.glazingId).flatten()
        spcList = np.array(self.space).flatten()
        '''
            face, faceId, normal, level=None, offset=None, area=None, model = None, glazingId = None
            'face', 'level', 'offset', 'area', 'faceId', 'Uid', 'normal','glazingId','parent','isOuter','space'
        '''
        ET.SubElement(geometry, "Uid").text = str(self.Uid)
        ET.SubElement(geometry, "faceId").text = ' '.join(idList.astype(str))
        ET.SubElement(geometry, "level").text = str(self.level)
        ET.SubElement(geometry, "offset").text = str(self.offset)
        ET.SubElement(geometry, "area").text = str((self.area) / INCH_METER_MULTIPLIER_SQR)
        ET.SubElement(geometry, "glazingId").text = ' '.join(glsIdList.astype(str))
        ET.SubElement(geometry, "height").text = str((self.level + self.offset) / INCH_METER_MULTIPLIER)
        ET.SubElement(geometry, "normal").text = ' '.join(Vector(self.normal).array.astype(str))
        ET.SubElement(geometry, "external").text = str(self.isOuter)
        ET.SubElement(geometry, "s").text = str(spcList.astype(str))
        neighbor = ET.SubElement(geometry, "neighbor")
        for key in self.neighbor:
            obj = ET.SubElement(neighbor, "edge")
            obj.set("key", key)
            obj.text = str(' '.join(self.neighbor[key]))
        if writeGeometry:
            geo = ET.SubElement(geometry, "geometries")
            for pts in pygeos.get_coordinates(self.face, include_z=True).astype(str):
                ET.SubElement(geo, "pt").text = ' '.join(pts)

        return geometry


class MoosasFace(MoosasElement):
    """
    The base class, which records the horizontal face
    since we also have MoosasFloor to record multi-surface,
    we strictly require the face attribute only contain one geometry
    """
    __slots__ = ['parentFloors']

    def __init__(self, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str], level: float = None,
                 offset: float = None, glazingId=None,
                 glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement] = None, space=None,
                 uid=None):
        if not isinstance(faceId, str):
            raise ValueError("MoosasFace should only contain one geometry")
        uid = f"face_{mixItemListToList(faceId)[0]}" if uid is None else uid
        super(MoosasFace, self).__init__(model, faceId, level=level, offset=offset, glazingElement=glazingElement,
                                         space=space, glazingId=glazingId, uid=uid)
        self.parentFloors: list[MoosasFloor] = []
        # calculates the plane elevation
        pointlist = pygeos.get_coordinates(self.face, include_z=True)
        coordinates_z = pointlist[:, 2]
        # Ver1.2 Changing to an average height to define the surface height is prone to errors on the bottom surface
        _facebotheight = np.round(np.mean(coordinates_z), 3)
        if np.isnan(_facebotheight):
            raise GeometryError(self.face, "invalid geometry")
        pointlist = list(pointlist)
        pointlist.pop()

        for bld_level in model.levelList:
            if np.abs(_facebotheight - bld_level) < geom.LEVEL_MAX_OFFSET:
                self.level = bld_level
        if self.level is None:
            self.level = _facebotheight
            model.levelList.append(self.level)
            model.levelList.sort()
        self.offset = _facebotheight - self.level

    @classmethod
    def fromDict(cls, elementDict, model: MoosasContainer):
        element = super(MoosasFace, cls).fromDict(elementDict, model)
        faceElement = cls(model, element.faceId, element.glazingId)
        for fid in mixItemListToList(element.faceId):
            model.builtData.elements[fid] = faceElement
        return faceElement

    def force_2d(self, region=True) -> pygeos.Geometry:
        # region is an useless arg to ensure consistency

        return pygeos.force_2d(self.face)

    def to_xml(self, model: MoosasContainer, Element_tag='face', writeGeometry=False):
        face_xml = super(MoosasFace, self).to_xml(model, Element_tag, writeGeometry=writeGeometry)

        return face_xml

    def dissolve(self, wall):
        raise Exception("MoosasFace cannot used to dissolve")

    def representation(self) -> pygeos.Geometry:
        return pygeos.force_3d(self.force_2d(), z=self.elevation)


class MoosasSkylight(MoosasFace):
    '''
        一个特别简单的glazing类，只为与Moosasface区分开
        '''
    __slots__ = ['parentFace']

    def __init__(self, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str], level: float = None,
                 offset: float = None, glazingId=None,
                 glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement] = None, space=None,
                 uid=None):
        if not isinstance(faceId, str):
            raise ValueError("MoosasFace should only contain one geometry")
        uid = f"sky_{mixItemListToList(faceId)[0]}" if uid is None else uid
        super(MoosasSkylight, self).__init__(model, faceId, level=level, offset=offset, glazingElement=glazingElement,
                                             space=space, glazingId=glazingId, uid=uid)
        self.parentFace: MoosasFace | None = None

    @property
    def orientation(self):
        return Vector(self.normal)

    def apply_to_face(self, face: MoosasFace):
        face.add_glazing(self)
        # self.parentFace = face
        # face.glazingId.append(self.Uid)

    def to_xml(self, model: MoosasContainer, Element_tag='skylight', writeGeometry=False):
        skylightXml = super(MoosasSkylight, self).to_xml(model, Element_tag, writeGeometry=writeGeometry)
        ET.SubElement(skylightXml, "parentFace").text = str(self.parentFace.Uid)
        ET.SubElement(skylightXml, "shadingid").text = ' '.join(np.array(self.shading).astype(str))
        return skylightXml


class MoosasWall(MoosasElement):
    """
    The basic class, which expresses the read vertical face, has the following new members:
        Bottom Data (Unique):
        '__botProjection': The bottom projection line of the wall, which will be used to identify the closed area, represented by a sequence of dots, is automatically generated
        Top Data (Unique):
        '__topProjection': The projection line on the top surface of the wall, represented by a sequence of dots, is automatically generated
        'toplevel': The top elevation of the wall, defined by the floor, with an elevation difference greater than 1.5 meters, is automatically generated
        'topoffset': The elevation offset of the top surface of the wall, which is less than plus or minus 1.5 meters, is automatically generated
    """
    __slots__ = ['__botProjection', '__topProjection', 'toplevel', 'topoffset', 'orientation']

    def __init__(self, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str], level: float = None,
                 offset: float = None, glazingId=None,
                 glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement] = None, space=None,
                 uid=None):
        uid = f"wall_{mixItemListToList(faceId)[0]}" if uid is None else uid
        super(MoosasWall, self).__init__(model, faceId, level=level, offset=offset, glazingElement=glazingElement,
                                         space=space, glazingId=glazingId, uid=uid)
        pointlist = pygeos.get_coordinates(self.face, include_z=True)
        self.toplevel = None
        self.isOuter = True
        self.orientation: Vector = Vector(self.normal)

        # find the bottom height of the wall
        coordinates_z = pointlist[:, 2]
        botheight = np.round(np.min(coordinates_z), 3)
        topheight = np.round(np.max(coordinates_z), 3)

        for i in range(len(model.levelList) - 1):
            # best match: the wall located between two level
            if model.levelList[i] <= botheight and model.levelList[i + 1] >= topheight:
                self.level = model.levelList[i]
                self.toplevel = model.levelList[i + 1]
                break
            # second match: the wall cross a level
            if botheight <= model.levelList[i] <= topheight:
                if model.levelList[i] - botheight < topheight - model.levelList[i]:
                    self.level = model.levelList[i]
                    self.toplevel = model.levelList[i + 1]
                else:
                    self.toplevel = model.levelList[i]
                    if i == 0:
                        self.level = model.levelList[i]
                    else:
                        self.level = model.levelList[i - 1]
                break

        # worst match: the wall locate below the whole building or above the whole building (mostly invalid)
        if self.level is None:
            if topheight <= model.levelList[0]:
                self.level = model.levelList[0]
                self.toplevel = model.levelList[0]
            else:
                self.level = model.levelList[-1]
                self.toplevel = model.levelList[-1]

        self.offset = botheight - self.level
        self.topoffset = topheight - self.toplevel

        # prepare the projection for the force_2d method
        self.prepareProjection()

    @classmethod
    def fromDict(cls, elementDict, model: MoosasContainer):
        element = super(MoosasWall, cls).fromDict(elementDict, model)
        faceElement = cls(model, element.faceId, element.glazingId)
        for fid in mixItemListToList(element.faceId):
            model.builtData.elements[fid] = faceElement
        return faceElement

    @classmethod
    def fromProjection(cls, prjLine: pygeos.Geometry, bottom: float, top: float, model: MoosasContainer,
                       airBoundary=False):
        stPoint, edPoint = pygeos.get_coordinates(prjLine)
        airBound = [
            np.append(stPoint, bottom),
            np.append(edPoint, bottom),
            np.append(edPoint, top),
            np.append(stPoint, top),
            np.append(stPoint, bottom),
        ]

        if airBoundary:
            idx = model.includeGeo(pygeos.polygons(airBound), cat=2)
            wall = cls(model, idx)
            gls = MoosasGlazing(model, idx)
            model.glazingList = np.append(model.glazingList, gls)
            wall.add_glazing(gls)
        else:
            idx = model.includeGeo(pygeos.polygons(airBound), cat=0)
            wall = cls(model, idx)
        return wall

    @classmethod
    def break_(cls, wall: MoosasWall, breakPoints: list[pygeos.Geometry] | pygeos.Geometry):
        twins = pygeos.points(pygeos.get_coordinates(wall.force_2d()))
        if len(twins) < 2:
            return [wall]
        bottom = wall.level + wall.offset
        top = wall.toplevel + wall.topoffset
        breakPoints = np.array([breakPoints]).flatten()
        # breakPoints = [breakP for breakP in breakPoints if pygeos.contains(wall.force_2d(), breakP)]
        breakPoints = np.append(twins, breakPoints)
        coor = pygeos.get_coordinates(breakPoints)
        argIdx = np.lexsort((coor[:, 0], coor[:, 1]))
        st, ed = list(argIdx).index(0), list(argIdx).index(1)
        argIdx = argIdx[min(st, ed):max(st, ed) + 1]
        breakPoints = breakPoints[argIdx]
        if len(breakPoints) < 3:
            # dont need to break
            return [wall]
        # print("\nbreakFunction",cls)
        newWalls = cls.fromSeriesPoint(breakPoints, bottom, top, wall.glazingElement, wall.parent)
        return newWalls

    @classmethod
    def fromSeriesPoint(cls, breakPoints: list[pygeos.Geometry] | pygeos.Geometry, bottom: float, top: float,
                        gls: list[MoosasGlazing], model: MoosasContainer) -> list[MoosasWall]:
        """partition the walls by sorting their coordinates and making polygon using the top and bottom boundaries
        the glazing of all walls will be collected and try to attach to the new wall again.
        """
        coor = list(pygeos.get_coordinates(breakPoints))
        coor.sort(key=lambda x: (x[0], x[1]))

        wallNew: list[MoosasWall] = []
        for thisPoi, nextPoi in zip(coor[:-1], coor[1:]):
            if Vector(thisPoi - nextPoi).length() > geom.POINT_PRECISION:
                edges = pygeos.linestrings([thisPoi, nextPoi])
                wallNew.append(cls.fromProjection(edges, bottom, top, model))
        # oldGls = len(gls)
        gls = [newg for g in gls for newg in MoosasGlazing.break_(g, breakPoints)]
        # print("\n???", oldGls,len(gls))
        # print("\n!!!",len(model.glazingList))
        for glazing in gls:
            if glazing is not None:
                if not glazing in model.glazingList:
                    model.glazingList = list(np.append(model.glazingList, glazing))
                for wall in wallNew:
                    if pygeos.contains(wall.force_2d(), glazing.force_2d()):
                        wall.add_glazing(glazing)
                        break

        return wallNew

    @property
    def height(self):
        top = [self.toplevel + self.topoffset] + [g.toplevel + g.topoffset for g in self.glazingElement]
        bot = [self.level + self.offset] + [g.level + g.offset for g in self.glazingElement]
        return np.max(top) - np.min(bot)

    def prepareProjection(self):
        pointlist = pygeos.get_coordinates(self.face, include_z=True)
        bottom = np.min(pointlist[:, 2])
        above = np.max(pointlist[:, 2])
        self.__botProjection = []
        for _point in pointlist:
            if np.abs(_point[2] - bottom) < geom.POINT_PRECISION:
                self.__botProjection.append(pygeos.set_precision(pygeos.points(_point), geom.POINT_PRECISION))
        self.__topProjection = []
        for _point in pointlist:
            if np.abs(_point[2] - above) < geom.POINT_PRECISION:
                self.__topProjection.append(pygeos.set_precision(pygeos.points(_point), geom.POINT_PRECISION))

    # conceptual method in the based class
    def force_2d(self, top=False, region=False) -> pygeos.Geometry | None:
        if region:
            lBot, lTop = self.force_2d(False, False), self.force_2d(True, False)
            if not pygeos.disjoint(lBot, lTop):
                return lBot
            lBot = pygeos.get_coordinates(lBot).tolist()
            lTop = pygeos.get_coordinates(lTop).tolist()
            if len(lTop) == 1 and len(lBot) == 1:
                return pygeos.linestrings(list(lBot) + list(lTop))
            lTop.reverse()
            lbound = list(lBot) + list(lTop)
            for i in range(2, len(lbound)):
                # detect the co-linear projections
                if not Vector.parallel(Vector(Vector(lbound[1]) - Vector(lbound[0])),
                                       Vector(Vector(lbound[i]) - Vector(lbound[0]))):
                    return simplify(pygeos.polygons(lbound + [lbound[0]]))
            return pygeos.linestrings([lbound[0], lbound[-1]])

        else:
            if top:
                target = self.__topProjection
            else:
                target = self.__botProjection

            # invalid projection, try to use the bottom projection
            if len(target) < 2:
                if top:
                    return self.force_2d(False, False)
                else:
                    return target[0]
            botx = np.array([pygeos.get_x(poi) for poi in target])
            boty = np.array([pygeos.get_y(poi) for poi in target])
            if np.max(botx) == np.min(botx):
                p1 = np.array([botx[np.argmin(boty)], boty[np.argmin(boty)]])
                p2 = np.array([botx[np.argmax(boty)], boty[np.argmax(boty)]])
            else:
                p1 = np.array([botx[np.argmin(botx)], boty[np.argmin(botx)]])
                p2 = np.array([botx[np.argmax(botx)], boty[np.argmax(botx)]])
            if np.sum(np.array(p1 - p2)) != 0:
                return pygeos.linestrings([p1, p2])
            else:
                return pygeos.points(p1)

    def to_xml(self, model: MoosasContainer, Element_tag='wall', writeGeometry=False):
        wall = super(MoosasWall, self).to_xml(model, Element_tag, writeGeometry=writeGeometry)
        'faces, faceId, normal, glazingId=None, _area=None'
        ET.SubElement(wall, 'length').text = str(pygeos.length(self.force_2d()) / INCH_METER_MULTIPLIER)
        ET.SubElement(wall, 'force2d').text = str(
            pygeos.get_coordinates(self.force_2d(), include_z=False) / INCH_METER_MULTIPLIER)
        ET.SubElement(wall, 'toplevel').text = str(self.toplevel)
        ET.SubElement(wall, 'topoffset').text = str(self.topoffset)

        return wall

    def dissolve(self, wall: MoosasWall | list[MoosasWall]):
        if isinstance(wall, MoosasWall):
            wall = [wall]
        if len(wall) == 0:
            return
        """merge two faces into one MoosasWall object"""
        super().dissolve(wall)
        toplevel = max(self.toplevel, np.max([w.toplevel for w in wall]))
        self.topoffset = max(self.topoffset + self.toplevel,
                             np.max([w.topoffset for w in wall]) + np.max([w.toplevel for w in wall])) - toplevel
        self.toplevel = toplevel
        self.prepareProjection()

    def representation(self) -> pygeos.Geometry:
        lBot = pygeos.force_3d(self.force_2d(False, False), z=self.level + self.offset)
        lTop = pygeos.force_3d(self.force_2d(True, False), z=self.toplevel + self.topoffset)

        lBot = pygeos.get_coordinates(lBot, include_z=True).tolist()
        lTop = pygeos.get_coordinates(lTop, include_z=True).tolist()
        lTop.reverse()
        return pygeos.polygons(list(lBot) + list(lTop) + [lBot[0]])


class MoosasGlazing(MoosasWall):
    """
    glazing element based on MoosasWall.
    this element should only contain one geometry.

    attribute:
    parentFace: the Uid of parent MoosasWall element
    orientation: normal facing outside.
    """
    __slots__ = ['parentFace']

    def __init__(self, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str], level: float = None,
                 offset: float = None, glazingId=None,
                 glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement] = None, space=None,
                 uid=None):
        uid = f"gls_{mixItemListToList(faceId)[0]}" if uid is None else uid
        super(MoosasGlazing, self).__init__(model, faceId, level=level, offset=offset, glazingElement=glazingElement,
                                            space=space, glazingId=glazingId, uid=uid)
        self.parentFace: MoosasWall | None = None

        if self.offset < -0.2:
            new_level = model.levelList[model.levelList.index(self.level) - 1]
            # print('\nMOVE!!!!!!!!!!!!!!!!!!!!!!!!!!!',new_level)
            self.offset = self.level + self.offset - new_level
            self.level = new_level
        if self.topoffset < -0.1:
            new_level = model.levelList[model.levelList.index(self.toplevel) - 1]
            self.topoffset = self.toplevel + self.topoffset - new_level
            self.toplevel = new_level

    @classmethod
    def fromProjection(cls, prjLine: pygeos.Geometry, bottom: float, top: float, model: MoosasContainer,
                       airBoundary=False):
        if pygeos.length(prjLine) < geom.POINT_PRECISION:
            return None
        stPoint, edPoint = pygeos.get_coordinates(prjLine)
        airBound = [
            np.append(stPoint, bottom),
            np.append(edPoint, bottom),
            np.append(edPoint, top),
            np.append(stPoint, top),
            np.append(stPoint, bottom),
        ]
        idx = model.includeGeo(pygeos.polygons(airBound), cat=0)
        gls = cls(model, idx)
        return gls

    def force_2d(self, top=False, region=False):
        return super(MoosasGlazing, self).force_2d(top, region)

    def to_xml(self, model, Element_tag='glazing', writeGeometry=False):
        glazingXml = super(MoosasGlazing, self).to_xml(model, Element_tag, writeGeometry=writeGeometry)
        ET.SubElement(glazingXml, "parentFace").text = self.parentFace.Uid
        ET.SubElement(glazingXml, "shadingid").text = ' '.join(np.array(self.shading).astype(str))
        return glazingXml


class MoosasFloor:
    """
    this class define a floor contains multi horizontal/incline face elements.

    init:
    face: list of MoosasFace

    classmethod:
    fromDict: construct a floor from a dictionary, which may be given by toDictionary method from a xmlTree

    attribute:
    'face': The set of horizontal planes that make up the slab, class Moosasface
    ***Many-to-one!Since the slab and ceiling coincide, there may be two identical Moosasfloors in the same location
    'Uid': The id of the element

    properties:
    'area': total face area
    'level': floor level
    'offset':average offset of all faces
    'glazingId': all glazingId of this element
    'glazingElement': all skylight elements of this element

    method:
    'getWeightCenter': the weight center of all geometries
    'force_2d': 2d projection of this element
    'to_xml': xmlTree object of this element, can also be used to create a some MoosasFloor


    'level': The elevation of the floor slab, defined by the floor, with an elevation difference
    greater than 1.5 meters
    'area': The total area of the quilt
    """
    __slots__ = ['face', 'Uid']

    def __init__(self, faces: list[MoosasFace]):
        faces = mixItemListToList(faces)
        self.Uid = generate_code(4)
        self.face: list[MoosasFace] = faces
        for f in self.face:
            f.parentFloors.append(self)

    @classmethod
    def fromDict(cls, floorDict, model: MoosasContainer):
        faces = _getElement('face', dictionary=floorDict)
        return cls([MoosasFace.fromDict(f, model) for f in faces])

    @property
    def area(self) -> float:
        return np.sum([f.area for f in self.face]).item()

    @property
    def level(self) -> float:
        return self.face[0].level

    @property
    def offset(self) -> float:
        return np.mean([f.offset for f in self.face]).item()

    @property
    def glazingId(self) -> list[str]:
        glsId = []
        for f in self.face:
            glsId = np.append(glsId, f.glazingId)
        return glsId

    @property
    def glazingElement(self) -> list[MoosasSkylight]:
        glsObj = []
        for f in self.face:
            glsObj = np.append(glsObj, f.glazingElement)
        return glsObj

    def getWeightCenter(self) -> np.ndarray:
        center = np.array([face.getWeightCenter() for face in self.face])
        return np.array([np.mean(x) for x in center.T])

    def force_2d(self) -> pygeos.Geometry:
        faces = [f.force_2d() for f in self.face]
        try:
            return pygeos.union_all(faces, grid_size=geom.POINT_PRECISION)
        except:
            return pygeos.multipolygons(faces)

    def to_xml(self, model: MoosasContainer, Element_tag='floor', writeGeometry=False) -> ET.Element:
        floor = ET.Element(Element_tag)
        for f in self.face:
            ET.SubElement(floor, "face").text = f.Uid
            # floor.append(f.to_xml(model,writeGeometry=writeGeometry))
        return floor


class MoosasEdge:
    """
    This class specifies a closed envelope

    attributes:
    'wall': The set of areas that make up the envelope, class Moosaswall
    'Uid': Unique id for the edge
    '__botBound': The lower contour of the envelope, which is used to delineate the floor slab
    '__topBound': The upper contour of the envelope, used to deline the ceiling

    properties:
    'FactorOfWall': An outward-facing 2d vector set made by ccw calculation, which is not normal
    'level': The lower elevation of the envelope, which is used to reduce the scope of floor identification
    'toplevel': The upper elevation of the envelope, which is used to reduce the ceiling identification area
    """
    __slots__ = ('wall', 'Uid', '__botBound', '__topBound','internalMass')

    def __init__(self, walls: list[MoosasWall]):
        self.wall: list[MoosasWall] = walls
        self.__botBound = []
        self.__topBound = []
        self.Uid = generate_code(4)
        # 创造底面/顶面投影多边形
        if len(self.wall) < 3:
            raise GeometryError(walls, "A boundary requires at least 3 walls.")
        self.prepareBoundary()
        self.internalMass: list[MoosasElement] = []
        for w in walls:
            self.internalMass+=w.shading

    def prepareBoundary(self):
        for _wall in self.wall:
            self.__botBound.append(_wall.force_2d())
            self.__topBound.append(_wall.force_2d(top=True))
            # if _wall.level>self.level: self.level=_wall.level
            # if _wall.toplevel < self.toplevel: self.toplevel = _wall.toplevel
        # print(self.__botBound,self.__topBound)
        self.__botBound = self.get_polygon(self.__botBound)
        try:
            self.__topBound = self.get_polygon(self.__topBound)
        except:
            self.__topBound = self.__botBound

        # overwrite orientation for walls and glazings
        for _wall, _factor in zip(self.wall, self.FactorOfWall):
            _wall.orientation = _factor
            for gls in _wall.glazingElement:
                gls.orientation = _factor

    @classmethod
    def fromDict(cls, floorDict, model):
        faces = _getElement('face', dictionary=floorDict)
        return cls([MoosasWall.fromDict(f, model) for f in faces])

    @classmethod
    def difference(cls, mainEdge: MoosasEdge, subBoundary: pygeos.Geometry):
        if not mainEdge.is_valid():
            raise GeometryError(mainEdge, "invalid boundary:{}")
        if overlapArea(mainEdge.force_2d(), subBoundary) != pygeos.area(subBoundary):
            # must be the same or errors would occur when splitting the walls
            raise GeometryError(subBoundary, "invalid subBoundary in boundary divided:{}")

    @classmethod
    def selectWall(cls, boundary: pygeos.Geometry, walls: list[MoosasWall]):
        walls = np.array(walls).flatten()
        boundary = pygeos.get_coordinates(boundary)
        # from ..visual.geometry import plot_object
        # plot_object(walls,boundary,colors=['red','black'])
        edges = [pygeos.linestrings([poi1, poi2]) for poi1, poi2 in zip(boundary[:-1], boundary[1:])]
        validWalls = []
        for edg in edges:
            matched = False
            for w in walls:
                # print(edg, w.force_2d())
                if equals(edg, w.force_2d()):
                    validWalls.append(w)
                    matched = True
                    break
            if not matched:
                newWall = MoosasWall.fromProjection(edg,walls[0].level,walls[0].toplevel,walls[0].parent,True)
                walls[0].parent.wallList = list(np.append(walls[0].parent.wallList, newWall))
                validWalls.append(newWall)


        # print(edges,validWalls)
        # edge = cls(validWalls)
        # print([w.force_2d() for w in validWalls],"\n",edge.force_2d())
        return cls(validWalls)

    @property
    def parent(self):
        return self.wall[0].parent

    @property
    def level(self) -> float:
        return np.min([w.level for w in self.wall])

    @property
    def toplevel(self) -> float:
        return np.max([w.toplevel for w in self.wall])

    @property
    def elevation(self) -> float:
        return np.mean([w.elevation for w in self.wall]).item()

    @property
    def FactorOfWall(self) -> np.ndarray[Vector]:
        poly_coordinates = pygeos.get_coordinates(self.__botBound)
        if self.is_ccw():
            factor = np.array([0, 0, -1])
        else:
            factor = np.array([0, 0, 1])
        poly_vector = [poly_coordinates[i] - poly_coordinates[i - 1] for i in range(1, len(poly_coordinates))]
        return np.array([Vector(np.cross(factor, vec)) for vec in poly_vector])

    @property
    def area(self) -> float:
        return pygeos.area(self.force_2d())

    def getWeightCenter(self) -> np.ndarray:
        return np.mean(pygeos.get_coordinates([w.force_2d() for w in self.wall]), axis=0)

    def is_ccw(self) -> bool:
        # Improved method for pygeos.is_ccw()
        # accepts both convex & non-convex polygons，but maintains lower efficiency
        poilist = pygeos.get_coordinates(self.__botBound)
        veclist = [poilist[i] - poilist[i - 1] for i in range(1, len(poilist))]
        crosslist = [np.cross(veclist[i], veclist[i - 1]) for i in range(len(veclist))]
        ccw = np.sum([2 for crs in crosslist if crs < 0])
        ccw -= len(crosslist)
        # ccw: np.cross < 0 means that:
        #   1. the corner is a convex corner in a ccw polygon;
        #   2. the corner is a non-convex corner in a rccw polygon.
        # convex corners are always more than non-convex corners.
        # Therefore, ccw > 0 means that the polygon is ccw.
        return ccw > 0

    def get_polygon(self, target) -> pygeos.Geometry:
        def reverseTwin(point_twin):
            tmp = point_twin[0]
            point_twin[0] = point_twin[1]
            point_twin[1] = tmp
            return point_twin

        point_twin = [pygeos.points(pygeos.get_coordinates(pygeos.set_precision(line, geom.POINT_PRECISION))) for line
                      in target]
        if not pygeos.dwithin(point_twin[0][0], point_twin[-1][0], 1.2 * geom.POINT_PRECISION):
            if not pygeos.dwithin(point_twin[0][0], point_twin[-1][1], 1.2 * geom.POINT_PRECISION):
                point_twin[0] = reverseTwin(point_twin[0])

        for i in range(1, len(point_twin)):
            if not pygeos.dwithin(point_twin[i][0], point_twin[i - 1][1], 1.2 * geom.POINT_PRECISION):
                point_twin[i] = reverseTwin(point_twin[i])
        polyPoints = [twin[0] for twin in point_twin]
        # polyPoints = np.array([])
        # for twins in point_twin:
        #     connection = set(twins) & set(polyPoints)
        #     if len(connection) == 1 and len(polyPoints) >= 2:
        #         if list(connection)[0] == polyPoints[-2]:
        #             polyPoints = np.append(polyPoints[:-2], [polyPoints[-1], polyPoints[-2]])
        #     polyPoints = np.append(polyPoints, list(set(twins).difference(set(polyPoints))))
        # print(polyPoints)
        polyPoints = np.append(polyPoints, polyPoints[0])
        poly_coordinates = pygeos.get_coordinates(polyPoints)

        polyg = pygeos.polygons(poly_coordinates)
        if str(pygeos.is_valid_reason(polyg)).find('Self-intersection') != -1:
            polyg_ori = polyg
            polyg = makeValid(polyg)[0]
            print(f"******Warning: GeometryError, self-intersection:{polyg_ori.__repr__()}fix to {polyg.__repr__()}")
        return polyg

    def force_2d(self, top=False) -> pygeos.Geometry:
        if top:
            target = self.__topBound
        else:
            target = self.__botBound

        # if selfIntersect(target):
        #     raise f"self-intersection, top:{top} {target}"
        return target

    def is_valid(self) -> bool:
        try:
            if self.area < geom.ROOM_MIN_AREA:
                print('******Warning: GeometryError, area invalid, floor:', self.level)
                return False
            boundary_box = pygeos.get_coordinates(pygeos.boundary(self.force_2d()))
            dimension = [np.max(boundary_box[:, 0]) - np.min(boundary_box[:, 0]),
                         np.max(boundary_box[:, 1]) - np.min(boundary_box[:, 1])]
            if dimension[0] <= geom.ROOM_MIN_DIMENSION or dimension[1] <= geom.ROOM_MIN_DIMENSION:
                print('******Warning: GeometryError, dimension invalid %.3f' % dimension[0], '%.3f' % dimension[1],
                      'floor:', self.level)
                # print(boundary_box)
                return False
            if str(pygeos.is_valid_reason(self.force_2d())).find('Self-intersection') != -1:
                print("******Warning: GeometryError, self-intersection", self.force_2d())
                return False
        except:
            print('******Warning: GeometryError, Boundary validation failed, floor:', self.level)
            return False
        return True

    def to_xml(self, model: MoosasContainer, Element_tag='edge', writeGeometry=False):
        edge = ET.Element(Element_tag)
        for w, factor in zip(self.wall, self.FactorOfWall):
            factor = factor.array
            wall = ET.SubElement(edge, "wall")
            ET.SubElement(wall, "Uid").text = w.Uid
            ET.SubElement(wall, "normal").text = str(factor[0]) + ' ' + str(factor[1]) + ' ' + '0'
            # w_xml = w.to_xml(model,writeGeometry=writeGeometry)
            # normal = w_xml.findall("normal")
            # for i in range(len(normal)):
            #     normal[i].text = str(factor[0]) + ' ' + str(factor[1]) + ' ' + '0'
            # edge.append(w_xml)
        return edge


class MoosasSpace(object):
    """define a space with topology and related data.
    it can be a void if floor or ceiling is None or area of floor/ceiling < area of edge

    """
    __slots__ = ['floor', 'edge', 'ceiling', '__void', '__id', '__neighbor', 'internalMass', 'settings']

    def __init__(self, _floor: MoosasFloor | None, _edge: MoosasEdge, _ceiling: MoosasFloor | None,
                 void: list[MoosasSpace] = None):
        self.floor: MoosasFloor | None = _floor
        self.edge: MoosasEdge = _edge
        self.ceiling: MoosasFloor | None = _ceiling

        self.__neighbor = {}
        self.internalMass: list[MoosasElement] = _edge.internalMass
        self.__void: list[MoosasSpace] = [] if void is None else void
        self.__id: str = ''

        self.regenerateId()

        # Thermal Settings
        self.settings = {
            "zone_name": self.id,

            "zone_summerrad": None,  # summer radiant heat units:kwh
            "zone_winterrad": None,  # winter radiant heat units:kwh

            "zone_template": None
        }

        self.applySettings('climatezone3_GB/T51350-2019_RESIDENTIAL')

    @classmethod
    def fromDict(cls, spaceDict, model: MoosasContainer):
        edge = _getElement('edge', dictionary=spaceDict)[0]
        ceiling = _getElement('ceiling', dictionary=spaceDict, strict=False)[0]
        floor = _getElement('floor', dictionary=spaceDict, strict=False)[0]

        internalMass = _getElement('internalMass', dictionary=spaceDict, strict=False)
        void = _getElement('void', dictionary=spaceDict, strict=False)

        if ceiling:
            ceiling = MoosasFloor.fromDict(floor, model)
        if edge:
            edge = MoosasEdge.fromDict(edge, model)
        if floor:
            floor = MoosasFloor.fromDict(ceiling, model)
        space = cls(floor, edge, ceiling)

        if internalMass[0]:
            for _intWall in internalMass:
                space.addInternalMass(MoosasWall.fromDict(_intWall, model))

        if void[0]:
            for _void in void:
                space.add_void(cls.fromDict(_void, model))
        return space

    @property
    def neighbor(self) -> dict:
        return self.__neighbor

    @property
    def void(self) -> list[MoosasSpace]:
        return self.__void

    @property
    def parent(self):
        return self.edge.parent

    @property
    def id(self) -> str:
        return self.__id

    @property
    def area(self) -> float:
        area = self.edge.area
        if len(self.void) > 0:
            for _void in self.void:
                area -= _void.area
        return area

    @property
    def level(self) -> float:
        return self.edge.level

    @property
    def topLevel(self) -> float:
        if self.is_void():
            return self.edge.toplevel
        else:
            return self.ceiling.level

    @property
    def height(self) -> float:
        if self.is_void():
            return self.edge.toplevel - self.edge.level
        else:
            return self.ceiling.level + self.ceiling.offset - self.floor.level - self.floor.offset

    @property
    def spaceType(self) -> str:
        """Select one of the following types of the space:
        Corridor: most of the pieces are narrow and long
        MainSpace: the main space in the building, like the living room or the hall
        privateSpace: the small space in the building, provided for a few amount of persons
        """
        convexFaces, _ = triangulate2dFace(self.force_2d())
        narrowPart, mainPart = [], []
        for face in convexFaces:
            if pygeos.area(face) > 9.0:
                boxDict = bBox(face)
                xSize = boxDict['x-domain'][1] - boxDict['x-domain'][0]
                ySize = boxDict['y-domain'][1] - boxDict['y-domain'][0]
                if min(xSize, ySize) < 2.5:
                    narrowPart.append(face)
                elif max(xSize, ySize) / min(xSize, ySize) > 3 and min(xSize, ySize) < 5:
                    narrowPart.append(face)
                else:
                    mainPart.append(face)
        if len(mainPart) == 0:
            return 'Corridor'
        else:
            if np.sum([pygeos.area(p) for p in mainPart]) / 18 < 3.0:
                """space less for 3 person"""
                return 'privateSpace'
            else:
                return 'MainSpace'

    def regenerateId(self) -> str:
        """calculate the id for the space
        the id comes from 7 params,each params space two indent('0'to'9' & 'a'to'j')
        so the id will be encoded like this:
            0x 1a 2b 3c 4d 5e 6f 7g

        Returns:
            str: self.id
        """
        originalId = self.id
        walls = self.getAllFaces(to_dict=True)['MoosasWall']
        params = [self.area, self.height * 10, self.level * 10, len(walls)]
        params += list([np.sum([w.wwr * 100 for w in walls])])
        params += list(self.edge.getWeightCenter() * 10)
        self.__id = encodeParams(*params)
        # Record self.id to all MoosasGeometries
        for moface in self.getAllFaces(to_dict=False):
            if originalId != "" and originalId in moface.space:
                moface.space.remove(originalId)
            if not self.id in moface.space:
                moface.space.append(self.id)
        return self.__id

    def add_void(self, void: MoosasSpace) -> None:
        """add void to self.__void, and change the space attribute in self.getAllFaces()
        """
        self.__void.append(void)
        # Record self.id to all MoosasGeometries
        self.regenerateId()

    def force_2d(self, top=False) -> pygeos.Geometry:
        if len(self.void) > 0:
            outerRing = pygeos.linearrings(pygeos.get_coordinates(self.edge.force_2d(top)))
            innerRing = [pygeos.linearrings(pygeos.get_coordinates(v.edge.force_2d(top))) for v in self.void]
            polygon = pygeos.polygons(outerRing, holes=innerRing)
        else:
            polygon = self.edge.force_2d(top)
        return polygon

    def is_void(self):
        if not self.floor or not self.ceiling:
            return True
        if self.floor.area < self.area - geom.AREA_PRECISION:
            return True
        if self.ceiling.area < self.area - geom.AREA_PRECISION:
            # print(self.ceiling.face[0].face if len(self.ceiling.face)>0 else None)
            return True
        return False

    def boundBox(self) -> np.ndarray:
        facesCoor = [pygeos.get_coordinates(moface.face, include_z=True) for moface in self.getAllFaces(to_dict=False)]
        facesCoorMin = np.min([np.min(coor, axis=0) for coor in facesCoor], axis=0)
        facesCoorMax = np.max([np.max(coor, axis=0) for coor in facesCoor], axis=0)
        return np.array([facesCoorMin, facesCoorMax])

    def applySettings(self, buildingTemplateHint):
        if not isinstance(buildingTemplateHint, dict):
            if not isinstance(buildingTemplateHint, str):
                raise Exception(f'Key Error: template key error {buildingTemplateHint}')
            if buildingTemplateHint in self.parent.buildingTemplate:
                template = self.parent.buildingTemplate[buildingTemplateHint]
            else:
                for hint in self.parent.buildingTemplate:
                    if re.search(buildingTemplateHint,hint) is not None:
                        template = self.parent.buildingTemplate[hint]
                        buildingTemplateHint = hint
        else:
            template = buildingTemplateHint
            buildingTemplateHint = list(self.parent.buildingTemplate.values()).index(template)
            buildingTemplateHint = list(self.parent.buildingTemplate.keys())[buildingTemplateHint]
        self.settings['zone_template'] = buildingTemplateHint
        for key in template.keys():
            self.settings[key] = template[key]
    def add_neighbor(self, neighbor_id, element: MoosasElement):
        if neighbor_id not in self.neighbor:
            self.neighbor[neighbor_id] = [element]
        else:
            self.neighbor[neighbor_id] += [element]

    def addInternalMass(self, wall: MoosasWall):
        self.internalMass.append(wall)

    def getAllFaces(self, to_dict=False) -> list[MoosasElement] | dict:
        """get all faces in the space.

        Args:
            to_dict (bool, optional): whether to return a dictionary or a list. Defaults to False.

        Returns:
            list[MoosasElement]: all faces in the space.
            dict:
            {
                MoosasFloor: list[MoosasFloor],
                MoosasCeiling:list[MoosasCeiling],
                MoosasWall:list[MoosasWall],
                MoosasSkylight:list[MoosasSkylight],
                MoosasGlazing:list[MoosasGlazing],
                Shading:list[MoosasElement],
                InternalMass:list[MoosasElement],
            }

        """

        faces = {}
        faces['MoosasFloor']: list[MoosasFace] = [f for f in self.floor.face] if self.floor else []
        faces['MoosasCeiling']: list[MoosasFace] = [f for f in self.ceiling.face] if self.ceiling else []
        faces['MoosasWall']: list[MoosasWall] = [w for w in self.edge.wall]
        for void in self.void:
            faces['MoosasWall'] += void.edge.wall

        faces['MoosasSkylight']: list[MoosasSkylight] = []
        faces['MoosasGlazing']: list[MoosasGlazing] = []
        faces['Shading']: list[MoosasElement] = []

        for moface in faces['MoosasFloor'] + faces['MoosasCeiling']:
            faces['MoosasSkylight'] += moface.glazingElement
        for moface in faces['MoosasWall']:
            faces['MoosasGlazing'] += moface.glazingElement
        for moface in faces['MoosasGlazing']:
            faces['Shading'] += moface.shading

        for moface in faces['MoosasSkylight']:
            faces['Shading'] += moface.shading

        faces['InternalMass'] = self.internalMass

        if to_dict:
            return faces
        else:
            return [item for subList in list(faces.values()) for item in subList]

    def open_edges(self):
        edges = {}
        for moGeometry in self.getAllFaces(False):
            for edge_str in moGeometry.getEdgeStr():
                if edge_str in edges.keys():
                    edges[edge_str] = None
                else:
                    edges[edge_str] = moGeometry
        openEdges = {key: edges[key] for key in edges.keys() if edges[key] is not None}
        return openEdges

    def to_string(self, model: MoosasContainer):
        """lagacy method to print the space info"""
        string_out = 'Space' + ' ' + self.id + '\n'
        string_out += '-Area' + ' ' + str((self.area) / INCH_METER_MULTIPLIER_SQR) + '\n'
        string_out += '-Height' + ' ' + str((self.height) / INCH_METER_MULTIPLIER) + '\n'
        string_out += '-Boundary\n'
        corrdiantes = pygeos.get_coordinates(pygeos.force_3d(self.edge.force_2d(), z=self.floor.level), include_z=True)
        for poi in corrdiantes:
            string_out += str(poi[0] / INCH_METER_MULTIPLIER) + ' ' \
                          + str(poi[1] / INCH_METER_MULTIPLIER) + ' ' \
                          + str(poi[2] / INCH_METER_MULTIPLIER) + '\n'

        string_out += '-Floor' + ' '

        for Moosasface in self.floor.face:
            string_out += str(Moosasface.faceId) + ' '
        string_out += '\n--Area' + ' ' + str((self.area) / INCH_METER_MULTIPLIER_SQR) + '\n'
        floor_normal = pygeos.get_coordinates(model.geoNormal[model.geoId.index(self.floor.face[0].faceId)],
                                              include_z=True).flatten()
        string_out += '--Normal ' + str(floor_normal[0]) + ' ' + str(floor_normal[1]) + ' ' + str(
            floor_normal[2]) + '\n'
        string_out += '--Height' + ' ' + str((self.floor.level) / INCH_METER_MULTIPLIER) + '\n'

        string_out += '-Ceiling' + ' '

        for Moosasface in self.ceiling.face:
            string_out += str(Moosasface.faceId) + ' '
        string_out += '\n--Area' + ' ' + str((self.area) / INCH_METER_MULTIPLIER_SQR) + '\n'
        floor_normal = pygeos.get_coordinates(model.geoNormal[model.geoId.index(self.ceiling.face[0].faceId)],
                                              include_z=True).flatten()
        string_out += '--Normal ' + str(floor_normal[0]) + ' ' + str(floor_normal[1]) + ' ' + str(
            floor_normal[2]) + '\n'
        string_out += '--Height' + ' ' + str((self.ceiling.level) / INCH_METER_MULTIPLIER) + '\n'

        for wall, factor in zip(self.edge.wall, self.edge.FactorOfWall):
            factor = factor.array
            string_out += '-Wall' + ' '
            if type(wall.faceId) == np.ndarray:
                for indd in wall.faceId:
                    string_out += str(indd) + ' '
            else:
                string_out += str(wall.faceId) + ' '
            string_out += '\n--Area' + ' ' + str((wall.area) / INCH_METER_MULTIPLIER_SQR) + '\n'
            string_out += '--Internal' + ' ' + str(wall.isOuter) + '\n'
            string_out += '--Height' + ' ' + str((wall.level) / INCH_METER_MULTIPLIER) + '\n'
            string_out += '--Normal' + ' ' + str(factor[0]) + ' ' + str(factor[1]) + ' ' + str(0) + '\n'
            string_out += '--Glazing' + ' '
            if type(wall.glazingId) == np.ndarray:
                for indd in wall.glazingId:
                    string_out += str(indd) + ' '
            else:
                string_out += str(wall.glazingId) + ' '
            string_out += '\n--Edge\n'
            twins = pygeos.get_coordinates(pygeos.force_3d(wall.force_2d()), include_z=True)
            string_out += str(twins[0][0]) + ' ' + str(twins[0][1]) + ' ' + str(twins[0][2]) + '\n'
            string_out += str(twins[1][0]) + ' ' + str(twins[1][1]) + ' ' + str(twins[1][2]) + '\n'

        string_out += 'End\n'
        return string_out

    def __repr__(self):
        return self.id

    def to_xml(self, model: MoosasContainer = None, xml_tag="space", writeGeometry=False):
        if not model:
            model = self.parent
        root = ET.Element(xml_tag)
        ET.SubElement(root, "id").text = self.id
        ET.SubElement(root, "area").text = str(self.area)
        if self.ceiling and self.floor:
            height = (self.edge.toplevel - self.edge.level) / INCH_METER_MULTIPLIER
        else:
            height = None
        ET.SubElement(root, "height").text = str(height)
        ET.SubElement(root, "is_void").text = str(self.is_void())
        ET.SubElement(root, "void").text = " ".join([str(v) for v in self.void])
        bound = ET.SubElement(root, "boundary")

        corrdiantes = pygeos.get_coordinates(
            pygeos.force_3d(self.edge.force_2d(), z=self.edge.elevation), include_z=True)
        for poi in corrdiantes:
            ET.SubElement(bound, "pt").text = ' '.join([str(p / INCH_METER_MULTIPLIER) for p in poi])
        settingXml = ET.SubElement(root, "setting")
        for key in self.settings.keys():
            ET.SubElement(settingXml, key).text = str(self.settings[key])

        topology = ET.SubElement(root, "topology")
        if self.floor:
            topology.append(self.floor.to_xml(model, writeGeometry=writeGeometry))
        if self.ceiling:
            topology.append(self.ceiling.to_xml(model, 'ceiling', writeGeometry=writeGeometry))
        topology.append(self.edge.to_xml(model, writeGeometry=writeGeometry))

        for _nei in self.neighbor:
            _neiElement = ET.SubElement(root, "neighbor")
            ET.SubElement(_neiElement, "Uid").text = str([w.Uid for w in self.neighbor[_nei]])
            ET.SubElement(_neiElement, "id").text = str(_nei)

        for _intWall in self.internalMass:
            root.append(_intWall.to_xml(model, 'internalMass', writeGeometry=writeGeometry))

        return root


class MoosasContainer(object):
    """Define all the global variables needed for Moosas+.

    This class does not have slots for the sake of flexible attributes.

    Attributes:
        geoId (str): Geometries' identification.
        geometryList (List): List of all geometries.
        faceList (List): List of MoosasFace objects.
        wallList (List): List of MoosasWall objects.
        skylightList (List): List of MoosasSkylight objects.
        glazingList (List): List of MoosasGlazing objects.
        levelList (List): List of all levels in the model.
        boundaryList (List): List of recognized boundaries.
        floorList (List): List of floors as MoosasFloor objects.
        edgeList (List): List of MoosasEdge objects.
        ceilingList (List): List of ceilings as MoosasFloor objects.
        spaceList (List): List of valid spaces as MoosasSpace objects.
        voidList (List): List of void spaces as MoosasSpace objects.
        weather (MoosasWeather): MoosasWeather in this model, default is None.
        builtData (Object): Data used to construct space manually.

    Properties:
        spaceIdDict (dict): A dictionary recording spaceId: MoosasSpace.

    Methods:
        fromDict(cls, spaceDict: dict) -> MoosasSpace: Create MoosasSpace from a dictionary.
        update(self) -> None: update self.builtData, which is used to record current elements and glazing when creating space manually.
        getAllFaces(self) -> List: Get all elements in the model.
        includeGeo(self, geo: pygeos.Geometry, normal: pygeos.Geometry | Vector | np.ndarray = None, cat: int = 0,
                   holes=None) -> str: Include a pygeos.Geometry to the library.
        findFace(self, faceId) -> list[MoosasGeometry]: Find a geometry by its geoId.
    """

    def __init__(self):
        """initialize the MoosasModel with default list, and apply type to these list"""
        self.geoId = []
        self.geometryList: list[MoosasGeometry] = []
        self.newIndex = 0

        # horizontalVerticalPlaneSet
        self.faceList: list[MoosasFace] = []
        self.wallList: list[MoosasWall] = []

        # Identify the result set
        self.levelList: list[float] = []
        self.boundaryList = []

        # envelope floor space set
        self.floorList: list[MoosasFloor] = []
        self.ceilingList: list[MoosasFloor] = []
        self.glazingList: list[MoosasGlazing] = []
        self.skylightList: list[MoosasSkylight] = []
        self.edgeList: list[MoosasEdge] = []
        self.spaceList: list[MoosasSpace] = []
        self.voidList: list[MoosasSpace] = []

        # object used to construct a space
        self.builtData = object()

    @property
    def spaceIdDict(self) -> dict:
        """space id dictionary for all spaces in self.spaceList

        Returns:
            dict: {spaceId:MoosasSpace}
        """
        return {space.id: space for space in self.spaceList+self.voidList}

    def fromDict(self, spaceDict: dict) -> MoosasSpace:
        """construct a space from a dictionary
        the space will be added to self.spaceList automatically,
        and the space topology will be automatically recalculate.
        for more information please refer to MoosasSpace.fromDict()

        Args:
            spaceDict (dict): Dictionary to construct space from.

        Returns:
            MoosasSpace: created MoosasSpace object.
        """
        if not hasattr(self.builtData, 'elements') or not hasattr(self.builtData, 'glazing'):
            self.update()
        space = MoosasSpace.fromDict(spaceDict, self)
        for void in self.voidList:
            if pygeos.contains(space.force_2d(), void.force_2d()):
                space.voidList.append(void)
        self.spaceList.append(space)
        return space

    def update(self) -> None:
        """update self.builtData, which is used to record current elements and glazing when creating space manually.
        builtData.element is a dictionary: {MoosasElement.faceId:MoosasElement}
        builtData.glazing is a dictionary: {MoosasGlazing.faceId:MoosasElement}
        """
        if not hasattr(self.builtData, 'elements') or not hasattr(self.builtData, 'glazing'):
            self.builtData.element = {}
            self.builtData.glazing = {}
        for gls in self.glazingList:
            for glsId in gls.glazingId:
                self.builtData.glazing[glsId] = gls
        for gls in self.skylightList:
            for glsId in gls.glazingId:
                self.builtData.glazing[glsId] = gls
        for element in self.getAllFaces():
            for eleId in mixItemListToList(element.faceId):
                self.builtData.element[eleId] = element

    def getAllFaces(self, dumpUseless=False) -> list[MoosasElement] | dict:
        """get all MoosasElement in the model as a list
        the elements in the list will not change their type hence you can test which element it is by isinstance()

        Returns:
            list[MoosasElement]: all MoosasElement in the model
        """
        if not dumpUseless:
            faces = []
            for elementList in [self.wallList, self.faceList, self.glazingList, self.skylightList]:
                faces = np.append(faces, elementList)
            return list(faces)
        else:
            mElements = {'MoosasFace': set(), 'MoosasSkylight': set(), 'MoosasWall': set(), 'MoosasGlazing': set()}
            for space in self.spaceList + self.voidList:
                elementDict = space.getAllFaces(to_dict=True)

                mElements['MoosasFace'] = mElements['MoosasFace'] | set(
                    elementDict['MoosasFloor'] + elementDict['MoosasCeiling'])
                mElements['MoosasWall'] = mElements['MoosasWall'] | set(
                    elementDict['MoosasWall'] + elementDict['InternalMass'])
                mElements['MoosasSkylight'] = mElements['MoosasSkylight'] | set(elementDict['MoosasSkylight'])
                mElements['MoosasGlazing'] = mElements['MoosasGlazing'] | set(elementDict['MoosasGlazing'])
            return mElements

    def includeGeo(self, geo: pygeos.Geometry, normal: pygeos.Geometry | Vector | np.ndarray = None, cat: int = 0,
                   holes=None) -> str:
        """Include a geometry into the geometry library.

        Args:
            geo (pygeos.Geometry): The polygon to include.
            normal (pygeos.Geometry, optional): The normal vector of the polygon. Defaults to None.
            cat (int, optional): Category of the geometry (opaque == 0, transparent == 1, aperture == 2). Defaults to 0.
            holes (List[pygeos.Geometry], optional): The inner holes of the geometry. Defaults to None.

        Returns:
            str: GeoId of the geometry, can be used to construct faces.
        """
        if holes is None:
            holes = []
        if normal is None:
            normal = faceNormal(geo)
        rings = pygeos.get_rings(geo)
        if len(rings) > 1:
            geo = pygeos.polygons(rings[0])
            holes += [pygeos.polygons(r) for r in rings[1:]]
        faceId = f"n{self.newIndex}"
        self.newIndex += 1

        self.geometryList.append(MoosasGeometry(geo, faceId, normal, cat, holes))
        self.geoId = list(np.append(self.geoId, [faceId]))
        return self.geoId[-1]

    def removeGeo(self, geo: MoosasGeometry | pygeos.Geometry | str):
        if isinstance(geo, pygeos.Geometry):
            for geoItems in self.geometryList:
                if geoItems.face == geo:
                    geo = geoItems
        if isinstance(geo, str):
            geo = self.geometryList[self.geoId.index(geo)]
        if isinstance(geo, MoosasGeometry):
            self.geometryList.remove(geo)
            self.geoId.remove(geo.faceId)

    def findFace(self, faceId: str | list[str]) -> list[MoosasGeometry]:
        """find a geometry in the library
        it will test the validation of the identification automatically, and skip invalid geometry

        Args:
            faceId (str|list[str]): The id of the face in the geo file or library

        Returns:
            list[MoosasGeometry]: a list of MoosasGeometry object of the face
        """
        if isinstance(faceId, str):
            faceId = [faceId]
        _faceId = []
        for idd in faceId:
            try:
                _faceId.append(self.geoId.index(idd))
            except:
                print(f"the geo: {idd} not in the geometry library.")
        return [self.geometryList[idd] for idd in _faceId]
