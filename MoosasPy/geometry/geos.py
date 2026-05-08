"""
    This module defines the main function for geometric processing. This module is used as a foundation for the models,
    transforming and encoding module. It has no documented public API and should not be used directly.
    This module has been translated from Chinese into English by Microsoft translation. Some expressions may be
    inaccurate or unprofessional.
"""
from __future__ import annotations

from ..utils import pygeos, np, GeometryError, Iterable
from ..utils.constant import geom


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
        Initialize a Vector object from various input types.
        
        Parameters
        ----------
        vec : Vector or Iterable or pygeos.Geometry or float or int
            Input representing a vector, which can be provided as:
            - A Vector instance
            - A pygeos.Geometry (point, line, etc.)
            - An Iterable (list, tuple, numpy array) of coordinates
            - Individual float or int values (as variable arguments)
        
        Returns
        -------
        None
            This constructor initializes the instance attributes x, y, z, and style.
        """
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
            if pygeos.is_empty(vec):
                vec = np.array([0, 0, 0])
                self.style = np.ndarray
            else:
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
        """
        Return the underlying geometry or array representation based on the current style.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `dump` property, with attributes `style`, `geometry`, and `array`.
        
        Returns
        -------
        numpy.ndarray or pygeos.Geometry
            If `self.style` is `pygeos.Geometry`, returns `self.geometry`; otherwise, returns `self.array`.
        """
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
        Return a string representation of the vector for comparing direction, where small values are zeroed and components are rounded.
        
        Parameters
        ----------
        self : Vector
            The Vector instance whose direction string is to be generated. The vector is normalized and its components are processed
            to allow comparison of direction, treating opposite vectors as equivalent in certain contexts.
        
        Returns
        -------
        str
            A string representation of the vector with components separated by underscores. Components smaller than 
            `geom.POINT_PRECISION` are replaced with '0.00', others are rounded to 2 decimal places. This format allows 
            forward and reverse vectors (e.g., [0,0,1] and [0,0,-1]) to have the same string representation when symmetry 
            in direction comparison is desired.
        """
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
            if abs(vec[i]) < geom.POINT_PRECISION:
                vec[i] = '0.00'
            else:
                vec[i] = round(vec[i], 2)
        return '_'.join(vec.astype(str))

    @property
    def uniform(self):
        """
        Get a normalized uniform representation of the vector.
        
        This property returns a unit vector in a consistent direction based on the
        lexicographic sign convention, ensuring that antipodal vectors (like `vec` and `-vec`)
        map to the same uniform vector. Specifically, the signs are flipped if the first
        non-zero component is negative.
        
        Parameters
        ----------
        self : Vector
            The vector instance for which the uniform representation is computed.
        
        Returns
        -------
        Vector
            A new Vector instance representing the uniform unit vector. The direction
            is adjusted so that the first non-zero component is non-negative, ensuring
            consistency across opposite vectors.
        """
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
        """
        Convert an azimuth angle to a unit direction vector.
        
        Parameters
        ----------
        azimuth : float
            The azimuth angle in degrees, measured clockwise from the positive y-axis.
            Negative angles are normalized to the range [0, 360).
        
        Returns
        -------
        Vector
            A unit vector in the xy-plane corresponding to the given azimuth, with z-component zero.
        """
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
        """
        Compute the length (magnitude) of the vector.
        
        Parameters
        ----------
        power : bool, optional
            If True, return the squared length (sum of squares) without taking the square root,
            which can accelerate the calculation. Default is False.
        
        Returns
        -------
        float
            The length of the vector. If `power` is True, returns the squared length;
            otherwise, returns the Euclidean norm.
        """
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
    def parallel(vec1, vec2, tolerance=None):
        """test if two vector is parallel, based on their dot value"""
        if not tolerance:
            tolerance = Vector.ANGLE_TOLERANCE
        vec1 = Vector(vec1)
        vec2 = Vector(vec2)
        if vec1.length() == 0 or vec2.length() == 0:
            return True
        dot = pow(vec1 * vec2, 2) / vec2.length(True) / vec1.length(True)
        if 1.0 + tolerance > dot > 1.0 - tolerance:
            return True
        if -1.0 + tolerance > dot > -1.0 - tolerance:
            return True
        return False

    @staticmethod
    def equal(vec1, vec2):
        """
        Check if two vectors are approximately equal within a given precision.
        
        Parameters
        ----------
        vec1 : array-like
            First vector to compare. Can be a list, tuple, or array.
        vec2 : array-like
            Second vector to compare. Can be a list, tuple, or array.
        
        Returns
        -------
        bool
            True if the vectors are approximately equal within POINT_PRECISION, False otherwise.
        """
        vec1 = Vector(vec1)
        vec2 = Vector(vec2)
        if Vector(vec1.array - vec2.array).length(True) < geom.POINT_PRECISION:
            return True
        return False

    def __add__(self, other):
        """Add two Vector objects element-wise.
        
                Parameters
                ----------
                other : Vector
                    Another Vector object whose array elements will be added to this vector's array.
        
                Returns
                -------
                Vector
                    A new Vector object containing the element-wise sum of the two vectors.
                """
        return Vector(self.array + other.array)

    def __sub__(self, other):
        """
        Subtracts another vector from this vector element-wise.
        
        Parameters
        ----------
        other : Vector
            The vector to be subtracted from this vector. Must have an `array` attribute 
            compatible with numpy-style subtraction.
        
        Returns
        -------
        Vector
            A new Vector instance containing the result of element-wise subtraction 
            of `other.array` from `self.array`.
        """
        return Vector(self.array - other.array)

    def __abs__(self):
        """Return the absolute value of each component in the vector.
        
                Returns
                -------
                Vector
                    A new Vector instance with the absolute values of the original components.
                """
        return Vector(np.abs(self.array))

    def __neg__(self):
        """Return the negation of the object by multiplying by -1.
        
                Returns
                -------
                Any
                    A new object that is the negation of `self`, obtained by multiplying by -1.
        """
        return self.__mul__(-1)

    def __getitem__(self, item):
        """
        Get item from the array using indexing.
        
        Parameters
        ----------
        item : int or slice
            Index or slice object specifying the position(s) to retrieve from the array.
        
        Returns
        -------
        Any
            The element or subarray at the specified index or slice.
        """
        return self.array.__getitem__(item)

    def __mul__(self, other):
        """
        Scalar multiplication or dot product of two vectors.
        
        Parameters
        ----------
        other : Vector or float or int
            The other vector or scalar to multiply with. If `other` is a Vector, 
            computes the dot product. If `other` is a scalar (int or float), 
            performs scalar multiplication and returns a new Vector.
        
        Returns
        -------
        float or Vector
            If `other` is a Vector, returns the dot product as a float. 
            If `other` is a scalar, returns a new Vector with components scaled by the scalar.
        """
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y + self.z * other.z
        else:
            return Vector(other * self.array)

    def __truediv__(self, other):
        """
        Divides the vector by a scalar or array and returns a new Vector instance.
        
        Parameters
        ----------
        other : scalar or array-like
            The value(s) to divide the vector's components by. Can be a scalar or an array-like 
            object compatible with numpy broadcasting rules.
        
        Returns
        -------
        Vector
            A new Vector instance containing the result of element-wise division.
        """
        return Vector(self.array / other)

    def __xor__(self, other):
        """
        Element-wise XOR or cross product operation between two Vectors or a Vector and a scalar.
        
        Parameters
        ----------
        other : Vector or array_like
            The second operand for the operation. If `other` is a Vector, computes the cross 
            product of the two vectors using their underlying arrays. If `other` is a scalar 
            or array_like, performs element-wise power (np.pow) of the vector's array with `other`.
        
        Returns
        -------
        Vector
            A new Vector instance containing the result of the cross product (if `other` is a Vector) 
            or element-wise power operation (if `other` is a scalar or array_like).
        """
        if isinstance(other, Vector):
            return Vector(np.cross(self.array, other.array))
        else:
            return Vector(np.pow(self.array, other))

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.x, self.y, self.z)

    def __hash__(self):
        """
        Compute the hash value of the object based on its key.
        
        Returns
        -------
        int
            The hash value of the object, computed from its key.
        """
        return hash(self.__key())

    def __eq__(self, other):
        """
        Check equality between this Vector and another object.
        
        Parameters
        ----------
        self : Vector
            The first vector operand.
        other : object
            The second operand to compare against, typically a Vector or compatible object.
        
        Returns
        -------
        bool
            True if the two vectors are equal, False otherwise.
        """
        return Vector.equal(self, other)

    def __ne__(self, other):
        """Check inequality between this object and another.
        
                Parameters
                ----------
                other : object
                    The object to compare with this instance.
        
                Returns
                -------
                bool
                    True if the objects are not equal, False otherwise.
                """
        return not self.__eq__(other)

    def __repr__(self):
        """
        Return a string representation of the Vector instance with formatted coordinates.
        
        Returns
        -------
        str
            A string in the format "Vector(x, y, z)" where x, y, and z are formatted to two decimal places.
        """
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
        """
        Initialize a Ray object with an origin, direction, and optional value.
        
        Parameters
        ----------
        origin : array-like or Vector
            The starting point of the ray. If not a Vector, it will be converted to one.
        direction : array-like or Vector
            The direction vector of the ray. If not a Vector, it will be converted to one.
            It will be normalized to a unit vector.
        value : float, optional
            An associated scalar value with the ray (default is 0).
        
        Returns
        -------
        None
        """
        if not isinstance(origin, Vector):
            origin = Vector(origin)
        if not isinstance(direction, Vector):
            direction = Vector(direction)

        super(Ray, self).__init__(direction.unit())
        self.origin: Vector = origin
        self.value = value
        self.direction: Vector = direction.unit()

    def reverse(self):
        """
        Reverse the direction of the ray.
        
        Parameters
        ----------
        self : Ray
            The Ray instance whose direction is to be reversed.
        
        Returns
        -------
        Ray
            A new Ray instance with the same origin and value, but with the direction reversed.
        """
        return Ray(self.origin, Vector(-self.direction.array), self.value)

    def mirror(self, mir):
        """
        Compute a mirror image of the ray based on a given normal vector.
        
        Parameters
        ----------
        mir : Vector
            The normal vector defining the plane of reflection. The direction of this vector
            is used to compute the reflection; its head and tail positions are ignored.
        
        Returns
        -------
        Ray
            A new Ray instance representing the mirrored (reflected) ray. The returned ray
            is reversed such that it represents the correct propagation direction after reflection.
        """
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
        Get the standard ray export string for MoosasRad.exe.
        
        Parameters
        ----------
        self : object
            The instance of the class containing `origin` and `direction` attributes,
            each having an `array` property with numeric values.
        
        Returns
        -------
        str
            A comma-separated string representation of the ray's origin and direction coordinates.
        """
        """
        get the standard ray export to MoosasRad.exe
        """
        rayStr = list(self.origin.array) + list(self.direction.array)
        rayStr = [str(ray) for ray in rayStr]
        return ','.join(rayStr)

    def __repr__(self):
        """Return a string representation of the Ray object with origin and direction.
        
        Parameters
        ----------
        self : Ray
            The instance of the Ray object to represent as a string.
        
        Returns
        -------
        str
            A formatted string showing the origin and direction of the Ray.
        """
        return f"Ray( ori {self.origin.__repr__()} dir {self.direction.__repr__()} )"


class Projection(Ray):
    """
    Establish a three-dimensional coordinate system based on the infinite plane input and realize the conversion with
    the world coordinate system Since pygeos does not provide 3D processing, it is necessary to process 3D collection
    processing on UVs after projection through the coordinate system
    """
    __slots__ = ['axisX']

    def __init__(self, origin, unitZ, unitX=None):
        """
        Initialize a Projection object with an origin and coordinate axes.
        
        Parameters
        ----------
        origin : array-like
            The origin point of the projection, converted to a Vector.
        unitZ : array-like
            The unit vector defining the Z-axis direction of the projection.
        unitX : array-like, optional
            The unit vector defining the X-axis direction. If not provided, it is 
            computed automatically based on the Z-axis and a default reference direction.
        
        Returns
        -------
        None
            This method initializes the object and does not return a value.
        """
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
        """
        Create a new instance from a Ray object.
        
        Parameters
        ----------
        plane : Ray
            The Ray object containing origin and direction used to create the new instance.
        
        Returns
        -------
        Projection
            A new instance of the class initialized with the origin and direction from the Ray.
        """
        return cls(plane.origin, plane.direction)

    @classmethod
    def fromPolygon(cls, polygon: pygeos.Geometry):
        """
        Construct a coordinate system from a given polygon.
        
        Parameters
        ----------
        polygon : pygeos.Geometry
            A polygon geometry used to define the coordinate system. Must be a valid 3D polygon.
        
        Returns
        -------
        Projection
            An instance of the class representing the coordinate system defined by the polygon's 
            normal vector, center point, and an orthogonal basis vector derived from a cross-section.
        """
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
        Find an orthogonal basis from the most frequent edge directions in given polygons.
        
        Parameters
        ----------
        polygons : pygeos.Geometry or list of pygeos.Geometry
            A single polygon or a list of polygons from which edge vectors are extracted 
            to determine the dominant orthogonal axes.
        
        Returns
        -------
        proj : object
            An instance of the class (likely a coordinate system or projection object) 
            representing the orthogonal basis, with `unitX` aligned to the most frequent 
            edge direction and `unitZ` set to [0, 0, 1]. The basis is centered at the 
            mean coordinates of all input polygons.
        """
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
        """
        Rotation matrix representing the orientation axes.
        
        Returns
        -------
        numpy.matrix
            A 3x3 matrix where each column is one of the local axes (axisX, axisY, axisZ),
            representing the rotation from the local coordinate system to the global coordinate system.
        """
        return np.asmatrix(np.array([self.axisX, self.axisY, self.axisZ]).T)

    @property
    def axisZ(self):
        """
        Return the array attribute as a property.
        
        Returns
        -------
        numpy.ndarray
            The array associated with the instance.
        """
        return self.array

    @property
    def axisY(self):
        """
        Return the Y-axis vector computed as the cross product of X-axis and Z-axis vectors.
        
        Parameters
        ----------
        self : object
            The instance of the class containing axisX and axisZ attributes, which are 3D vectors.
        
        Returns
        -------
        numpy.ndarray
            A 3D vector representing the Y-axis, computed as the cross product of axisX and axisZ.
        """
        return np.cross(self.axisX, self.axisZ)

    def toUV(self, worldGeometry: pygeos.Geometry):
        """
        Converts a geometry from world coordinates to UV coordinates on a specified plane.
        
        Parameters
        ----------
        worldGeometry : pygeos.Geometry
            The input geometry in world coordinates to be transformed. Can be a point, 
            line, or polygon. Must be a valid 2D or 3D geometry.
        
        Returns
        -------
        pygeos.Geometry
            The geometry transformed into UV coordinates on the specified plane. The 
            output retains the type (point, linestring, polygon, etc.) of the input 
            geometry but is represented in the 2D UV coordinate system of the plane.
        """
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
        Converts a geometry from UV coordinate system to world coordinate system.
        
        Parameters
        ----------
        UVGeometry : pygeos.Geometry
            The input geometry in UV coordinates to be transformed. Must be a valid 2D or 3D geometry.
        
        Returns
        -------
        pygeos.Geometry
            The transformed geometry in the world coordinate system. The type of geometry (point, linestring, polygon) 
            is preserved after transformation.
        """
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
        """
        Initialize transformation parameters for movement and rotation.
        
        Parameters
        ----------
        moveVec : array-like or pygeos.Geometry, optional
            Vector representing the translation to apply. If a pygeos Geometry is provided,
            its coordinates are extracted. Default is numpy array [0, 0].
        rotateRadius : float, optional
            Angular distance (in radians) to rotate. Default is 0.
        rotateOrigin : array-like or pygeos.Geometry, optional
            Point around which rotation occurs. If a pygeos Geometry is provided,
            its coordinates are extracted. If None, no rotation origin is set. Default is None.
        
        Returns
        -------
        None
        """
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
        """
        Rotation matrix property based on the object's rotation angle.
        
        Returns the inverse of the 2D rotation matrix corresponding to the `rotateRadius` attribute,
        where the rotation angle is given in radians. The returned matrix can be used to reverse
        the rotation transformation.
        
        Parameters
        ----------
        self : object
            The instance having the `rotateRadius` attribute, which specifies the rotation
            angle in radians.
        
        Returns
        -------
        numpy.matrix
            A 2x2 inverse rotation matrix represented as a NumPy matrix object.
        """
        rotateMatrix = [np.cos(self.rotateRadius), -np.sin(self.rotateRadius)], [np.sin(self.rotateRadius),
                                                                                 np.cos(self.rotateRadius)]
        rotateMatrix = np.asmatrix(np.array(rotateMatrix).T).I
        return rotateMatrix

    @classmethod
    def opposite(cls, transformation):
        """
        Get the inverse of a given transformation.
        
        Parameters
        ----------
        transformation : object
            An object representing a transformation, which must have attributes `moveVec` (numpy.ndarray or similar),
            `rotateAngle` (float), and `rotateOrigin` (numpy.ndarray or None). The `moveVec` represents the translation 
            vector, `rotateAngle` the rotation angle in radians, and `rotateOrigin` the origin point for rotation, if any.
        
        Returns
        -------
        object
            A new instance of the class (same type as `cls`) representing the opposite transformation, with reversed 
            translation (`-moveVec`), reversed rotation angle (`-rotateAngle`), and adjusted rotation origin if applicable.
        """
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
        Transform a geometry by applying translation followed by rotation.
        
        Parameters
        ----------
        geo : pygeos.Geometry
            The input geometry to be transformed. Can be a point, linestring, or polygon.
        
        Returns
        -------
        pygeos.Geometry
            The transformed geometry after applying translation and optional rotation.
            The output type matches the input geometry type (point, linestring, or polygon).
        """
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
    Determine if a polygon's ring is oriented counter-clockwise.
    
    Parameters
    ----------
    geo : pygeos.Geometry
        A geometry object representing a polygon or line string. Must have at least 3 points to form a ring.
    
    Returns
    -------
    bool
        True if the ring is oriented counter-clockwise, False otherwise.
    """

    poilist = pygeos.get_coordinates(geo)
    veclist = [poilist[i] - poilist[i - 1] for i in range(1, len(poilist))]
    crosslist = [np.cross(veclist[i], veclist[i - 1]) for i in range(len(veclist))]
    ccw = np.sum([2 for vec in crosslist if vec > 0])
    ccw -= len(crosslist)
    return ccw < 0


def selfIntersect(geo: pygeos.Geometry) -> bool:
    """
    Test whether a geometry is self-intersecting.
    
    Parameters
    ----------
    geo : pygeos.Geometry
        A PyGEOS geometry object to be tested for self-intersection.
    
    Returns
    -------
    bool
        True if the geometry is self-intersecting, False otherwise.
    """
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
    Determine if two geometries share at least two endpoints, indicating a common edge.
    
    Parameters
    ----------
    geo1 : pygeos.Geometry
        First geometry object to compare.
    geo2 : pygeos.Geometry
        Second geometry object to compare.
    
    Returns
    -------
    bool
        True if the two geometries share at least two endpoints (i.e., overlap on an edge), False otherwise.
    """
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
    Calculate the overlapping area between two geometries.
    
    Parameters
    ----------
    geo1 : pygeos.Geometry
        The first input geometry.
    geo2 : pygeos.Geometry
        The second input geometry.
    
    Returns
    -------
    float
        The area of the intersection between geo1 and geo2. Returns 0.0 if there is no overlap, 
        if either geometry is empty, or if an error occurs during computation.
    """
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


def area3d(geo: pygeos.Geometry) -> float:
    """Calculate polygon area in 3D by projecting to its local UV plane.

    pygeos only measures planar 2D area, so this helper projects each
    polygon part to its own UV coordinate system and sums UV areas.
    """
    if geo is None or pygeos.is_empty(geo):
        return 0.0

    total = 0.0
    try:
        parts = [p for p in pygeos.get_parts(geo) if pygeos.get_dimensions(p) == 2]
    except Exception:
        parts = [geo] if pygeos.get_dimensions(geo) == 2 else []

    for part in parts:
        try:
            proj = Projection.fromPolygon(part)
            uv = pygeos.force_2d(proj.toUV(part))
            total += float(pygeos.area(uv))
        except Exception:
            continue
    return total


def makeValid(geo: pygeos.Geometry, error='raise') -> list[pygeos.Geometry] | None:
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
    """
    Check if all points of a child geometry are within a specified distance from a parent geometry.
    
    Parameters
    ----------
    child : pygeos.Geometry
        The geometry whose points are to be checked for proximity to the parent.
    parent : pygeos.Geometry
        The geometry used as reference for proximity checking.
    
    Returns
    -------
    bool
        True if all points of the child geometry are within twice the POINT_PRECISION distance 
        from the parent geometry, False otherwise. Returns False if an error occurs during processing.
    """
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
    """Check if two geometries are approximately equal by comparing their points within a tolerance.
    
    Parameters
    ----------
    geo1 : pygeos.Geometry
        First geometry to compare.
    geo2 : pygeos.Geometry
        Second geometry to compare.
    
    Returns
    -------
    bool
        True if the geometries have the same number of points and all corresponding points 
        (in forward or reverse order) are within 1.2 * geom.POINT_PRECISION distance; otherwise False.
    """
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


def projectTo(child: pygeos.Geometry, parent: pygeos.Geometry) -> pygeos.Geometry:
    """
        project a child surface to the parent surface.

        Parameters
        ----------
        child : pygeos.Geometry
            3D polygon geometry with z-coordinates (pygeos.Polygon type) to be projected.
        parent : pygeos.Geometry
            3D polygon geometry with z-coordinates (pygeos.Polygon type) as the Projection aixs system.

        Returns
        -------
        pygeos.Geometry

        Notes
        -----
        - Projection.toUV method
    """
    proj = Projection.fromPolygon(parent)
    childProj = proj.toUV(child)
    childProj = pygeos.force_3d(pygeos.force_2d(childProj), z=0)
    child = proj.toWorld(childProj)
    if Vector.dot(faceNormal(child), faceNormal(parent)) < 0:
        coordinates = pygeos.get_coordinates(child,include_z=True)[::-1]
        child = pygeos.polygons(coordinates)
    return child


def trim(child: pygeos.Geometry, parent: pygeos.Geometry) -> pygeos.Geometry | None:
    """
    Trim a child surface with the parent surface.

    Parameters
    ----------
    child : pygeos.Geometry
        3D polygon geometry with z-coordinates (pygeos.Polygon type) to be trimmed.
    parent : pygeos.Geometry
        3D polygon geometry with z-coordinates (pygeos.Polygon type) as the splitter.

    Returns
    -------
    pygeos.Geometry

    Notes
    -----
    - pygeos.intersection method
    """
    proj = Projection.fromPolygon(parent)
    childProj = proj.toUV(child)
    parentProj = proj.toUV(parent)
    if overlapArea(childProj, parentProj) < pygeos.area(childProj):
        childProjIntersection = pygeos.intersection(childProj, parentProj)
        if pygeos.get_dimensions(childProjIntersection) == 2:
            childProjIntersection = pygeos.get_parts(childProjIntersection)[0]
            return proj.toWorld(childProjIntersection)
        else:
            return None
    return child


def offset(polygon: pygeos.Geometry, offset: float) -> pygeos.Geometry:
    """
    Offset a geometry by a specified offset. Positive for outer offset and negative for inner offset.

    Parameters
    ----------
    polygon : pygeos.Geometry
        3D polygon geometry with z-coordinates (pygeos.Polygon type) to be offset.
    offset : float
        offset distance

    Returns
    -------
    pygeos.Geometry

    Notes
    -----
    - pygeos.buffer method


    """
    proj = Projection.fromPolygon(polygon)
    polygonProj = proj.toUV(polygon)
    polygonProjOffset = pygeos.buffer(polygonProj, offset)
    return proj.toWorld(polygonProjOffset)


def faceNormal(poly: pygeos.Geometry, EPS: float = geom.POINT_PRECISION) -> Vector:
    """
    Compute stable normal vector for 3D polygon (handles non-convex/non-coplanar vertices)

    Parameters
    ----------
    poly : pygeos.Geometry
        3D polygon geometry with z-coordinates (pygeos.Polygon type)
    EPS : float, optional
        Floating point precision threshold (default: 1e-9)

    Returns
    -------
    Vector
        Unit normal vector (x, y, z) of shape (3,)
        Returns None if computation fails (invalid input/insufficient vertices)

    Notes
    -----
    - Uses PCA + SVD for non-coplanar vertices (most stable method)
    - Falls back to edge cross product for triangular faces (faster)
    - Ensures consistent orientation via right-hand rule
    """
    # ------------------- Step 1: Validate input and extract 3D coordinates -------------------

    # Extract 3D coordinates (remove closing duplicate point)
    coords = pygeos.get_coordinates(poly, include_z=True)
    if coords.shape[1] != 3:
        return Vector(0, 0, 1)

    # Remove duplicate closing point and filter valid vertices
    vertices = coords[:-1] if np.allclose(coords[0], coords[-1], atol=EPS) else coords
    vertices = np.unique(vertices, axis=0)  # Remove duplicate vertices
    n_vertices = len(vertices)

    if n_vertices < 3:
        return Vector(0, 0, 1)  # Need at least 3 unique vertices

    # ------------------- Step 2: Fast path for triangular faces (3 vertices) -------------------
    if n_vertices == 3:
        # Compute two edge vectors
        v1 = vertices[1] - vertices[0]
        v2 = vertices[2] - vertices[0]

        # Cross product for normal
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)

        if norm < EPS:
            print("******GeometryError: invalid face results in zero normal")
            return Vector(0, 0, 1)  # Collinear vertices
        return Vector(normal / norm)

    # ------------------- Step 3: PCA + SVD for non-coplanar polygons (stable method) -------------------
    # Center vertices (remove translation)
    centroid = np.mean(vertices, axis=0)
    centered = vertices - centroid

    # Compute covariance matrix (3x3, symmetric)
    cov_matrix = np.dot(centered.T, centered) / (n_vertices - 1)

    # SVD decomposition (stable for small matrices)
    _, _, vh = np.linalg.svd(cov_matrix)
    normal = vh[-1]  # Normal = eigenvector with smallest eigenvalue (best fit plane)

    # ------------------- Step 4: Ensure consistent orientation -------------------
    # Use right-hand rule with first two edges for orientation consistency
    edge1 = vertices[1] - vertices[0]
    edge2 = vertices[2] - vertices[0]
    reference_normal = np.cross(edge1, edge2)

    # Flip normal if it opposes reference orientation
    if np.dot(normal, reference_normal) < 0:
        normal = -normal

    # ------------------- Step 5: Normalize and return unit vector -------------------
    norm = np.linalg.norm(normal)
    if norm > EPS:
        norm = normal / norm
        return Vector(norm)
    else:
        raise GeometryError(poly, "******GeometryError: invalid face results in zero normal")

def ccwNormal(poly: pygeos.Geometry, EPS: float = geom.POINT_PRECISION) -> Vector:
    """
    enhance Normal method for 3D polygon to ensure the normal pass the ccw test.
    using the faceNormal method.

    Parameters
    ----------
    poly : pygeos.Geometry
        3D polygon geometry with z-coordinates (pygeos.Polygon type)
    EPS : float, optional
        Floating point precision threshold (default: 1e-9)

    Returns
    -------
    Vector
        Unit normal vector (x, y, z) of shape (3,)
        Returns None if computation fails (invalid input/insufficient vertices)

    Notes
    -----
    - Uses PCA + SVD for non-coplanar vertices (most stable method)
    - Falls back to edge cross product for triangular faces (faster)
    - Ensures consistent orientation via right-hand rule
    """
    norm = faceNormal(poly, EPS)
    proj = Projection(origin=pygeos.get_coordinates(poly)[0],unitZ=norm)
    polyProj = proj.toUV(poly)
    polyProj = pygeos.force_2d(polyProj)
    if is_ccw(polyProj):
        return norm
    else:
        return -norm
# def faceNormalLegacy(face: pygeos.Geometry) -> Vector:
# #     """Calculate the normal vector of a face using cross product of non-parallel edges.
# #
# #         Parameters
# #         ----------
# #         face : pygeos.Geometry
# #             A geometry object representing a face or linestring. Coordinates are extracted to compute edge vectors.
# #
# #         Returns
# #         -------
# #         Vector
# #             A unit vector representing the normal to the face, computed via the cross product of two non-parallel edges.
# #             If no such pair is found, returns a Vector constructed directly from the face.
# #         """
# #     """calculate the face normal by cross calculation.
# #     we only need to find two edges that do not parallel.
# #     in this case, this method is valid even if a linestring is provided
# #     """
# #     coordinates = pygeos.get_coordinates(face, include_z=True)
# #     edges = [coordinates[i] - coordinates[i + 1] for i in range(len(coordinates) - 1)]
# #     for i in range(1, len(edges)):
# #         if not Vector.parallel(edges[i], edges[0]):
# #             return Vector(np.cross(edges[i], edges[0])).unit()
# #     return Vector(face)


