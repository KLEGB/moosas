"""
    This module defines the main function for geometric processing. This module is used as a foundation for the models,
    transforming and encoding module. It has no documented public API and should not be used directly.
    This module has been translated from Chinese into English by Microsoft translation. Some expressions may be
    inaccurate or unprofessional.
"""
from __future__ import annotations

from ..utils.constant import geom
from ..utils import pygeos, np, GeometryError, Iterable


class Vector(object):
    """
        The geometric operations of points and vectors and related 2D and 3D are defined, and the data formats of pygeos
        and numpy are fused with high fault tolerance x,y,z: vector three-dimensional components style: The format of the
        data used to create the vector, which will be returned according to the format
    """
    __slots__ = ['x', 'y', 'z', 'style']

    ANGLE_TOLERANCE = 0.01

    def __init__(self, *vec: Vector | Iterable | pygeos.Geometry | float | int):
        """
            accepts input in 5 formats: Vector, pygeos.Geometry, np.ndarry, list, numbers
            default: ndarry
        """
        if len(vec) == 1:
            vec = vec[0]
        if isinstance(vec, Vector):
            vec = vec.array
            self.style = np.ndarray
        if isinstance(vec, pygeos.Geometry):
            vec = pygeos.force_3d(vec, z=0)
            vec = pygeos.get_coordinates(vec, include_z=True)
            if len(vec) > 1:
                vec = vec[-1] - vec[0]
            else:
                vec = vec[0]
            self.style = pygeos.Geometry
        else:
            if not (isinstance(vec, Iterable)):
                raise Exception(f'Expect Iterable, got{type(vec)}')
            self.style = np.ndarray
        if len(vec) <= 2:
            vec = np.append(vec, 0)
        vec = np.nan_to_num(vec, nan=0)
        self.x = vec[0]
        self.y = vec[1]
        self.z = vec[2]

    @property
    def dump(self):
        if self.style == pygeos.Geometry:
            return self.geometry
        else:
            return self.array

    @property
    def geometry(self) -> pygeos.Geometry:
        """get geometry representation of the vector"""
        return pygeos.points([self.x, self.y, self.z])

    @property
    def array(self) -> np.ndarray:
        """get array representation of the vector"""
        return np.array([self.x, self.y, self.z])

    @property
    def string(self):
        """
            The vector is expressed as a string describing the direction, and the forward and reverse vectors are
            expressed in the same way, which is used to quickly determine whether the normal vectors of the surface are
            parallel.
            e.g.
            vec = np.array([0,0,1])
            Vector(vec).string == Vector(-vec).string
        """
        vec = Vector(self).uniform.array

        for i in range(3):
            if abs(vec[i]) <geom.POINT_PRECISION:
                vec[i] = '0.00'
            else:
                vec[i] = round(vec[i], 2)
        return '_'.join(vec.astype(str))

    @property
    def uniform(self):
        """get an uniform vector,
        in which Vector(vec).uniform == Vector(-vec).uniform == Vector(-vec * 10).uniform
        """
        vec = Vector(self).unit().array
        if vec[0] < 0:
            return Vector(np.array([-vec[0], -vec[1], -vec[2]]))
        else:
            if vec[0] == 0 and vec[1] < 0:
                return Vector(np.array([-vec[0], -vec[1], -vec[2]]))
            else:
                if vec[0] == 0 and vec[1] == 0 and vec[2] < 0:
                    return Vector(np.array([-vec[0], -vec[1], -vec[2]]))

        return Vector(vec)

    @classmethod
    def azimuthToVector(cls, azimuth):
        x, y = 1, 0
        if azimuth < 0:
            azimuth = azimuth + 360
        if azimuth == 270:
            x, y = -1, 0
        elif azimuth == 0 or azimuth == 360:
            x, y = 0, 1
        elif azimuth == 180:
            x, y = 0, -1
        else:
            y = np.tan(np.radians(azimuth)) * x
            if azimuth > 180:
                x, y = -x, -y

        return cls([x, y, 0]).unit()

    def altitude(self, to_degree=False):
        """get the angle to Vector([0,0,1])"""
        tan = np.power(self.z, 2) / (np.power(self.x, 2) + np.power(self.y, 2))
        radius = np.arctan(np.sqrt(tan))
        if to_degree:
            radius *= 180 / np.pi
        return radius

    def azimuth(self, to_degree=False):
        """get the angle to Vector(0,1,0) in clockwise"""
        if self.x == 0.0:
            return 0.0 if self.y >= 0 else np.pi
        radius = np.arctan(self.y / self.x)

        if self.x <= 0.0:
            radius = np.pi + radius
        if to_degree:
            radius *= 180 / np.pi
        return radius

    def length(self, power=False):
        """get length of the vector, Set power to True to accelerate the calculation
        """
        if power:
            return np.sum([i * i for i in self.array])
        else:
            return np.sqrt(np.sum([i * i for i in self.array]))

    def unit(self):
        """
            Returns a normalized vector. The original vector will be modified and returned to itself
            If you don't want to change the vector, you can do like this:
            unitVec = Vector(vec).unit()
        """
        length = self.length()
        if length == 0: raise GeometryError(self, 'zero vector')
        self.x /= length
        self.y /= length
        self.z /= length
        return self

    def quickAngle(self):
        """
            a quick calculation for angle to Vector(1,0,0)
            if the self.y>=0: get Vector.dot([1,0],vec) in [-1,1]
            if the self.y<0: get -vector.dot([1,0],vec)-2 in [-3,-1]
            the return result is in [-3,1] and is positive correlation to the angle.
            for example:
            [1,0]==1,[0,1]==0,[-1,0]==-1
            [.99,-.01]==-3,[0,-1]==-2,[-.99,-.01]==-1
        """
        if self.length() == 0:
            print('zero length vector')
            return None
        vec = self / self.length()
        dot = Vector.dot(np.array([1, 0]), vec)
        if vec[1] < 0:
            dot = -dot - 2
        return dot

    @staticmethod
    def dot(vec1, vec2):
        """call np.dot"""
        vec1 = Vector(vec1).array
        vec2 = Vector(vec2).array
        return np.sum([vec1[i] * vec2[i] for i in range(len(vec1))])

    @staticmethod
    def cross(vec1, vec2, style=np.ndarray):
        """call np.cross"""
        vec1 = Vector(vec1).array
        vec2 = Vector(vec2).array
        if style == np.ndarray:
            return np.cross(vec1, vec2)
        elif style == pygeos.Geometry:
            return pygeos.points(np.cross(vec1, vec2))
        else:
            return Vector(np.cross(vec1, vec2))

    @staticmethod
    def parallel(vec1, vec2):
        """test if two vector is parallel, based on their dot value"""
        vec1 = Vector(vec1)
        vec2 = Vector(vec2)
        if vec1.length() == 0 or vec2.length() == 0:
            return True
        dot = pow(vec1 * vec2, 2) / vec2.length(True) / vec1.length(True)
        if 1.0 + Vector.ANGLE_TOLERANCE > dot > 1.0 - Vector.ANGLE_TOLERANCE:
            return True
        if -1.0 + Vector.ANGLE_TOLERANCE > dot > -1.0 - Vector.ANGLE_TOLERANCE:
            return True
        return False

    @staticmethod
    def equal(vec1, vec2):
        vec1 = Vector(vec1)
        vec2 = Vector(vec2)
        if Vector(vec1.array - vec2.array).length(True) < geom.POINT_PRECISION:
            return True
        return False

    def __add__(self, other):
        return Vector(self.array + other.array)

    def __sub__(self, other):
        return Vector(self.array - other.array)

    def __abs__(self):
        return Vector(np.abs(self.array))

    def __neg__(self):
        return self.__mul__(-1)

    def __getitem__(self, item):
        return self.array.__getitem__(item)

    def __mul__(self, other):
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y + self.z * other.z
        else:
            return Vector(other * self.array)

    def __truediv__(self, other):
        return Vector(self.array / other)

    def __xor__(self, other):
        if isinstance(other, Vector):
            return Vector(np.cross(self.array, other.array))
        else:
            return Vector(np.pow(self.array, other))

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.x, self.y, self.z)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return Vector.equal(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Vector({'%.2f' % self.x},{'%.2f' % self.y},{'%.2f' % self.z})"


class Ray(Vector):
    """
    Defines a ray with a direction and can also be used to express an infinite plane
    origin: The origin of the ray, of the Vector type
    direction: The direction of the ray, Vector type
    value: Used to store related data, which can be in any data format
    """
    __slots__ = ['origin', 'direction', 'value']

    def __init__(self, origin, direction, value=0):
        if not isinstance(origin, Vector):
            origin = Vector(origin)
        if not isinstance(direction, Vector):
            direction = Vector(direction)

        super(Ray, self).__init__(direction.unit())
        self.origin: Vector = origin
        self.value = value
        self.direction: Vector = direction.unit()

    def reverse(self):
        return Ray(self.origin, Vector(-self.direction.array), self.value)

    def mirror(self, mir):
        """
        Compute a mirror image of itself based on the normal vector, ignoring the heads and tails of the input normal
        vector. The obtained mirror rays are equivalent to the reflection of their own relative infinite planes
        """
        if Vector.dot(self.direction, mir.direction) <= 0:
            mir = mir.reverse()
        transfrom = 2 * (self.direction.array - Vector.dot(self.direction, mir.direction) * mir.direction.array)
        return Ray(self.origin, Vector(self.direction.array + transfrom), self.value).reverse()

    def dump(self):
        """
        get the standard ray export to MoosasRad.exe
        """
        rayStr = list(self.origin.array) + list(self.direction.array)
        rayStr = [str(ray) for ray in rayStr]
        return ','.join(rayStr)

    def __repr__(self):
        return f"Ray( ori {self.origin.__repr__()} dir {self.direction.__repr__()} )"


class Projection(Ray):
    """
    Establish a three-dimensional coordinate system based on the infinite plane input and realize the conversion with
    the world coordinate system Since pygeos does not provide 3D processing, it is necessary to process 3D collection
    processing on UVs after projection through the coordinate system
    """
    __slots__ = ['axisX']

    def __init__(self, origin, unitZ, unitX=None):
        origin = Vector(origin)
        unitZ = Vector(unitZ).unit().array
        super(Projection, self).__init__(origin, unitZ)
        if unitX is not None:
            self.axisX = Vector(unitX).unit().array
        else:
            if not Vector.parallel(self.axisZ, np.array([0, 0, 1])):
                self.axisX = np.cross(np.array([0, 0, 1]), self.axisZ)
            else:
                self.axisX = np.array([1, 0, 0])

    @classmethod
    def fromRay(cls, plane: Ray):
        return cls(plane.origin, plane.direction)

    @classmethod
    def fromPolygon(cls, polygon: pygeos.Geometry):
        unitz = faceNormal(polygon)
        if Vector.parallel(unitz, np.array([0, 0, 1])):
            return cls.findOrthogonalBasis([polygon])
        else:
            center = np.mean(pygeos.get_coordinates(polygon, include_z=True), axis=0)
            sectionVector = pygeos.get_coordinates(section(polygon, center[2], False), include_z=True)
            sectionVector = sectionVector[1] - sectionVector[0]
            return cls(center, unitz, unitX=sectionVector)

    @classmethod
    def findOrthogonalBasis(cls, polygons):
        """
        Find a twin of orthogonal axis from given polygons by counting the most popular vectors in the polygons' edges
        """
        if isinstance(polygons, pygeos.Geometry):
            polygons = [polygons]
        # Organize the axis of the boundary, and find the most oriented direction to establish the coordinate system
        projAxisCount = {}  # statistics of the axis
        edgeVectors = []  # the orientation of all edges
        for boundary in polygons:
            coordinates = pygeos.get_coordinates(pygeos.force_3d(boundary, z=0), include_z=True)
            coordinates = np.nan_to_num(coordinates, nan=0)
            edgeVectors += [coordinates[i] - coordinates[i + 1] for i in range(len(coordinates) - 1)]
            for vec in edgeVectors:
                if Vector(vec).length() > geom.POINT_PRECISION:
                    vecStr = Vector(vec).unit().string
                    if vecStr not in projAxisCount.keys():
                        projAxisCount[vecStr] = 1
                    else:
                        projAxisCount[vecStr] += 1

        # Sort the axis to find the one facing the most, as unitX of the projection. (unitZ == [0,0,1])
        sortlist = [[vecStr, projAxisCount[vecStr]] for vecStr in projAxisCount.keys()]
        sortlist.sort(key=lambda x: (x[1]))
        unitX = sortlist[-1][0]
        unitX = [eval(dim) for dim in unitX.split('_')]
        center = np.mean(pygeos.get_coordinates(polygons, include_z=True), axis=0)
        proj = cls(center, [0, 0, 1], unitX)  # The orthogonal coordinate system applied when orthogonalization
        return proj

    @property
    def rotateMatrix(self):
        return np.asmatrix(np.array([self.axisX, self.axisY, self.axisZ]).T)

    @property
    def axisZ(self):
        return self.array

    @property
    def axisY(self):
        return np.cross(self.axisX, self.axisZ)

    def toUV(self, worldGeometry: pygeos.Geometry):
        """
        Converts geometry from world coordinates to a specified plane, obtaining UV coordinates on that plane
        """
        if pygeos.get_dimensions(worldGeometry) == -1:
            raise Exception(f'invalid geometry: {worldGeometry}')
        if pygeos.get_dimensions(worldGeometry) == 2:
            rings = [[self.toUV(ring) for ring in pygeos.get_rings(part)] for part in pygeos.get_parts(worldGeometry)]
            parts = []
            for ring in rings:
                if len(ring) > 1:
                    try:
                        parts.append(pygeos.polygons(rings[0], rings[1:]))
                    except Exception as e:
                        # failed to create hole
                        parts.append(pygeos.polygons(rings[0]))
                else:
                    parts.append(pygeos.polygons(rings[0]))
            return pygeos.union_all(parts)
        worldGeometry = pygeos.force_3d(worldGeometry, z=0)
        coors = pygeos.get_coordinates(worldGeometry, include_z=True)
        coors = np.nan_to_num(coors, nan=0)
        coor_new = [coor - self.origin.array for coor in coors]
        if not (Vector.parallel(self.axisZ, np.array([0, 0, 1])) and Vector.parallel(self.axisX, np.array([1, 0, 0]))):
            coor_new = [np.asmatrix(coor) * self.rotateMatrix for coor in coor_new]
        coor_new = np.array([np.array(coor).flatten() for coor in coor_new])
        if pygeos.get_dimensions(worldGeometry) == 0:
            return pygeos.points(coor_new[0])
        if pygeos.get_dimensions(worldGeometry) == 1:
            if pygeos.points(coor_new[0]) == pygeos.points(coor_new[-1]):
                return pygeos.linearrings(coor_new)
            else:
                return pygeos.linestrings(coor_new)
        # if pygeos.get_dimensions(worldGeometry) == 2:
        #     return pygeos.polygons(coor_new)

    def toWorld(self, UVGeometry: pygeos.Geometry):
        """
        Converts the geometry represented by UV coordinates to the world coordinate system
        """
        if pygeos.get_dimensions(UVGeometry) == -1:
            raise Exception(f'invalid geometry: {UVGeometry}')
        if pygeos.get_dimensions(UVGeometry) == 2:
            rings = [self.toWorld(ring) for ring in pygeos.get_rings(UVGeometry)]
            if len(rings) > 1:
                return pygeos.polygons(rings[0], rings[1:])
            else:
                return pygeos.polygons(pygeos.get_coordinates(rings[0], include_z=True))
        UVGeometry = pygeos.force_3d(UVGeometry, z=0)
        coors = pygeos.get_coordinates(UVGeometry, include_z=True)
        if not (Vector.parallel(self.axisZ, np.array([0, 0, 1])) and Vector.parallel(self.axisX, np.array([1, 0, 0]))):
            coor_new = [np.asmatrix(coor) * self.rotateMatrix.I for coor in coors]
        else:
            coor_new = coors
        coor_new = np.array([coor + self.origin.array for coor in coor_new])

        coor_new = np.array([np.array(coor).flatten() for coor in coor_new])

        if pygeos.get_dimensions(UVGeometry) == 0:
            return pygeos.points(coor_new[0])
        if pygeos.get_dimensions(UVGeometry) == 1:
            return pygeos.linestrings(coor_new)


class Transformation2d:
    """
    Realize two-dimensional transformation, including movement and rotation, and define the rotation angle in clockwise
    """
    __slots__ = ['moveVec', 'rotateRadius', 'rotateOrigin']

    def __init__(self, moveVec=np.array([0, 0]), rotateRadius: float = 0, rotateOrigin=None):
        if isinstance(moveVec, pygeos.Geometry):
            moveVec = pygeos.get_coordinates(moveVec)
        if isinstance(rotateOrigin, pygeos.Geometry):
            rotateOrigin = pygeos.get_coordinates(rotateOrigin)
        self.rotateRadius = rotateRadius
        self.moveVec = np.array(moveVec)
        self.rotateOrigin = None
        if rotateOrigin is not None:
            self.rotateOrigin = np.array(rotateOrigin)

    @property
    def rotateMatrix(self):
        rotateMatrix = [np.cos(self.rotateRadius), -np.sin(self.rotateRadius)], [np.sin(self.rotateRadius),
                                                                                 np.cos(self.rotateRadius)]
        rotateMatrix = np.asmatrix(np.array(rotateMatrix).T).I
        return rotateMatrix

    @classmethod
    def opposite(cls, transformation):
        """
            get the opposite transformation.
        """
        if transformation.rotateOrigin is not None:
            rotateOrigin = transformation.rotateOrigin - transformation.moveVec
            return cls(- transformation.moveVec, - transformation.rotateAngle, rotateOrigin)
        else:
            return cls(- transformation.moveVec, - transformation.rotateAngle)

    def transfrom(self, geo: pygeos.Geometry):
        """
        Move first then rotate next. If the rotate origin do not provide, it will rotate around its weight center:
        rotateOrigin = np.array([np.mean(coor) for coor in coordiantes.T])
        It can accept geometries in different dimensions
        """
        coordiantes = pygeos.get_coordinates(geo)
        coordiantes = np.array([coor + self.moveVec for coor in coordiantes])
        if self.rotateRadius != 0:
            rotateOrigin = self.rotateOrigin
            if rotateOrigin is None:
                rotateOrigin = np.array([np.mean(coor) for coor in coordiantes.T])
            coordinatesRelative = np.array([coor - rotateOrigin for coor in coordiantes])
            coordinatesRelative = np.array([np.asmatrix(coor) * self.rotateMatrix for coor in coordinatesRelative])
            coordiantes = np.array([np.array(coor + rotateOrigin).flatten() for coor in coordinatesRelative])
        if pygeos.get_dimensions(geo) == 0:
            return pygeos.points(coordiantes[0])
        if pygeos.get_dimensions(geo) == 1:
            return pygeos.linestrings(coordiantes)
        if pygeos.get_dimensions(geo) == 2:
            return pygeos.polygons(coordiantes)


def bBox(geo: pygeos.Geometry):
    """calculate the bounding box of the geometry with direction(calculating by OrthogonalBasis):
    two projection will be done:
    1. project the geo to 2d faces geoProj as projection 1
    2.1 in the projection 1, find the Orthogonal Basis of geoProj as projection 2
    2.2 reversed project.axisX the projection 2 to the world
    3. construct bBoxProjection using the projection2World.axisX and projection1.axisZ

    ----------------------------------------
    geo (pygeos.Geometry) : input 3d geometry

    returns: dict() include:
    Projection:(Projection) the OrthogonalBasis projection (3d)
    x-domain:(float,float) x min and max of the bBox
    y-domain:(float,float) y min and max of the bBox
    """
    proj1 = Projection.fromPolygon(geo)
    geoProj = proj1.toUV(geo)
    proj2 = Projection.findOrthogonalBasis(geoProj)
    minX, minY, maxX, maxY = pygeos.bounds(geoProj)
    worldAxisX = proj1.toWorld(Vector(proj2.axisX).geometry)
    worldAxisZ = proj1.axisZ
    origin = pygeos.centroid(geo)
    bBoxProjection = Projection(origin=origin, unitZ=worldAxisZ, unitX=worldAxisX)
    return {"Projection": bBoxProjection, "x-domain": (minX, maxX), "y-domain": (minY, maxY)}


def is_ccw(geo: pygeos.Geometry) -> bool:
    """
    Improved method for pygeos.is_ccw()
    accept both convex & non-convex but have lower efficiency
    """
    poilist = pygeos.get_coordinates(geo)
    veclist = [poilist[i] - poilist[i - 1] for i in range(1, len(poilist))]
    crosslist = [np.cross(veclist[i], veclist[i - 1]) for i in range(len(veclist))]
    ccw = np.sum([2 for vec in crosslist if vec > 0])
    ccw -= len(crosslist)
    return ccw < 0


def selfIntersect(geo: pygeos.Geometry) -> bool:
    """
    test whether a geometry is self-intersect
    """

    pointList = pygeos.points(pygeos.get_coordinates(geo, include_z=True))
    if (len(pointList) - len(set(pointList))) > 1:
        return True
    # if str(pygeos.is_valid_reason(geo)).startswith('Self-intersection'):
    #     return True
    return False


def overlapEdge(geo1: pygeos.Geometry, geo2: pygeos.Geometry) -> bool:
    """
    Determines whether two geometries containBy on at least 2 endpoints,
    which means that they share an exact same edge
    """
    try:
        geo1 = pygeos.get_coordinates(geo1, include_z=True)
        geo1 = set(pygeos.set_precision(
            pygeos.points(geo1),
            geom.POINT_PRECISION))
        geo2 = pygeos.get_coordinates(geo2, include_z=True)
        geo2 = set(pygeos.set_precision(
            pygeos.points(geo2),
            geom.POINT_PRECISION))
        if len(geo1.intersection(geo2)) >= 2:
            return True
        return False
    except:
        return False


def overlapArea(geo1: pygeos.Geometry, geo2: pygeos.Geometry) -> float:
    """
    retrun the containBy area of two geometries
    """

    if pygeos.is_empty(geo1) or pygeos.is_empty(geo1):
        return 0.0
    geo1 = makeValid(geo1)[0]
    geo2 = makeValid(geo2)[0]
    try:
        if pygeos.disjoint(geo1, geo2):
            return 0.0
        intersections = pygeos.intersection(geo1, geo2, grid_size=geom.POINT_PRECISION)
        if pygeos.get_dimensions(intersections) != 2:
            return 0.0
        area1 = pygeos.area(intersections)
    except:
        return 0.0
    return area1


def makeValid(geo: pygeos.Geometry, error='raise') -> pygeos.Geometry:
    """revise method of pygeos.make_valid()"""
    geos = pygeos.make_valid(geo)
    geos = [g for g in pygeos.get_parts(geos) if pygeos.get_dimensions(g) == 2]
    if len(geos) == 0:
        if error == 'raise':
            raise GeometryError(geo, "No valid geometries")
        else:
            print('******Warning: GeometryError: no valid geometries')
            return None
    for i, g in enumerate(geos):
        rings = pygeos.get_rings(g)
        if len(rings) > 1:
            innerRings = [pygeos.intersection(r, rings[0], grid_size=geom.POINT_PRECISION) for r in rings[1:]]
            innerRings = [r for r in innerRings if pygeos.get_dimensions(r) == 2]
            # print(rings[0],innerRings)
            if len(innerRings) > 0:
                geos[i] = pygeos.polygons(pygeos.get_coordinates(rings[0], include_z=True), holes=innerRings)
            else:
                geos[i] = pygeos.linestrings(pygeos.get_coordinates(rings[0], include_z=True))
    return geos


def contains(child: pygeos.Geometry, parent: pygeos.Geometry):
    # child = pygeos.set_precision(child, geom.POINT_PRECISION)
    child = pygeos.get_coordinates(child)
    # print(child)
    # parent = pygeos.set_precision(parent, geom.POINT_PRECISION)
    # geo1=pygeos.get_point(geo1,[0,1])
    try:
        for i in range(len(child)):
            # if pygeos.dwithin(geo1[0],geo2,2*geom.POINT_PRECISION) and pygeos.dwithin(geo1[1],geo2,2*geom.POINT_PRECISION):
            if not pygeos.dwithin(pygeos.points(child[i]), parent, 2 * geom.POINT_PRECISION):
                # if not pygeos.contains(parent,pygeos.points(child[i])):
                return False
    except:
        return False
    return True


def equals(geo1: pygeos.Geometry, geo2: pygeos.Geometry):
    geo1 = pygeos.get_point(geo1, range(pygeos.get_num_points(geo1)))
    geo2 = pygeos.get_point(geo2, range(pygeos.get_num_points(geo2)))
    if len(geo1) != len(geo2): return False
    valid = True
    for i in range(len(geo1)):
        if not pygeos.dwithin(geo1[i], geo2[i], 1.2 * geom.POINT_PRECISION):
            valid = False
    if not valid:
        valid = True
        geo2 = geo2[::-1]
        for i in range(len(geo1)):
            if not pygeos.dwithin(geo1[i], geo2[i], 1.2 * geom.POINT_PRECISION):
                valid = False
    if valid:
        return True
    else:
        return False


def faceNormal(face: pygeos.Geometry) -> Vector:
    """calculate the face normal by cross calculation.
    we only need to find two edges that do not parallel.
    in this case, this method is valid even if a linestring is provided
    """
    coordinates = pygeos.get_coordinates(face, include_z=True)
    edges = [coordinates[i] - coordinates[i + 1] for i in range(len(coordinates) - 1)]
    for i in range(1, len(edges)):
        if not Vector.parallel(edges[i], edges[0]):
            return Vector(np.cross(edges[i], edges[0])).unit()
    return Vector(face)


"""constructive methods"""


def difference(geoBase: pygeos.Geometry, geoDifference: pygeos.Geometry) -> list[pygeos.Geometry]:
    """
        3d difference for polygons
    """
    proj = Projection(
        origin=pygeos.points(pygeos.get_coordinates(geoBase)[0]),
        unitZ=faceNormal(geoBase)
    )
    geoBaseProj = pygeos.set_precision(proj.toUV(geoBase), geom.POINT_PRECISION)
    geoDifferenceProj = pygeos.set_precision(proj.toUV(geoDifference), geom.POINT_PRECISION)
    geoBaseProj = pygeos.difference(geoBaseProj, geoDifferenceProj, grid_size=geom.POINT_PRECISION)
    return proj.toWorld(geoBaseProj)


def intersection(geoBase: pygeos.Geometry, geoDifference: pygeos.Geometry) -> list[pygeos.Geometry]:
    """
        3d difference for polygons
    """
    proj = Projection(
        origin=pygeos.points(pygeos.get_coordinates(geoBase)[0]),
        unitZ=faceNormal(geoBase)
    )
    geoBaseProj = pygeos.set_precision(proj.toUV(geoBase), geom.POINT_PRECISION)
    geoDifferenceProj = pygeos.set_precision(proj.toUV(geoDifference), geom.POINT_PRECISION)
    geoBaseProj = pygeos.difference(geoBaseProj, geoDifferenceProj, grid_size=geom.POINT_PRECISION)
    return proj.toWorld(geoBaseProj)


def rayFaceIntersect(ray: Ray, face: pygeos.Geometry,
                     normal: Vector = None, infinity_face=False, limit_distance=None) -> pygeos.Geometry | None:
    """func to calculate the intersection for face and ray in many circumstances.

    ray: input ray as Ray object
    face: input face as pygeos.Geometry
    normal: faceNormal(face), you can provide one to accelerate the calculation
    infinity_face: do not test the containment of the face and the intersection
    limit_distance: the "ray" is a line and have limit length

    return: point as pygeos.points, None if no intersection

    --------------------------------------
        plan expression: (P - p0).n = 0
        ray expression: P(t) = p1 + tu
        cross them: (P(t) - p0).n = (p1 + tu - p0).n = 0
        as result: P(t) = p1 + t*u = p1 + ((p0 - p1).n/u.n) * u
    """
    if normal is None:
        normal = faceNormal(face)
    if Vector.dot(ray.direction, normal) == 0:
        return None

    vec = ray.direction.unit().array
    normal = Vector(normal).unit().array

    p0 = pygeos.get_coordinates(face, include_z=True)[0]
    p1 = ray.origin.array
    t = np.dot((p0 - p1), normal) / np.dot(normal, vec)
    if t < 0:
        return None
    if limit_distance is not None:
        if t > limit_distance:
            return None
    pt = p1 + t * vec
    if infinity_face:
        return pygeos.points(pt)
    else:
        coordinates = pygeos.get_coordinates(face,include_z=True)
        if np.min(coordinates[:,0])<=pt[0]<=np.max(coordinates[:,0]):
            if np.min(coordinates[:,1])<=pt[1]<=np.max(coordinates[:,1]):
                if np.min(coordinates[:,2])<=pt[2]<=np.max(coordinates[:,2]):
                    return pygeos.points(pt)
        # proj = Projection(origin=p0, unitZ=normal)
        # face = proj.toUV(face)
        # pt = proj.toUV(pt)
        # if pygeos.contains(pygeos.force_2d(face), pygeos.force_2d(pt)):
        #     return proj.toWorld(pt)

        else:
            return None


def simplify(geo: pygeos.Geometry, include_z=False) -> pygeos.Geometry:
    """simplified the geometry to remove redundant points where the last and next directions are parallel"""
    coordinates = pygeos.get_coordinates(geo, include_z=include_z)[:-1]
    points = pygeos.points(coordinates)
    edges = [coordinates[i] - coordinates[i - 1] for i in range(len(coordinates))]
    delPoints = []
    for i in range(1, len(edges)):
        if Vector.parallel(edges[i - 1], edges[i]):
            delPoints.append(i)
    points = np.delete(points, delPoints)
    points = np.append(points, points[0])
    if pygeos.get_dimensions(geo) == 1:
        return pygeos.linestrings(pygeos.get_coordinates(points, include_z=include_z))
    if pygeos.get_dimensions(geo) == 2:
        try:
            return pygeos.polygons(pygeos.get_coordinates(points, include_z=include_z))
        except:
            raise GeometryError(geo, "")


def split(geo: pygeos.Geometry, spliter: Ray | pygeos.Geometry, normal=None) -> list[list[pygeos.Geometry]]:
    """
    split the polygon by curve or plane
    In this version only polygon can be accepted as geo,
    line(pygoes.Geometry) polygon(pygeos.Geometry) plane(Ray) can be accepted as spliter.
    the normal of the spliter can be automatically calculated.
    Besides, you can send a Ray object as a spliter to create both the normal and spliter plane
    """
    if isinstance(spliter, Ray):
        normal = spliter.direction
        proj = Projection(spliter.origin, spliter.direction)
        spliter = proj.toWorld(pygeos.polygons(
            [[-9999, -9999, 0], [-9999, 9999, 0], [9999, 9999, 0], [9999, -9999, 0], [-9999, -9999, 0]]))
    elif not isinstance(spliter, pygeos.Geometry):
        raise Exception(f'wrong type of spliter, except{pygeos.Geometry} or {Ray} got {type(spliter)}')

    # if spliter is a linestring, call splitByCurve directly
    if pygeos.get_dimensions(spliter) == 1:
        return splitByCurve(geo, spliter)

    coordinates = pygeos.get_coordinates(geo, include_z=True)
    edges = [[pygeos.points(coordinates[i]), pygeos.points([coordinates[i + 1] - coordinates[i]])] for i in
             range(len(coordinates) - 1)]
    if normal is None:
        normal = faceNormal(spliter).array
    else:
        normal = Vector(normal).array

    # Calculates the intersection point, and the insertion sequence number of the intersection point
    intersectPoint = [
        rayFaceIntersect(Ray(edge[0], Vector(edge[1]).unit()), face=spliter, normal=Vector(normal),
                         limit_distance=Vector(edge[1]).length()) for edge in edges]
    intersectPoint = [poi for poi in intersectPoint if poi is not None]

    # Sort intersect points according to the order of x, y, and z
    sortlist = np.array([intersectPoint, pygeos.get_x(intersectPoint), pygeos.get_y(intersectPoint),
                         pygeos.get_z(intersectPoint)]).T.tolist()
    sortlist.sort(key=lambda x: (x[3], x[2], x[1]))

    # construct 3d split lines
    spliter = pygeos.linestrings(pygeos.get_coordinates([sortlist[0][0], sortlist[-1][0]]))
    return splitByCurve(geo, spliter)


def section(geo: pygeos.Geometry, elevation: float, segment=True) -> list[pygeos.Geometry] | pygeos.Geometry | None:
    """Calculate the section for a geometry on given elevation(z value), which can be used to do a section on z
    Return all parts of the section if segment==True
    Otherwise, only the biggest line will be return, it can be used to split the geometry by split() method
    """
    coordinates = pygeos.get_coordinates(geo)
    points = pygeos.points([np.append(coor, elevation) for coor in coordinates])

    points = [poi for poi in points if distance(poi, geo) < geom.POINT_PRECISION]

    if len(points) < 2:
        return []

    # sort the point by x and y coordinates, find the biggest line
    sort_list = [[poi, coor[0], coor[1]] for poi, coor in zip(points, coordinates)]
    sort_list.sort(key=lambda x: (x[1], x[2]))
    points = [item[0] for item in sort_list]
    if segment:
        edges = [pygeos.linestrings(pygeos.get_coordinates(points, include_z=True)[i:i + 2]) for i in
                 range(len(points) - 1)]
        secionedges = []
        for edge in edges:
            if pygeos.contains(geo, edge):
                secionedges.append(edge)
        return secionedges
    else:
        if pygeos.distance(points[0], points[-1]) > geom.POINT_PRECISION:
            return pygeos.linestrings(pygeos.get_coordinates([points[0], points[-1]], include_z=True))
        else:
            return None


def distance(point, polygon: pygeos.Geometry, normal=None):
    """
        Get the distance for a point to a polygon or plane.
        actually if you know the origin of the plane(as Ray) the distance should be
        abs(Vector.dot(Vector(point).array - plane.origin.array, plane.direction))
    """
    point = Vector(point).array
    if normal is None:
        normal = faceNormal(polygon).array
    else:
        normal = Vector(normal).array
    vec = pygeos.get_coordinates(polygon, include_z=True)[0] - point
    return np.abs(Vector.dot(vec, normal))


def splitByCurveLagacy(geoBase: pygeos.Geometry, curve: pygeos.Geometry) -> list[list[pygeos.Geometry]]:
    """
        This function is part of the split function. It should not be used directly.
    """
    proj = Projection(
        origin=pygeos.points(pygeos.get_coordinates(geoBase, include_z=True)[0]),
        unitZ=faceNormal(geoBase)
    )
    geoBaseProj = pygeos.set_precision(proj.toUV(geoBase), geom.POINT_PRECISION)
    curveProj = pygeos.set_precision(proj.toUV(curve), geom.POINT_PRECISION)
    points = pygeos.points(pygeos.get_coordinates(geoBaseProj, include_z=True))
    geoCollection = [[], []]
    breakPoint = 0
    pointOnCurve = None
    side = 1

    # Start by segmenting the curve according to both sides of the dividing line
    for i in range(len(points) - 1):
        # If the current point is on the split line, move the split point to that point and continue
        if pygeos.covers(curveProj, points[i]):
            breakPoint = i
            pointOnCurve = None
            continue

        # If the current and back points are on opposite sides of z, or the back point is on the dividing line,
        # the segment crosses the dividing line (the current point will not be on the dividing line)
        edge = pygeos.linestrings(pygeos.get_coordinates([points[i], points[i + 1]]))
        if pygeos.intersects(edge, curveProj):
            subCurve = points[breakPoint:i + 1]
            breakPoint = i + 1
            # Insert last point
            if pointOnCurve is not None:
                subCurve = np.append([pointOnCurve], subCurve)
            # Insert next point
            pointOnCurve = pygeos.intersection(edge, curveProj, grid_size=geom.POINT_PRECISION)
            subCurve = np.append(subCurve, pointOnCurve)
            geoCollection[int((side + 1) / 2)].append(subCurve)
            side *= -1
    side = int((side + 1) / 2)
    subCurve = points[breakPoint:]
    # Insert last point
    if pointOnCurve is not None:
        subCurve = np.append(pointOnCurve, subCurve)
    geoCollection[side].append(subCurve)

    # If the start point and end point of the curve belong to two segments in the same group, join them.
    for i in range(len(geoCollection[side])):
        if points[0] in geoCollection[side][i] and i != len(geoCollection[side]) - 1:
            geoCollection[side][i] = np.append(geoCollection[side][-1][:-1], geoCollection[side][i])
            geoCollection[side].pop()
            break

    # The envelope times of the inner and outer collections were respectively used to determine
    # the positive and negative shapes, and hollowed out
    for group in [0, 1]:
        collection = []
        geoCollection[group] = [closeTheCurve(pygeos.linestrings(pygeos.get_coordinates(curve, include_z=True))) for
                                curve in geoCollection[group]]
        voidVolume = [1 for i in geoCollection[group]]
        diffDict = {i: [] for i in range(len(geoCollection[group]))}
        for i in range(len(geoCollection[group])):
            for j in range(i, len(geoCollection[group])):
                if pygeos.contains(geoCollection[group][i], geoCollection[group][j]):
                    voidVolume[j] *= -1
                    diffDict[i].append(j)
                if pygeos.contains(geoCollection[group][j], geoCollection[group][i]):
                    voidVolume[i] *= -1
                    diffDict[j].append(i)

        for i in diffDict.keys():
            if voidVolume[i] == -1: continue
            thisGeo = geoCollection[group][i]
            for j in diffDict[i]:
                if voidVolume[j] == 1: continue
                thisGeo = difference(thisGeo, geoCollection[group][j])
            collection.append(thisGeo)
        geoCollection[group] = collection

    # Reproject the curve to worldXY
    for group in [0, 1]:
        for i in range(len(geoCollection[group])):
            faceProj = geoCollection[group][i]
            faceWorld = proj.toWorld(faceProj)
            geoCollection[group][i] = faceWorld

    return geoCollection


def splitByCurve(geoBase: pygeos.Geometry, curve: pygeos.Geometry) -> list[list[pygeos.Geometry]]:
    """
        This function is part of the split function. It should not be used directly.
    """
    proj = Projection(
        origin=pygeos.points(pygeos.get_coordinates(geoBase, include_z=True)[0]),
        unitZ=faceNormal(geoBase)
    )
    # z=pygeos.get_coordinates(geoBase, include_z=True)
    # print(z.min(),z.max())
    # print(curve)
    geoBaseProj = proj.toUV(geoBase)
    curveProj = proj.toUV(curve)
    points = pygeos.points(pygeos.get_coordinates(geoBaseProj, include_z=True))
    geoCollection = [[], []]
    pointOnCurve = []
    curveWithBreakPoint = list(np.array(points))
    # Start by adding breakPoints
    for i in range(len(points) - 1):
        # If the current point is on the split line, append to pointOnCurve and continue
        if pygeos.covers(curveProj, points[i]):
            pointOnCurve.append(i)
        elif not pygeos.covers(curveProj, points[i + 1]):
            # If the current and back points are on opposite sides of z, or the back point is on the dividing line,
            # the segment crosses the dividing line (the current point will not be on the dividing line)
            edge = pygeos.linestrings(pygeos.get_coordinates([points[i], points[i + 1]]))
            if pygeos.intersects(edge, curveProj):
                breakPoint = pygeos.intersection(edge, curveProj, grid_size=geom.POINT_PRECISION)
                shift = len(curveWithBreakPoint) - len(points)
                curveWithBreakPoint = curveWithBreakPoint[:i + 1 + shift] + [breakPoint] + curveWithBreakPoint[
                                                                                           i + 1 + shift:]
                pointOnCurve.append(i + 1 + shift)

    if len(pointOnCurve) < 2:
        print("******Warning: Failed to split the polygon since no break point")
        return None
    elif len(pointOnCurve) == 2:
        if np.abs(pointOnCurve[0] - pointOnCurve[1]) == 1:
            print("******Warning: Failed to split the polygon since no break point")
            return None

    if pygeos.covers(curveProj, points[-1]):
        pointOnCurve.append(len(curveWithBreakPoint) - 1)

    # Translate the pointOnCurve into index
    # for i,p in enumerate(pointOnCurve):
    #     pointOnCurve[i] = curveWithBreakPoint.index(p)

    # start breaking the curve side by side
    side = 1
    for i in range(len(pointOnCurve) - 1):
        if pointOnCurve[i + 1] - pointOnCurve[i] > 1:
            subCurve = range(pointOnCurve[i], pointOnCurve[i + 1])
            subCurve = np.append(subCurve, [pointOnCurve[i + 1], pointOnCurve[i]])
            geoCollection[int((side + 1) / 2)].append(subCurve)
            side *= -1

    # add the first and last segments to the collection[0]
    if pointOnCurve[0] != 0:
        subCurve = list(range(pointOnCurve[0])) + [pointOnCurve[0], pointOnCurve[-1]] + list(
            range(pointOnCurve[-1] + 1, len(curveWithBreakPoint)))
        geoCollection[0].append(np.array(subCurve))

    # print("\nbase:",geoBase)
    # print("\nadd:",[proj.toWorld(x)for x in curveWithBreakPoint])
    # print()
    # print(pointOnCurve)
    # print(geoCollection)
    # The envelope times of the inner and outer collections were respectively used to determine
    # the positive and negative shapes, and hollowed out

    for group in [0, 1]:
        collection = []
        geoCollection[group] = [np.array(curveWithBreakPoint)[curve] for curve in geoCollection[group] if
                                len(curve) > 3]
        geoCollection[group] = [pygeos.polygons(pygeos.get_coordinates(curve, include_z=True)) for curve in
                                geoCollection[group]]
        # faceWorld=[proj.toWorld(faceProj) for faceProj in geoCollection[group]]
        # z = pygeos.get_coordinates(faceWorld, include_z=True)[:,2]
        # print(z.min(),z.max())
        voidVolume = [1 for i in geoCollection[group]]
        diffDict = {i: [] for i in range(len(geoCollection[group]))}
        for i in range(len(geoCollection[group])):
            for j in range(i, len(geoCollection[group])):
                if pygeos.contains(geoCollection[group][i], geoCollection[group][j]):
                    voidVolume[j] *= -1
                    diffDict[i].append(j)
                if pygeos.contains(geoCollection[group][j], geoCollection[group][i]):
                    voidVolume[i] *= -1
                    diffDict[j].append(i)

        for i in diffDict.keys():
            if voidVolume[i] == -1: continue
            thisGeo = geoCollection[group][i]
            for j in diffDict[i]:
                if voidVolume[j] == 1: continue
                thisGeo = difference(thisGeo, geoCollection[group][j])
            collection.append(thisGeo)
        geoCollection[group] = collection

    # Reproject the curve to worldXY
    for group in [0, 1]:
        for i in range(len(geoCollection[group])):
            faceProj = geoCollection[group][i]
            faceWorld = proj.toWorld(faceProj)
            geoCollection[group][i] = faceWorld

    return geoCollection


def lineIntersection(l1: pygeos.Geometry, l2: pygeos.Geometry):
    '''
        define the intersection point as P
        for any point P on line_1: p = o1 + t * v1
        p is on line_2: np.cross(p - o2, v2)==0
        which means: np.cross(o1-o2+t*v1,v2)==0
        which means: np.cross(o1-o2,v2) + np.cross(t*v1,v2)== np.cross(o1-o2,v2) + t * np.cross(v1,v2) ==0
        which means: t=-np.cross(o1-o2,v2)/np.cross(v1,v2)
    '''
    edge1 = pygeos.get_coordinates(l1)
    edge2 = pygeos.get_coordinates(l2)
    o1, v1 = edge1[0], edge1[1] - edge1[0]
    o2, v2 = edge2[0], edge2[1] - edge2[0]
    if np.abs(Vector.dot(Vector(v1).unit(), Vector(v2).unit())) > 0.999: return None
    t = -np.cross(o1 - o2, v2) / np.cross(v1, v2)
    p = o1 + t * v1
    return pygeos.points(p)


def closeTheCurve(geo: pygeos.Geometry):
    # Ver 2.0 使曲线闭合
    if pygeos.is_closed(geo):
        return geo
    coordinates = pygeos.get_coordinates(geo, include_z=True).tolist()
    coordinates.append(coordinates[0])
    return pygeos.polygons(coordinates)

# 旧版本的vector计算
# 向量计算 / 整合了pygeos.Geometry类型，比np的泛用性广
# def vector.dot(vec1, vec2):
#    vec1 = vector(vec1).array
#    vec2 = vector(vec2).array
#    return np.sum([vec1[i] * vec2[i] for i in range(len(vec1))])


# def vector.to_array(vec, _3d=False):
#    vec = vector(vec).array
#    if not _3d:
#        vec = vec[:2]
#    return vec

# def vec_cross(vec1, vec2):
#    vec1 = vector(vec1).array
#    vec2 = vector(vec2).array
#    return np.cross(vec1, vec2)


# def vec_length(vec, power=False):
#    vec = vector(vec).array
#    if power:
#        return np.sum([i * i for i in vec])
#    else:
#        return np.power(np.sum([i * i for i in vec]), 0.5)


# def vec_angle(vec):
#    '''
#    vec在正y轴：返回vector.dot([1,0],vec)结果在[-1,1]中，[1,0]为1,[0,1]为0,[-1,0]为-1
#    vec在负y轴：返回-vector.dot([1,0],vec)-2结果在[-3,-1]中,[.99,-.01]为-3,[0,-1]为-2,[-.99,-.01]为-1
#    返回值与沿逆时针方向[-3,1]的角度大小正相关
#    '''
#
#    if type(vec) == pygeos.Geometry:
#        vec = vector.to_array(vec, False)
#    if vec_length(vec) == 0:
#        print('zero length vector')
#        return None
#    vec = vec / vec_length(vec)
#    dot = vector.dot(np.array([1, 0]), vec)
#    if vec[1] < 0:
#        dot = -dot - 2
#    return dot


# def vec_to_string(vec):
#    vec = vec_unit(vec)
#    if vec[0] < 0:
#        return vec_to_string(np.array([-vec[0], -vec[1], -vec[2]]))
#    else:
#        if vec[0] == 0 and vec[1] < 0:
#            return vec_to_string(np.array([-vec[0], -vec[1], -vec[2]]))
#        else:
#            if vec[0] == 0 and vec[1] == 0 and vec[2] < 0:
#                return vec_to_string(np.array([-vec[0], -vec[1], -vec[2]]))

#    vec = vec.tolist()
#    for i in range(3):
#        if vec[i] == 0:
#            vec[i] = '0.0'
#        else:
#            vec[i] = str(round(vec[i], 1))
#    return '_'.join(vec)


# Ver1.3 判断平行
# def vector.parallel(vec1, vec2):
#    vec1 = vec_unit(vec1)
#    vec2 = vec_unit(vec2)
#    dot = vector.dot(vec1, vec2)
#    if dot < 1.0 + 0.001 and dot > 1.0 - 0.001:
#        return True
#    if dot < -1.0 + 0.001 and dot > -1.0 - 0.001:
#        return True
#    return False

# def vec_equal(vec1, vec2):
#    vec1 = vector(vec1)
#    vec2 = vector(vec2)
#    if vec_length(vec1.array-vec2.array , True) < geom.POINT_PRECISION:
#        return True
#    return False
