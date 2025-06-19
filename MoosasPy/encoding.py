"""experimented module"""
from .geometry.geos import *
from .models import MoosasModel, MoosasSpace, searchBy
import pygeos
import numpy as np
from pythonDist.MoosasPy.utils.constant import geom

class Moosasboundary(object):
    def __init__(self,polygon:pygeos.Geometry):
        coordinates = pygeos.get_coordinates(polygon)
        self.originalEdge = np.array([pygeos.linestrings(coordinates[i:i+2]) for i in range(len(coordinates)-1)])
        self.edgeTransformation = [Transformation2d() for edge in self.originalEdge]

        self.regularEdge = [edge for edge in self.originalEdge]
        edgeVector = [pygeos.get_coordinates(edge)[1] - pygeos.get_coordinates(edge)[0] for edge in self.regularEdge]
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
            lastVector = pygeos.get_coordinates(self.regularEdge[i])[1] - pygeos.get_coordinates(self.regularEdge[i])[0]

    @property
    def regularize(self):
        return self.connectSegment(self.regularEdge)

    def connectSegment(self,segments):
        coordinates = []
        for i in range(len(segments)):
            veci = pygeos.get_coordinates(segments[i])[1] - pygeos.get_coordinates(segments[i])[0]
            veci_1 = pygeos.get_coordinates(segments[i-1])[1] - pygeos.get_coordinates(segments[i-1])[0]
            if Vector.parallel(veci, veci_1):
                coordinates.pop()
                p = pygeos.get_coordinates(lineIntersection(segments[i-2],segments[i]))[0]
                coordinates.append(p)
                p = pygeos.get_coordinates(segments[i])[0]
            else:
                p = pygeos.get_coordinates(lineIntersection(segments[i - 1], segments[i]))[0]
            coordinates.append(p)
        coordinates.append(coordinates[0])
        return pygeos.polygons(coordinates)

    def deRegularize(self,geo:pygeos.Geometry):
        regularPolygon = self.regularize
        medianOri = pygeos.get_coordinates(regularPolygon)
        edgesOri = [medianOri[i+1]-medianOri[i] for i in range(len(medianOri)-1)]
        medianOri = [medianOri[i]+medianOri[i+1]/2 for i in range(len(medianOri)-1)]
        medianNew = pygeos.get_coordinates(geo)
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
        boundary = simplify(self.regularize)
        if proj is None:
            proj = Projection.findOrthogonalBasis(boundary)
        # 将boundary投影到坐标系，并整理每条边的点和方向
        edgeProj = proj.toUV(pygeos.force_3d(boundary, z=0))
        edgeProjCoordiantes = pygeos.get_coordinates(edgeProj)
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
        boundary = simplify(pygeos.polygons(coordinates))
        coordinates = pygeos.get_coordinates(boundary)
        # 当最简化图形非四边形时切割图形
        spliter = []
        while len(coordinates)>5:
            spliter.append(pygeos.linestrings([coordinates[0], coordinates[-4]]))
            coordinates=list(coordinates[:-3])
            coordinates.append(coordinates[0])
            print('???',coordinates)

            boundary = simplify(pygeos.polygons(coordinates))
            print(boundary)
            coordinates = pygeos.get_coordinates(boundary)
        return spliter

def encodingModel(model: MoosasModel):
    for buildingLevel in model.levelList:
        spaces = np.array(model.spaceList)[searchBy('level', buildingLevel, model.spaceList)]
        for space in spaces:
            space = standarizeSpace(space)
            edge = space.edge.force_2d()
            boundary = Moosasboundary(edge)
            edge = boundary.regularize

    return model


def standarizeSpace(space: MoosasSpace):
    return space
