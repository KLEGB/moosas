import numpy as np
import pygeos
from .element import MoosasElement
from .geos import Ray, Vector, Projection, faceNormal


class MoosasGrid(MoosasElement):
    __slots__ = ['gridSize', 'gridOffset', 'gridCell', 'params','proj','UVFace']

    def __init__(self, element: MoosasElement, gird_size=None, grid_offset=0.78):
        super(MoosasGrid, self).__init__(element.faceId, element.parent,
                                         element.level, element.offset, element.glazingId, element.space)

        self.griding(gird_size, grid_offset)

    def griding(self, grid_size=None, grid_offset=0.78):
        """
        Create grid points and grid polygons based on grid size and grid offset.
        The grid will be built on UV face, then transform back to world.
        The projection is built by Projection.fromPolygon() method.
        Polygons will be squares and will be trim on the edge.
        """
        # Create projection for the face
        self.proj = Projection.fromPolygon(self.face)
        self.UVFace = self.proj.toUV(self.face)
        bbox = pygeos.bounds(self.UVFace)
        if grid_size is None:
            grid_size = max(bbox[2]- bbox[2],bbox[3]- bbox[1])/5
        self.gridSize = grid_size
        self.gridOffset = grid_offset

        z = self.level + self.offset + self.gridOffset

        # Generate grid point as a array of Ray object
        self.gridCell = []
        for i, x in enumerate(np.arange(bbox[0], bbox[2], self.gridSize)):
            self.gridCell.append([])
            for j, y in enumerate(np.arange(bbox[1], bbox[3], self.gridSize)):
                position = MoosasGridCell(
                    origin=Vector([x, y, z]),
                    direction=Vector(self.normal),
                    valid=pygeos.contains(self.UVFace, pygeos.points([x, y]))
                )
                self.gridCell[i].append(position)
        self.gridCell = np.array(self.gridCell)

    @property
    def gridPoints(self):
        projPts = [self.proj.toWorld(cell.origin.geometry)  for cellLine in self.gridCell for cell in cellLine]
        maskPts = [cell.valid for cellLine in self.gridCell for cell in cellLine]
        return np.array(projPts)[maskPts]

    @property
    def mask(self):
        return [[cell.valid for cell in cellLine] for cellLine in self.gridCell]
    @property
    def gridPolygon(self):
        # Generate grid polygons using the grid points as centers
        for rowIdx, row in enumerate(self.gridCell):
            bound = False
            for colIdx, col in enumerate(self.gridCell[rowIdx]):
                if self.gridCell[rowIdx, colIdx].valid:
                    center = self.gridCell[rowIdx, colIdx].origin.array
                    poly = pygeos.polygons([
                        [center[0] - 0.5 * self.gridSize, center[1] - 0.5 * self.gridSize],
                        [center[0] - 0.5 * self.gridSize, center[1] + 0.5 * self.gridSize],
                        [center[0] + 0.5 * self.gridSize, center[1] + 0.5 * self.gridSize],
                        [center[0] + 0.5 * self.gridSize, center[1] - 0.5 * self.gridSize],
                        [center[0] - 0.5 * self.gridSize, center[1] - 0.5 * self.gridSize]
                    ])

                    # Trim the grid polygons on the edges
                    if self.gridCell[rowIdx, colIdx].valid != bound:
                        poly = pygeos.intersection(self.UVFace, poly)
                        bound = self.gridCell[rowIdx, colIdx].valid

                    self.gridCell[rowIdx, colIdx].polygon = self.proj.toWorld(pygeos.force_3d(poly, z=0))
        return self.gridCell


class MoosasGridCell(Ray):
    __slots__ = ['valid', 'polygon']

    def __init__(self, origin, direction, value=None, valid=False, polygon=None):
        super(MoosasGridCell, self).__init__(origin, direction, value)
        self.valid = valid
        self.polygon = polygon

    def flipPolygon(self):
        if self.polygon is None:
            return
        normal = faceNormal(self.polygon)
        dot = Vector.dot(normal, self.direction)
        if dot < -1 + Vector.ANGLE_TOLERANCE:
            self.polygon = pygeos.reverse(self.polygon)
