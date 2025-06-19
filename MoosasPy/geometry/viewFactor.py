from __future__ import annotations
from .geos import Ray, Vector, rayFaceIntersect, Projection
from ..utils import np, pygeos
from ..utils.constant import geom
from .element import MoosasElement, MoosasWall
from .contour import TopoEdge, TopoNetwork
from .cleanse import _groupRelateArray


class ViewFactorFace(Ray):
    __slots__ = ("element", "objects")

    def __init__(self, element: MoosasElement, normal=None, value=None):
        self.element = element
        normal = normal if normal is not None else element.normal
        normal = Vector(normal).unit()
        origin = np.mean(pygeos.get_coordinates(element.face, include_z=True), axis=0)
        self.objects: set[ViewFactorFace] = set()
        super().__init__(origin, normal, value)

    @classmethod
    def fromElement(cls, element: MoosasElement):
        normal = Vector(element.normal)
        vFF1 = cls(element, normal, element.Uid + "+")
        vFF2 = cls(element, -normal, element.Uid + "-")
        return (vFF1, vFF2)

    def branchTest(self, faces: list[ViewFactorFace], number=100):
        factor = []
        proj = Projection.fromRay(self)
        for alt in [-.1,-.05,0,.05,.1]:
            for j in range(number):
                vec = Vector.azimuthToVector(5+float(j / int(number-1)) * 360) + Vector(0, 0, alt)
                if Vector.dot(vec, self.direction) >= 0:
                    factor.append(Ray(self.origin, vec.unit()))
        # testFaces = [proj.toUV(f.element.representation()) for f in faces]
        validFaces, representation = [], []
        for f in faces:
            if Vector(f.origin - self.origin).length() > geom.POINT_PRECISION:
                if Vector.dot(self.direction, Vector(f.origin - self.origin).unit()) > geom.POINT_PRECISION:
                    validFaces.append(f)
                    representation.append(f.element.representation())
        # validFaces = faces
        # representation = [f.element.representation() for f in faces]
        for r in factor:
            dist = []
            match = False
            for f, testFace in zip(validFaces, representation):
                if Vector.dot(f.direction, r.direction) < -geom.POINT_PRECISION:
                    pt = rayFaceIntersect(r, testFace, normal=f.direction)
                    if pt:
                        dists = (r.origin - Vector(pt)).length()
                        if dists > geom.POINT_PRECISION:
                            dist.append(dists)
                            match = True
                    else:
                        dist.append(99999)
                else:
                    dist.append(99999)
            if match:
                self.objects.add(validFaces[np.argmin(dist)])



def viewFactorTopology(model, elementList,vfNumber=64):
    vfFaces: list[ViewFactorFace] = [vfw for w in elementList for vfw in ViewFactorFace.fromElement(w)]
    _nameDict = {vfw.value: vfw for vfw in vfFaces}
    for i, vfw in enumerate(vfFaces):
        vfw.branchTest(np.delete(vfFaces, i), number=vfNumber)
        print(f'\rTOPOLOGY: view topology calculation {i}/{len(vfFaces)}', end='')
    """split the vfFaces into groups"""

    vfGroup = [[vfw] + list(vfw.objects) for vfw in vfFaces]
    _names = [[vfw.value for vfw in vfFaces] for vfFaces in vfGroup]
    _names = _groupRelateArray(_names)
    vfGroup = [[_nameDict[vfName] for vfName in vfG] for vfG in _names]

    bounds = []
    for faceSet in vfGroup:
        wallElements = [w.element for w in faceSet if isinstance(w.element, MoosasWall)]
        wallElements = [w for w in wallElements if
                        w.force_2d() is not None and pygeos.get_dimensions(w.force_2d()) != 0]
        walls = [TopoEdge(list(model.wallList).index(w), w) for w in wallElements]
        outBound = TopoNetwork(edges=walls).outerBoundary()
        if len(outBound) > 0:
            for b in outBound:
                walls = list(set(walls).difference(b.edgeLoop))
            for wi, w in enumerate(walls):
                cen = pygeos.force_2d(pygeos.centroid(model.wallList[w.modelId].representation()))
                target, distance = wallElements[0], 10000
                for b in outBound:
                    for edge in b.edgeLoop:
                        _dist = pygeos.distance(cen, model.wallList[edge.modelId].force_2d())
                        if _dist < distance:
                            target, distance = model.wallList[edge.modelId], _dist
                target.shading.append(model.wallList[w.modelId])
                print(f'\rTOPOLOGY: attach shading {wi}/{len(walls)}', end='')
            bounds += outBound

    return bounds