"""constructive methods"""


def difference(geoBase: pygeos.Geometry, geoDifference: pygeos.Geometry) -> list[pygeos.Geometry]:
    """
    3D difference operation between two polygons.
    
    Performs a 3D boolean difference between a base geometry and a differencing geometry by projecting 
    them into a 2D UV plane, computing the difference, and transforming the result back to 3D space.
    
    Parameters
    ----------
    geoBase : pygeos.Geometry
        The base geometry from which parts will be subtracted. Must be a valid polygon.
    geoDifference : pygeos.Geometry
        The geometry to subtract from the base. Must be a valid polygon.
    
    Returns
    -------
    list of pygeos.Geometry
        A list of geometries representing the result of the 3D difference operation.
    """
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
    Compute the 3D intersection of two geometric polygons by projecting them into 2D, performing the intersection, and transforming back.
    
    Parameters
    ----------
    geoBase : pygeos.Geometry
        The base geometry (polygon) involved in the intersection.
    geoDifference : pygeos.Geometry
        The geometry to intersect with the base geometry.
    
    Returns
    -------
    list of pygeos.Geometry
        A list containing the resulting geometry or geometries from the intersection operation in 3D space.
    """
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
        coordinates = pygeos.get_coordinates(face, include_z=True)
        if np.min(coordinates[:, 0]) <= pt[0] <= np.max(coordinates[:, 0]):
            if np.min(coordinates[:, 1]) <= pt[1] <= np.max(coordinates[:, 1]):
                if np.min(coordinates[:, 2]) <= pt[2] <= np.max(coordinates[:, 2]):
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
    delPoints = []
    # remove overlap points
    for i in range(1, len(points)):
        if Vector(coordinates[i] - coordinates[i - 1]).length(power=True) == 0:
            delPoints.append(i)
    points = np.delete(points, delPoints)
    coordinates = pygeos.get_coordinates(points, include_z=include_z)
    edges = [coordinates[i] - coordinates[i - 1] for i in range(len(coordinates))]

    # remove parallel redundant points
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
        except Exception as e:
            raise GeometryError(geo, str(e))


def split(geo: pygeos.Geometry, spliter: Ray | pygeos.Geometry, normal=None) -> list[list[pygeos.Geometry]]:
    """
    Split a polygon geometry using a curve or plane.
    
    Parameters
    ----------
    geo : pygeos.Geometry
        The input polygon geometry to be split. Only polygon geometries are supported.
    spliter : Ray or pygeos.Geometry
        The splitting element, which can be a Ray object representing a plane, or a pygeos.Geometry
        (e.g., line or polygon) used to define the split. If a Ray is provided, it defines both the
        splitting plane and its normal direction.
    normal : array-like or None, optional
        The normal vector of the splitting plane. If not provided and `spliter` is a Ray, the normal
        is taken from the Ray's direction. If `spliter` is a geometry, the normal is computed using
        the face normal of the geometry.
    
    Returns
    -------
    list[list[pygeos.Geometry]]
        A list containing one or more lists of geometric components resulting from the split.
        Each inner list represents a connected part of the split result, composed of pygeos.Geometry objects.
    """
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
    Get the distance from a point to a polygon or plane.
    
    Parameters
    ----------
    point : array-like
        The point for which the distance to the polygon or plane is calculated.
        It will be converted to a numpy array internally.
    polygon : pygeos.Geometry
        A geometric object representing the polygon. Coordinates of the polygon
        are used to compute the distance.
    normal : array-like, optional
        The normal vector of the plane. If not provided, it is computed using
        the `faceNormal` function based on the polygon. If provided, it will be
        converted to a Vector and normalized.
    
    Returns
    -------
    float
        The absolute distance from the point to the polygon or plane, computed
        as the absolute dot product between the vector from a point on the polygon
        to the input point and the normal vector.
    """
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
    Split a geometry into two parts based on intersection with a dividing curve using legacy projection-based method.
    
    This function is part of the split function. It should not be used directly.
    
    Parameters
    ----------
    geoBase : pygeos.Geometry
        The base geometry to be split, typically a linestring or polygon.
    curve : pygeos.Geometry
        The curve geometry used as the splitting divider; intersections with `geoBase` determine split locations.
    
    Returns
    -------
    list[list[pygeos.Geometry]]
        A list containing two lists of geometries: the first sublist represents geometries on one side of the split curve,
        and the second sublist represents geometries on the other side. Each sublist contains reconstructed curve segments
        after splitting and re-projection back to world coordinates.
    """
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


def splitOnZ(geoBase: pygeos.Geometry, level: float, EPS: float = 1e-9) -> list[list[pygeos.Geometry]]:
    """
    Simple logic for 3D polygon cutting: insert intersection points → reorder path → split segments → close to rings → classify output

    Parameters
    ----------
    geoBase : pygeos.Geometry
        3D simple polygon (no inner rings) with z-coordinates
    level : float
        Cutting height (z-coordinate value)
    EPS : float, optional
        Floating point precision threshold, default 1e-9

    Returns
    -------
    list[list[pygeos.Geometry]]
        List containing two sublists:
        - First sublist: Upper polygons (z > level)
        - Second sublist: Lower polygons (z < level)
        Returns original polygon wrapped in GeometryCollection if cutting fails

    Notes
    -----
    The algorithm follows these key steps:
    1. Detect intersections between polygon edges and z=level plane
    2. Reorder polygon path to start from first intersection point
    3. Split path into segments separated by intersection points
    4. Close segments to form valid rings
    5. Classify rings into upper/lower groups based on z-coordinates
    """

    # ------------------- Step 1: Extract coordinates and insert intersection points -------------------
    # Get original 3D coordinates (remove closing point which duplicates first point)
    coords = pygeos.get_coordinates(geoBase, include_z=True)[:-1].tolist()
    new_coords = []
    intersections = []  # Store all intersection points with z=level plane

    for i in range(len(coords)):
        p1 = coords[i]
        p2 = coords[(i + 1) % len(coords)]
        z1, z2 = p1[2], p2[2]

        # Add current vertex to new coordinate list
        new_coords.append(p1)
        if np.abs(z1 - level) < EPS:
            intersections.append(p1)
            continue
        if np.abs(z2 - level) < EPS:
            continue
        # Check if edge intersects z=level plane (exclude endpoints on plane)
        if (z1 - level) * (z2 - level) < -EPS and abs(z1 - z2) > EPS:
            # Calculate intersection using linear interpolation
            t = (level - z1) / (z2 - z1)
            intersect_pt = [
                p1[0] + t * (p2[0] - p1[0]),
                p1[1] + t * (p2[1] - p1[1]),
                level
            ]
            # Insert intersection point and record
            new_coords.append(intersect_pt)
            intersections.append(intersect_pt)

    # Return original polygon if insufficient intersections

    if len(intersections) < 2:
        return [
            [geoBase],  # Upper group (original)
            []  # Lower group (empty)
        ]
    # ------------------- Step 2: Reorder path to start from first intersection -------------------
    # Find position of first intersection point
    start_idx = -1
    for i, pt in enumerate(new_coords):
        if any(np.linalg.norm(np.array(pt) - np.array(ip)) < EPS for ip in intersections):
            start_idx = i
            break

    if start_idx == -1:
        return [
            [geoBase],
            []
        ]

    # Reorder coordinates to start from first intersection
    shifted_coords = new_coords[start_idx:] + new_coords[:start_idx]

    # Close the reordered path
    shifted_coords.append(shifted_coords[0])

    # ------------------- Step 3: Split path into segments at intersection points -------------------
    segments = []
    current_segment = []

    for pt in shifted_coords:
        current_segment.append(pt)

        # Split segment when encountering intersection (not first point)
        is_intersect = any(np.linalg.norm(np.array(pt) - np.array(ip)) < EPS for ip in intersections)
        if is_intersect and len(current_segment) > 1:
            segments.append(current_segment)
            current_segment = [pt]  # Start new segment with intersection point

    # Handle last segment
    if len(current_segment) > 1:
        segments.append(current_segment)

    # ------------------- Step 4: Close segments to form rings -------------------
    # Close each segment by appending first point to end
    rings = [seg + [seg[0]] for seg in segments]

    # ------------------- Step 5: Classify rings into upper/lower groups -------------------
    def classify_ring(ring, level):
        """Classify ring as 'upper' (z > level) or 'lower' (z < level)

        Parameters
        ----------
        ring : list
            List of 3D points forming a closed ring
        level : float
            Cutting height threshold

        Returns
        -------
        str
            'upper' if average z > level, 'lower' if average z < level, 'unknown' otherwise
        """
        # Calculate average z-value excluding intersection points (z=level)
        z_values = []
        for pt in ring:
            if abs(pt[2] - level) > EPS:
                z_values.append(pt[2])

        if not z_values:
            return 'unknown'
        avg_z = np.mean(z_values)
        return 'upper' if avg_z > level else 'lower'

    upper_rings = []
    lower_rings = []

    for ring in rings:
        category = classify_ring(ring, level)
        if category == 'upper':
            upper_rings.append(ring)
        elif category == 'lower':
            lower_rings.append(ring)

    # ------------------- Generate final polygons -------------------
    final_polygons_upper = []
    final_polygons_lower = []

    # Create upper polygons
    for ring in upper_rings:
        try:
            poly = pygeos.polygons(ring)
            final_polygons_upper.append(poly)
        except Exception:
            continue

    # Create lower polygons
    for ring in lower_rings:
        try:
            poly = pygeos.polygons(ring)
            final_polygons_lower.append(poly)
        except Exception:
            continue

    # Return original polygon if no valid polygons generated
    if len(final_polygons_upper) + len(final_polygons_lower) == 0:
        return [[geoBase], []]

    return [final_polygons_upper, final_polygons_lower]


def splitFace2d(geoBaseProj: pygeos.Geometry, curveProj: pygeos.Geometry) -> list[list[pygeos.Geometry]]:
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
        print("******GeometryError: Failed to split: no break point")
        return None
    elif len(pointOnCurve) == 2:
        if np.abs(pointOnCurve[0] - pointOnCurve[1]) == 1:
            print("******GeometryError: Failed to split: overlap")
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
            for j in range(i + 1, len(geoCollection[group])):
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
    return geoCollection


def splitByCurve(geoBase: pygeos.Geometry, curve: pygeos.Geometry) -> list[list[pygeos.Geometry]]:
    """
    Split a geometric object by a curve using projection and intersection analysis.
    
    Parameters
    ----------
    geoBase : pygeos.Geometry
        The base geometry to be split, typically a polygon or linestring in 3D space.
        It serves as the input shape that will be divided based on its intersection with the curve.
    curve : pygeos.Geometry
        A curve (linestring) used to split the geoBase. This curve is projected into the same
        plane as geoBase for intersection calculations.
    
    Returns
    -------
    list of list of pygeos.Geometry
        A list containing two groups of geometries resulting from the split operation.
        Each group is a list of pygeos.Geometry objects representing polygons.
        The first sublist typically represents one side of the split, and the second sublist
        the other side, with holes properly subtracted based on containment relationships.
    """
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

    geoCollection = splitFace2d(geoBaseProj, curveProj)

    if geoCollection is None:
        return None
    # Reproject the curve to worldXY
    for group in [0, 1]:
        for i in range(len(geoCollection[group])):
            faceProj = geoCollection[group][i]
            faceWorld = proj.toWorld(faceProj)
            geoCollection[group][i] = faceWorld

    return geoCollection


def lineIntersection(l1: pygeos.Geometry, l2: pygeos.Geometry):
    """
    Compute the intersection point of two line segments using vector mathematics.
    
    Parameters
    ----------
    l1 : pygeos.Geometry
        A LineString geometry representing the first line segment.
    l2 : pygeos.Geometry
        A LineString geometry representing the second line segment.
    
    Returns
    -------
    pygeos.Geometry
        A Point geometry representing the intersection point of the two lines,
        or None if the lines are parallel or nearly collinear.
    """
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
    """
    Close an open geometric curve by adding the first coordinate to the end if not already closed.
    
    Parameters
    ----------
    geo : pygeos.Geometry
        A geometric object (e.g., LineString) that may be open or closed. If the geometry is already closed,
        it is returned as-is.
    
    Returns
    -------
    pygeos.Geometry
        A new geometry where the input curve is closed by connecting the last point to the first.
        If the input was already closed, the original geometry is returned.
    """
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
"""
Compute the cross product of two 3-dimensional vectors.

