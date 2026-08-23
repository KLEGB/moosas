"""experimented module"""
from .geometry.geos import *
from .models import MoosasModel, MoosasSpace, searchBy
import shapely
import numpy as np
from .utils.constant import geom

class Moosasboundary(object):
    def __init__(self,polygon:shapely.Geometry):
        """
        Initialize the object with a polygon geometry and compute transformed edges based on angular thresholds.
        
        Parameters
        ----------
        polygon : shapely.Geometry
            A Shapely geometry object representing a polygon. The polygon's coordinates are used to create edge linestrings
            and apply transformations based on alignment with orthogonal basis vectors.
        
        Returns
        -------
        None
            This method initializes instance attributes and does not return any value.
        """
        coordinates = shapely.get_coordinates(polygon)
        self.originalEdge = np.array([shapely.linestrings(coordinates[i:i+2]) for i in range(len(coordinates)-1)])
        self.edgeTransformation = [Transformation2d() for edge in self.originalEdge]

        self.regularEdge = [edge for edge in self.originalEdge]
        edgeVector = [shapely.get_coordinates(edge)[1] - shapely.get_coordinates(edge)[0] for edge in self.regularEdge]
        edgeVector = [Vector(vec).unit().dump for vec in edgeVector]
        lastVector=Projection.findOrthogonalBasis(polygon).axisX[:2]
        for i in range(len(self.regularEdge)):
            verticalVector = np.cross([0, 0, 1], [lastVector[0], lastVector[1], 0])[:2]
            if Vector.parallel(lastVector, edgeVector[i]) or Vector.parallel(verticalVector, edgeVector[i]):
                continue

            # 角度接近0度
            elif np.abs(Vector.dot(lastVector, edgeVector[i]))>np.cos(geom.REGULATION_ANGEL_THRESHOLD):
                self.edgeTransformation[i] = Transformation2d(rotateRadius=self.getRadius(lastVector, edgeVector[i]))

            #角度接近90度
            elif np.abs(Vector.dot(lastVector, edgeVector[i])) < np.sin(geom.REGULATION_ANGEL_THRESHOLD):
                self.edgeTransformation[i] = Transformation2d(rotateRadius=self.getRadius(verticalVector, edgeVector[i]))

            # 对边进行变换
            self.regularEdge[i] = self.edgeTransformation[i].transfrom(self.originalEdge[i])
            lastVector = shapely.get_coordinates(self.regularEdge[i])[1] - shapely.get_coordinates(self.regularEdge[i])[0]

    @property
    def regularize(self):
        """
        Regularize the edge by connecting segments.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the `regularEdge` attribute and `connectSegment` method.
        
        Returns
        -------
        object
            The result of connecting the regular edge segment, type depends on `connectSegment` implementation.
        """
        return self.connectSegment(self.regularEdge)

    def connectSegment(self,segments):
        """
        Connect a sequence of line segments into a closed polygon, handling parallel segments.
        
        Parameters
        ----------
        self : object
            The instance of the class containing this method.
        segments : array-like of shapely geometries (LineString)
            A sequence of line segment geometries. Each segment is expected to be a two-point LineString.
        
        Returns
        -------
        shapely.geometry.Polygon
            A closed polygon formed by connecting the input segments, with intersections computed at joints.
            If consecutive segments are parallel, their common vertex is replaced with an intersection point 
            from the previous and current segment to ensure proper closure and geometry continuity.
        """
        coordinates = []
        for i in range(len(segments)):
            veci = shapely.get_coordinates(segments[i])[1] - shapely.get_coordinates(segments[i])[0]
            veci_1 = shapely.get_coordinates(segments[i-1])[1] - shapely.get_coordinates(segments[i-1])[0]
            if Vector.parallel(veci, veci_1):
                coordinates.pop()
                p = shapely.get_coordinates(lineIntersection(segments[i-2],segments[i]))[0]
                coordinates.append(p)
                p = shapely.get_coordinates(segments[i])[0]
            else:
                p = shapely.get_coordinates(lineIntersection(segments[i - 1], segments[i]))[0]
            coordinates.append(p)
        coordinates.append(coordinates[0])
        return shapely.polygons(coordinates)

    def deRegularize(self,geo:shapely.Geometry):
        """
        De-regularizes a geometry by applying transformation based on a reference regularized polygon.
        
        Parameters
        ----------
        geo : shapely.Geometry
            Input geometry whose coordinate structure is used to compute new edge transformations.
            Must have the same number of coordinates as the original regularized polygon.
        
        Returns
        -------
        shapely.Geometry
            A reconnected geometry formed by transforming and connecting de-regularized edges.
        """
        regularPolygon = self.regularize
        medianOri = shapely.get_coordinates(regularPolygon)
        edgesOri = [medianOri[i+1]-medianOri[i] for i in range(len(medianOri)-1)]
        medianOri = [medianOri[i]+medianOri[i+1]/2 for i in range(len(medianOri)-1)]
        medianNew = shapely.get_coordinates(geo)
        edgesNew = [medianNew[i+1] - medianNew[i] for i in range(len(medianNew) - 1)]
        medianNew = [medianNew[i] + medianNew[i + 1] / 2 for i in range(len(medianNew) - 1)]
        if len(medianNew)!=len(medianOri):
            raise Exception('input geo must have the same number of coordinates to original')
        movement = [ori2-ori1 for ori1,ori2 in zip(medianOri,medianNew)]
        rotation = [self.getRadius(Vector(newEdge).unit().dump, Vector(oriEdge).unit().dump) for newEdge, oriEdge in zip(edgesNew, edgesOri)]
        transform = [Transformation2d(moveVec, radius) for moveVec, radius in zip(movement, rotation)]
        self.deRegularizeEdge = [trans.transfrom(edge) for trans,edge in zip(transform,self.originalEdge)]
        return self.connectSegment(self.deRegularizeEdge)



    def getRadius(self,axis, vector):
        """
        Calculate the signed angular radius between a given axis and vector.
        
        Parameters
        ----------
        axis : array-like
            The reference axis direction as a 3D vector. Will be converted to a numpy array.
        vector : array-like
            The input vector as a 3D vector. Will be converted to a numpy array.
        
        Returns
        -------
        float
            The signed angle (in radians) between the axis and vector. Positive if counter-clockwise,
            negative if clockwise when viewed along the [0,0,1] direction.
        """
        axis = np.array(axis)
        vector = np.array(vector)
        # 使轴与线同方向
        if vector.dot(axis, vector) < 0: axis = -axis
        radius = np.arccos(vector.dot(axis, vector))
        # 判断是否顺时针
        vertices = np.cross([0, 0, 1], [axis[0],axis[1], 0])[:2]
        if vector.dot(vertices, vector - axis) < 0:
            radius = -radius
        return radius

    def orthogonalization(self, proj:Projection=None):
        """
        Perform orthogonalization of a polygon boundary by projecting it onto an orthogonal basis and adjusting non-orthogonal edges.
        
        Parameters
        ----------
        proj : Projection, optional
            A projection object defining the coordinate system for orthogonalization. If None, an orthogonal basis is automatically 
            determined from the regularized boundary using `Projection.findOrthogonalBasis`. Default is None.
        
        Returns
        -------
        spliter : list of shapely geometries (LineString)
            A list of splitting lines used to subdivide the input boundary when it cannot be represented as a quadrilateral after 
            orthogonalization. Each LineString connects vertices to reduce the number of boundary points until a quadrilateral is formed.
        """
        boundary = simplify(self.regularize)
        if proj is None:
            proj = Projection.findOrthogonalBasis(boundary)
        # 将boundary投影到坐标系，并整理每条边的点和方向
        edgeProj = proj.toUV(shapely.force_3d(boundary, z=0))
        edgeProjCoordiantes = shapely.get_coordinates(edgeProj)
        edgeProjCoordiantes = [[edgeProjCoordiantes[i], edgeProjCoordiantes[i + 1]] for i in
                                   range(len(edgeProjCoordiantes) - 1)] # 每条边的点，初始为两个（起止点）可扩充为三个（半边化节点转变斜线为正交）
        edgeProjVector = [coorTwin[1] - coorTwin[0] for coorTwin in edgeProjCoordiantes]

        if Vector.parallel(edgeProjVector[-1], [1, 0]) or Vector.parallel(edgeProjVector[-1], [0, 1]):
            lastVector = Vector(edgeProjVector[-1]).unit().array
        else:
            lastVector = np.array([1, 0])

        # 若边非正交边，则将对角点加入点集使该斜边正交化
        for i in range(len(edgeProjVector)):
            if not (Vector.parallel(edgeProjVector[-1], [1, 0]) or Vector.parallel(edgeProjVector[-1], [0, 1])):
                poi0 = np.array([edgeProjCoordiantes[i][0][0], edgeProjCoordiantes[i][1][1]])
                poi1 = np.array([edgeProjCoordiantes[i][1][0], edgeProjCoordiantes[i][0][1]])
                if Vector.parallel(poi0 - edgeProjCoordiantes[i][0], lastVector):
                    edgeProjCoordiantes[i] = [edgeProjCoordiantes[i][0], poi0, edgeProjCoordiantes[i][1]]
                    lastVector = Vector(poi0 - edgeProjCoordiantes[i][0]).unit().array
                else:
                    edgeProjCoordiantes[i] = [edgeProjCoordiantes[i][0], poi1, edgeProjCoordiantes[i][1]]
                    lastVector = Vector(poi1 - edgeProjCoordiantes[i][0]).unit().array
        coordinates = [coor for edge in edgeProjCoordiantes for coor in edge[:-1]]
        coordinates.append(coordinates[0])
        boundary = simplify(shapely.polygons(coordinates))
        coordinates = shapely.get_coordinates(boundary)
        # 当最简化图形非四边形时切割图形
        spliter = []
        while len(coordinates)>5:
            spliter.append(shapely.linestrings([coordinates[0], coordinates[-4]]))
            coordinates=list(coordinates[:-3])
            coordinates.append(coordinates[0])
            print('???',coordinates)

            boundary = simplify(shapely.polygons(coordinates))
            print(boundary)
            coordinates = shapely.get_coordinates(boundary)
        return spliter

def encodingModel(model: MoosasModel):
    """
    Apply encoding process to the model by standardizing spaces and regularizing boundaries.
    
    Parameters
    ----------
    model : MoosasModel
        The input model containing levels, spaces, and associated geometric data to be processed.
    
    Returns
    -------
    MoosasModel
        The input model after processing each space by standardization and boundary regularization.
    """
    for buildingLevel in model.levelList:
        spaces = np.array(model.spaceList)[searchBy('level', buildingLevel, model.spaceList)]
        for space in spaces:
            space = standarizeSpace(space)
            edge = space.edge.force_2d()
            boundary = Moosasboundary(edge)
            edge = boundary.regularize

    return model


def standarizeSpace(space: MoosasSpace):
    """
    Standardize the given space object.
    
    Parameters
    ----------
    space : MoosasSpace
        The space object to be standardized.
    
    Returns
    -------
    MoosasSpace
        The standardized space object.
    """
    return space
