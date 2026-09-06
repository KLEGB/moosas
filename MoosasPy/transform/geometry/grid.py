import numpy as np
import shapely
from .element import MoosasElement
from .geos import Ray, Vector, Projection, faceNormal


class MoosasGrid(MoosasElement):
    __slots__ = ['gridSize', 'gridOffset', 'gridCell', 'params','proj','UVFace']

    def __init__(self, element: MoosasElement, gird_size=None, grid_offset=0.78):
        """
        Initialize a MoosasGrid instance with element properties and apply grid configuration.
        
        Parameters
        ----------
        element : MoosasElement
            The element object containing parent, faceId, level, offset, glazingId, space attributes.
        gird_size : float or None, optional
            Size of the grid cells. If None, a default or internal logic is used. Default is None.
        grid_offset : float, optional
            Offset value for grid positioning. Default is 0.78.
        
        Returns
        -------
        None
        """
        super(MoosasGrid, self).__init__(element.parent,element.faceId,
                                         element.level, element.offset, element.glazingId, element.space)

        self.griding(gird_size, grid_offset)

    def griding(self, grid_size=None, grid_offset=0.78):
        """
        Create grid points and grid polygons based on specified grid size and offset.
        
        Parameters
        ----------
        grid_size : float, optional
            The size of each grid cell. If None, it is automatically calculated as one-fifth 
            of the maximum bounding box dimension of the UV-projected face. Default is None.
        grid_offset : float, default=0.78
            The offset value added to the z-coordinate (level + offset + grid_offset) 
            to position the grid in 3D space. Default is 0.78.
        
        Returns
        -------
        None
            This function does not return a value. It modifies the instance attributes:
            `proj`, `UVFace`, `gridSize`, `gridOffset`, and `gridCell`, where `gridCell` 
            is a 2D numpy array of `MoosasGridCell` objects representing the generated grid.
        """
        """
        Create grid points and grid polygons based on grid size and grid offset.
        The grid will be built on UV face, then transform back to world.
        The projection is built by Projection.fromPolygon() method.
        Polygons will be squares and will be trim on the edge.
        """
        # Create projection for the face
        face_geometry = self.face
        if isinstance(face_geometry, np.ndarray):
            face_parts = [geo for geo in face_geometry if shapely.get_dimensions(geo) == 2]
            if len(face_parts) == 0:
                raise ValueError(f"No valid polygon face found for grid generation: {self.faceId}")
            # Use the dominant polygon to avoid costly unions on fragmented faces.
            face_geometry = max(face_parts, key=shapely.area)
        self.proj = Projection.fromPolygon(face_geometry)
        self.UVFace = self.proj.toUV(face_geometry)
        bbox = shapely.bounds(self.UVFace)
        if grid_size is None:
            grid_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 5
        self.gridSize = grid_size
        self.gridOffset = grid_offset

        z = self.gridOffset

        # Generate grid point as a array of Ray object
        self.gridCell = []
        for i, x in enumerate(np.arange(bbox[0], bbox[2], self.gridSize)):
            self.gridCell.append([])
            for j, y in enumerate(np.arange(bbox[1], bbox[3], self.gridSize)):
                position = MoosasGridCell(
                    origin=Vector([x, y, z]),
                    direction=Vector(self.normal),
                    valid=shapely.contains(self.UVFace, shapely.points([x, y]))
                )
                self.gridCell[i].append(position)
        self.gridCell = np.array(self.gridCell)

    @property
    def gridPoints(self):
        """
        Return valid grid points in world coordinates as a NumPy array.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the grid structure and projection.
            Must have a `gridCell` attribute (list of lists of cells) where each cell
            has an `origin.geometry` and a `valid` attribute, and a `proj` attribute
            with a `toWorld` method to transform coordinates.
        
        Returns
        -------
        numpy.ndarray
            An array of valid grid points transformed to world coordinates,
            filtered by the `valid` mask.
        """
        projPts = [self.proj.toWorld(cell.origin.geometry)  for cellLine in self.gridCell for cell in cellLine]
        maskPts = [cell.valid for cellLine in self.gridCell for cell in cellLine]
        return np.array(projPts)[maskPts]

    @property
    def mask(self):
        """
        Return a 2D mask of boolean values indicating the validity of each cell in the grid.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `gridCell` attribute. This should be an object 
            with a `gridCell` property that is a 2D list (or similar structure) of cell objects, 
            where each cell has a `valid` attribute.
        
        Returns
        -------
        list of list of bool
            A 2D list with the same dimensions as `self.gridCell`, where each element is a boolean 
            indicating whether the corresponding cell is valid (`True`) or not (`False`).
        """
        return [[cell.valid for cell in cellLine] for cellLine in self.gridCell]
    @property
    def gridPolygon(self):
        """
        Generate grid polygons from valid grid cells and assign them to the gridCell array.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the gridCell attribute, gridSize, UVFace, 
            proj, and other related properties. It is assumed that `gridCell` is a 2D array 
            of `MoosasGridCell` objects, each having `valid`, `origin`, and `polygon` attributes.
        
        Returns
        -------
        gridCell : numpy.ndarray
            A 2D array of `MoosasGridCell` objects with updated `polygon` attributes, where each 
            valid cell contains a 3D polygon (shapely geometry) in world coordinates, generated 
            from the cell's origin and trimmed by the UVFace if on the boundary.
        """
        # Generate grid polygons using the grid points as centers
        for rowIdx, row in enumerate(self.gridCell):
            bound = False
            for colIdx, col in enumerate(self.gridCell[rowIdx]):
                if self.gridCell[rowIdx, colIdx].valid:
                    center = self.gridCell[rowIdx, colIdx].origin.array
                    poly = shapely.polygons([
                        [center[0] - 0.5 * self.gridSize, center[1] - 0.5 * self.gridSize],
                        [center[0] - 0.5 * self.gridSize, center[1] + 0.5 * self.gridSize],
                        [center[0] + 0.5 * self.gridSize, center[1] + 0.5 * self.gridSize],
                        [center[0] + 0.5 * self.gridSize, center[1] - 0.5 * self.gridSize],
                        [center[0] - 0.5 * self.gridSize, center[1] - 0.5 * self.gridSize]
                    ])

                    # Trim the grid polygons on the edges
                    if self.gridCell[rowIdx, colIdx].valid != bound:
                        poly = shapely.intersection(self.UVFace, poly)
                        bound = self.gridCell[rowIdx, colIdx].valid

                    self.gridCell[rowIdx, colIdx].polygon = self.proj.toWorld(shapely.force_3d(poly, z=0))
        return self.gridCell