Parameters
----------
vec1 : array_like
    First input vector, must be a 3-dimensional array-like object.
vec2 : array_like
    Second input vector, must be a 3-dimensional array-like object.

Returns
-------
numpy.ndarray
    The cross product of `vec1` and `vec2`, returned as a 3-dimensional numpy array.
"""
#    vec1 = vector(vec1).array
#    vec2 = vector(vec2).array
#    return np.cross(vec1, vec2)


# def vec_length(vec, power=False):
"""
Calculate the length (magnitude) of a vector.

Parameters
----------
vec : array-like
    Input vector, represented as a sequence of numerical values.
power : bool, optional
    If True, return the squared magnitude (sum of squares) instead of the Euclidean length.
    Default is False.

Returns
-------
float
    The Euclidean length of the vector if `power` is False;
    otherwise, the squared magnitude (sum of squares).
"""
#    vec = vector(vec).array
#    if power:
#        return np.sum([i * i for i in vec])
#    else:
#        return np.power(np.sum([i * i for i in vec]), 0.5)


# def vec_angle(vec):
"""
Compute a normalized angular measure of a 2D vector relative to the positive x-axis, adjusted for quadrant.

Parameters
----------
vec : array-like or pygeos.Geometry
    Input 2D vector. If a pygeos geometry is provided, it will be converted to a numpy array.
    Must have at least two components (x, y).

Returns
-------
float or None
    A value in the range [-3, 1] that is monotonically related to the counter-clockwise angle from the positive x-axis.
    Returns None if the input vector has zero length.
"""
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
"""
Convert a 3D vector to a formatted string representation.

Parameters
----------
vec : array_like
    A 3-element array or list representing a 3D vector. Elements are rounded to one decimal place.

Returns
-------
str
    A string representation of the vector with components separated by underscores, where each component is rounded to one decimal place and zero values are represented as '0.0'.
"""
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
"""
Check if two vectors are equal within a given precision.

Parameters
----------
vec1 : array_like
    First vector to compare.
vec2 : array_like
    Second vector to compare.

Returns
-------
bool
    True if the vectors are equal within the specified precision, False otherwise.
"""
#    vec1 = vector(vec1)
#    vec2 = vector(vec2)
#    if vec_length(vec1.array-vec2.array , True) < geom.POINT_PRECISION:
#        return True
#    return False