class MoosasGridCell(Ray):
    __slots__ = ['valid', 'polygon']

    def __init__(self, origin, direction, value=None, valid=False, polygon=None):
        """
        Initialize a MoosasGridCell instance.
        
        Parameters
        ----------
        origin : array-like
            The origin point of the grid cell.
        direction : array-like
            The direction vector associated with the grid cell.
        value : float or None, optional
            The value assigned to the grid cell. Default is None.
        valid : bool, optional
            Flag indicating whether the grid cell is valid. Default is False.
        polygon : Polygon or None, optional
            Geometric polygon representing the grid cell's shape. Default is None.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        super(MoosasGridCell, self).__init__(origin, direction, value)
        self.valid = valid
        self.polygon = polygon

    def flipPolygon(self):
        """
        Flip the orientation of the polygon if its normal is opposite to the given direction.
        
        Parameters
        ----------
        self : object
            The instance containing the polygon and direction attributes.
            self.polygon : shapely geometry or None
                The polygon to be flipped; modified in place if conditions are met.
            self.direction : numpy.ndarray or similar vector-like
                Direction vector used for comparison with the polygon's normal.
            self.ANGLE_TOLERANCE : float
                Tolerance value for angle comparison, typically defined in Vector class.
        
        Returns
        -------
        None
            This function does not return a value; it modifies the polygon in place.
        """
        if self.polygon is None:
            return
        normal = faceNormal(self.polygon)
        dot = Vector.dot(normal, self.direction)
        if dot < -1 + Vector.ANGLE_TOLERANCE:
            self.polygon = shapely.reverse(self.polygon)
