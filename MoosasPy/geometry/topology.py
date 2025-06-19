from __future__ import annotations

from .geos import *
from .element import MoosasWall
from ..utils.constant import geom
from ..utils import searchBy, TopologyError,copy


class TopoEdge(object):
    __slots__ = ('modelId', 'fromLocation', 'toLocation', 'uid', 'fromP', 'toP')

    def __init__(self, idd, edge: MoosasWall):
        self.modelId = idd
        line2d = edge.force_2d()
        self.fromLocation = pygeos.set_precision(pygeos.get_point(line2d, 0), geom.POINT_PRECISION)
        self.toLocation = pygeos.set_precision(pygeos.get_point(line2d, 1), geom.POINT_PRECISION)
        self.uid = edge.Uid
        self.fromP: TopoNode | None = None
        self.toP: TopoNode | None = None

    @property
    def valid(self):
        if self.fromLocation is None or self.toLocation is None:
            return False
        if pygeos.dwithin(self.fromLocation, self.toLocation, geom.POINT_PRECISION):
            return False
        return True

    @property
    def fromPStr(self):
        return '_'.join(pygeos.get_coordinates(self.fromLocation)[0].astype(str))

    @property
    def toPStr(self):
        return '_'.join(pygeos.get_coordinates(self.toLocation)[0].astype(str))

    @staticmethod
    def overlap(this: TopoEdge, other: TopoEdge):
        if pygeos.dwithin(this.fromLocation, other.fromLocation, geom.POINT_PRECISION) or pygeos.dwithin(
                this.fromLocation, other.toLocation,
                geom.POINT_PRECISION):
            if pygeos.dwithin(this.toLocation, other.fromLocation, geom.POINT_PRECISION) or pygeos.dwithin(
                    this.toLocation, other.toLocation,
                    geom.POINT_PRECISION):
                return True
        return False

    @staticmethod
    def isolateEdge(edge_list: Iterable[TopoEdge]):
        nodeList = {}
        for i, edge in enumerate(edge_list):
            fromP = edge.fromPStr
            toP = edge.toPStr
            if fromP in nodeList:
                nodeList[fromP].append(i)
            else:
                nodeList[fromP] = [i]
            if toP in nodeList:
                nodeList[toP].append(i)
            else:
                nodeList[toP] = [i]

        delEdges = []
        for i, edge in enumerate(edge_list):
            fromP = edge.fromPStr
            toP = edge.toPStr
            if len(nodeList[fromP]) < 2 or len(nodeList[toP]) < 2:
                delEdges.append(i)
        return delEdges

    def __str__(self):
        return f"EdgeId {self.modelId} from {self.fromP} to {self.toP}"


class TopoNode(object):
    __slots__ = ('idd', 'connectedEdges', 'neighbor', 'neiAngle', 'location')

    def __init__(self, idd, location: pygeos.Geometry):
        self.idd = idd
        self.location = location
        self.neighbor: list[TopoNode] = []
        self.neiAngle: list[float] = []
        self.connectedEdges: list[TopoEdge] = []

    def sortNeighbor(self):
        """sort the neighbor according to their angle to x-axis"""
        argsort = np.argsort(self.neiAngle)
        self.neighbor = list(np.array(self.neighbor)[argsort])
        self.neiAngle = list(np.array(self.neiAngle)[argsort])
        self.connectedEdges = list(np.array(self.connectedEdges)[argsort])

    def __repr__(self):
        return "N" + self.idd.__repr__()


class TopoNetwork(object):
    __slots__ = ('edges', 'nodes')

    def __init__(self, edges=None, nodes=None):
        """initialize the network:
            get 2 things recording the topology of the network:
            self.edges:list[TopoEdge] records the edges' id and their end points' location
            self.nodes:list[TopoNode] records all unique nodes (end points).
                These topoNodes have 4 contents:
                the unique id to find them in the self.nodes,
                a list of the neighbors as list[TopoNode],
                a list of the edges' id in the same sequence which connect to the neighbors,
                a list of the angle between node's neighbor and itself, presented as the dot value of the vector to x-axis.

            This method will run _nodeFromEdges or _EdgeFromNodes automatically according to which list is given.
            """
        self.edges: list[TopoEdge] = edges
        self.nodes: list[TopoNode] = nodes

        if self.edges is None and self.nodes is not None:
            self._edgeFromNode()

        elif self.edges is not None and self.nodes is None:
            self._nodeFromEdge()

    # function to initialize TopoEdge list

    # function to initialize TopoNode list
    def _nodeFromEdge(self) -> None:
        """construct the nodeList(self.nodes)
        1. find the unique nodes from all TopoEdges, and put the neighbor of the nodes in TopoNode.neighbor
        2. get the locations of that unique nodes,
        3. calculate the angle between the vector of neighbors to nodes and x-axis.
        """

        """zero length edges"""
        edges = [topoedge for topoedge in self.edges if topoedge.valid]
        """duplicate edges"""
        delEdges = []
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                if TopoEdge.overlap(edges[i], edges[j]):
                    delEdges.append(i)
                    break
        edges = np.delete(edges, delEdges)
        # plot_object([model.wallList[edge.id] for edge in edge_list], color='black')

        """blur match existing locations and the edge nodes"""
        location = set()
        for edge in edges:
            if edge.fromLocation not in location:
                for poi in location:
                    if pygeos.dwithin(edge.fromLocation, poi, 1.1 * geom.POINT_PRECISION):
                        edge.fromLocation = poi
                        break
                location.add(edge.fromLocation)

            if edge.toLocation not in location:
                for poi in location:
                    if pygeos.dwithin(edge.toLocation, poi, 1.1 * geom.POINT_PRECISION):
                        edge.toLocation = poi
                        break
                location.add(edge.toLocation)

        """double check zero length edges"""
        edges = [topoedge for topoedge in edges if topoedge.valid]

        """isolate edges"""
        edge_list_len = 0
        while edge_list_len != len(edges):
            edge_list_len = len(edges)
            delEdges = TopoEdge.isolateEdge(edges)
            edges = np.delete(edges, delEdges)
            # plot_object([model.wallList[edge.id] for edge in edge_list], color='black')

        # generate node network
        self.edges = edges
        self.nodes: list[TopoNode] = []
        # 1. find the unique nodes from all TopoEdges, and put the neighbor of the nodes in TopoNode.neighbor
        uniqueNodeDict = {}
        location = {}

        for edge in self.edges:

            if edge.fromPStr in uniqueNodeDict:
                uniqueNodeDict[edge.fromPStr].append(edge)
            else:
                uniqueNodeDict[edge.fromPStr] = [edge]
                location[edge.fromPStr] = edge.fromLocation
            if edge.toPStr in uniqueNodeDict:
                uniqueNodeDict[edge.toPStr].append(edge)
            else:
                uniqueNodeDict[edge.toPStr] = [edge]
                location[edge.toPStr] = edge.toLocation

        for i, node in enumerate(list(location.keys())):
            self.nodes.append(TopoNode(i, location[node]))
            self.nodes[-1].connectedEdges = uniqueNodeDict[node]

        # 2. get the locations of that unique nodes,
        locationList = [node.location for node in self.nodes]
        for edge in self.edges:
            fromIdx = locationList.index(edge.fromLocation)
            toIdx = locationList.index(edge.toLocation)
            self.nodes[fromIdx].neighbor.append(self.nodes[toIdx])
            self.nodes[toIdx].neighbor.append(self.nodes[fromIdx])
            edge.fromP = self.nodes[fromIdx]
            edge.toP = self.nodes[toIdx]

        # 3. calculate the angle between the vector of neighbors to nodes and x-axis.
        for node in self.nodes:
            for other in node.neighbor:
                vec = Vector(other.location).array - Vector(node.location).array
                node.neiAngle.append(Vector(vec).quickAngle())
            node.sortNeighbor()

        return

    def _edgeFromNode(self) -> None:
        """Extract unique edge list from node.edgeId"""
        edges: set[TopoEdge] = set()
        for node in self.nodes:
            for edge in node.connectedEdges:
                edges.add(edge)

        self.edges = list(edges)

    @classmethod
    def inLevel(cls, bld_level: float, model) -> TopoNetwork:
        """clean zero, duplicate and isolated edge in the edge list,
        then build a list[TopoEdge] to record these edge for next step.
        This list will construct a TopoNetwork.

        ---------------------------------
        bld_level: building level to retrieve in float
        model: get topoEdge from this model

        return: TopoNetwork with select edges
        """
        edge_list = searchBy('level', bld_level, model.wallList)
        if len(edge_list) == 0:
            return TopoNetwork()
        edge_list = [i for i in edge_list if model.wallList[i].force_2d() != None]
        edge_list = [i for i in edge_list if model.wallList[i].height > 0.9]
        edges = [TopoEdge(i, model.wallList[i]) for i in edge_list]

        return TopoNetwork(edges=edges)

    @classmethod
    def splitNetwork(cls, oriNetwork: TopoNetwork) -> list[TopoNetwork]:
        """split the network into several isolate part
        this method can be improved consider the stability facing strange network,
        especially those with self-interest part
        """

        eligible = np.array([node for node in oriNetwork.nodes if len(node.neighbor) > 1])
        eligible = list(eligible)
        groups = []
        while len(eligible) > 0:
            nodeInGroup = []

            def _findItemBreadth(node: TopoNode):
                """Recursive Breadth-first search method to find all connected node to the target node

                    ---------------------------------------------
                    node: target node
                    avoidPoint: optional nodes that don't want to add in the group
                    nodeInGroup: please leave blank for this argument
                    max_depth: maximum iteration to avoid collapse

                    return: list[TopoNode] target nodes which are connected together
                """
                if node in nodeInGroup: return False
                if not (node in eligible): return False
                nodeInGroup.append(node)
                for nei in node.neighbor:
                    _findItemBreadth(nei)
                return True

            _findItemBreadth(eligible[0])

            groupIndex = [list(eligible).index(item) for item in nodeInGroup]
            groups.append(nodeInGroup)
            eligible = np.delete(eligible, groupIndex)
            eligible = list(eligible)

        return [cls(nodes=nodes) for nodes in groups]

    def outerBoundary(self) -> list[TopoBound]:
        """calculate the outer boundary(s) of this network
        sometime it will have several boundaries instead of one
        when the outer boundary is self-interest.
        """
        boundary_list: list[TopoBound] = []
        """find the extreme node in max x and min y as the start node
        group_xy list: the node, node.location.x, node.location.y
        """
        if len(self.nodes)<3:
            return []
        group = self.nodes

        group_xy = np.append(np.arange(len(group)).reshape(len(group), 1),
                             pygeos.get_coordinates([node.location for node in group]), axis=1)

        # group_xy = np.array([[node, pygeos.get_x(node.location), pygeos.get_y(node.location)] for node in group])
        max_x = np.max(group_xy[:, 1])

        group_xy = group_xy[[i for i in range(len(group)) if group_xy[i][1] == max_x]]

        start_node: TopoNode = group[group_xy[np.argmin(group_xy.T[2])][0].astype(int)]
        end_node: TopoNode = start_node.neighbor[0]
        """the boundary start with the start node and its first neighbor"""
        bound: list[TopoNode] = [start_node, end_node]
        is_valid = True

        """start iteration: find next node until the outer_boundary is close"""
        # Ver1.3: to avoid circular traverse, we should record all selection in the boundary

        nextNodeDict = {}
        while bound[-1] != bound[0] and is_valid:
            # calculate the vector come from outer_boundary[-2]
            vec_last = Vector(bound[-2].location).array - Vector(bound[-1].location).array

            # find the clockwise first node of outer_boundary[-1], except for outer_boundary[-2]
            next_node = bound[-1].neighbor[0]
            if bound[-1].neighbor[0] == bound[-2]:
                next_node = bound[-1].neighbor[1]

            for i in range(len(bound[-1].neighbor)):
                if bound[-1].neighbor[i] != bound[-2]:
                    if bound[-1].neiAngle[i] > Vector(vec_last).quickAngle():
                        if bound[-1].idd in nextNodeDict.keys():
                            # Ver1.3: to avoid circular traverse, we should record all selection in the boundary
                            if bound[-1].neighbor[i].idd == nextNodeDict[bound[-1].idd]:
                                continue
                        # yes! it is you!!!
                        next_node = bound[-1].neighbor[i]
                        # Ver1.3: to avoid circular traverse, we should record all selection in the boundary
                        nextNodeDict[bound[-1].idd] = next_node.idd
                        break

            bound.append(next_node)

            print('\rOuter boundary iteration:' + str(len(bound)), end='')
            if len(bound) > 10000:
                print()
                print('******Warning: TopologyError, outerBoundary iteration collapsed. Dump the group')
                print(next_node.location)
                is_valid = False

        """Ver1.3 check and break on the self intersection point"""
        if is_valid:
            outerBound = TopoBound(bound)
            boundary_list = TopoBound.selfIntersect(outerBound)

        return boundary_list


class TopoBound(object):
    __slots__ = ('nodeLoop', 'edgeLoop')

    def __init__(self, nodes: list[TopoNode] = None, edges: list[TopoEdge] = None):
        self.nodeLoop = list(nodes) if nodes is not None else None
        self.edgeLoop = list(edges) if edges is not None else None
        if nodes is not None and edges is None:
            self.initEdgeLoop()
        elif nodes is None and edges is not None:
            self.initNodeLoop()

    def initEdgeLoop(self):
        """extract the edges from nodeLoop"""
        self.edgeLoop: list[TopoEdge] = []
        for i in range(len(self.nodeLoop) - 1):
            neiIdx = self.nodeLoop[i].neighbor.index(self.nodeLoop[i + 1])
            self.edgeLoop.append(self.nodeLoop[i].connectedEdges[neiIdx])

    def initNodeLoop(self):
        self.nodeLoop = []
        """open nodeLoop"""
        for edge in self.edgeLoop:
            if edge.fromP not in self.nodeLoop:
                self.nodeLoop.append(edge.fromP)
            if edge.toP not in self.nodeLoop:
                self.nodeLoop.append(edge.toP)
        """decide which is the start point"""
        if self.nodeLoop[0] == self.edgeLoop[1].fromP or self.nodeLoop[0] == self.edgeLoop[1].toP:
            temp = self.nodeLoop[0]
            self.nodeLoop[0] = self.nodeLoop[1]
            self.nodeLoop[1] = temp
        """test if the edgeLoop is closed: if the len of set < 4, the loop is closed"""
        if len({self.edgeLoop[-1].fromP, self.edgeLoop[-1].toP, self.edgeLoop[0].fromP, self.edgeLoop[0].toP}) != 4:
            self.nodeLoop.append(self.nodeLoop[0])

    def reverse(self):
        """reverse boundary"""
        self.nodeLoop.reverse()
        self.edgeLoop.reverse()

    @classmethod
    def fromTopoEdge(cls, edge: TopoEdge):
        return cls(nodes=[edge.fromP, edge.toP], edges=[edge])

    def isClose(self):
        """whether the loop is close?"""
        return self.nodeLoop[0] == self.nodeLoop[-1]

    def coveredBy(self, other: TopoBound) -> bool:
        """test if this boundary share same topology with others"""
        for edge in self.edgeLoop:
            if edge not in other.edgeLoop:
                return False
        return True

    def connect(self, other: TopoBound) -> int:
        """test if this boundary connected to others"""
        if len({node for node in self.nodeLoop} & {node for node in other.nodeLoop}) >= 2:
            return True
        return False

    @property
    def geometry(self):
        """get the polygon or linestring from the nodeLoop"""
        loc = pygeos.get_coordinates([node.location for node in self.nodeLoop])
        if self.isClose():
            return pygeos.polygons(loc)
        else:
            return pygeos.linestrings(loc)

    def __repr__(self):
        return " ".join([node.__repr__() for node in self.nodeLoop])

    @classmethod
    def split(cls, oriBoundary: TopoBound, splitLinestring: TopoBound) -> (TopoBound, TopoBound):
        """split the boundary by another spliter"""
        oriNodeLoop = list(copy.copy(oriBoundary.nodeLoop))

        if oriBoundary.isClose():
            oriNodeLoop.pop()
        # print(oriNodeLoop,oriBoundary.nodeLoop)
        if splitLinestring.isClose():
            return oriBoundary,splitLinestring
            # raise GeometryError(splitLinestring.geometry, 'invalid spliter: the split line should not be closed')

        if splitLinestring.nodeLoop[0] not in oriNodeLoop or splitLinestring.nodeLoop[-1] not in oriNodeLoop:
            raise TopologyError(split, "incompleted spliter")
        breakPoint1 = oriNodeLoop.index(splitLinestring.nodeLoop[0])
        breakPoint2 = oriNodeLoop.index(splitLinestring.nodeLoop[-1])

        linerRing1, linerRing2 = [], []
        if breakPoint2 > breakPoint1:
            linerRing1 = splitLinestring.nodeLoop + oriNodeLoop[breakPoint2 + 1:] + oriNodeLoop[:breakPoint1 + 1]
            splitLinestring.nodeLoop.reverse()
            linerRing2 = splitLinestring.nodeLoop + oriNodeLoop[breakPoint1 + 1:breakPoint2 + 1]

        else:
            linerRing1 = splitLinestring.nodeLoop + oriNodeLoop[breakPoint2 + 1:breakPoint1 + 1]
            splitLinestring.nodeLoop.reverse()
            linerRing2 = splitLinestring.nodeLoop + oriNodeLoop[breakPoint1 + 1:] + oriNodeLoop[
                                                                                             :breakPoint2 + 1]

        return cls(linerRing1), cls(linerRing2)

    # Ver1.3 break the self intersection point
    @classmethod
    def selfIntersect(cls, oriBoundary) -> list[TopoBound]:
        """check the boundary if self intersect, and break it on the intersect point(s)
        the main part (start with self.nodeLoop[0]) will be located in validBound[-1]
        this method can work with both closed and open linestring.
        """
        validBound = []
        bound = oriBoundary.nodeLoop
        while len(bound) > 0:
            sub_boundary: list[TopoNode] = []
            break_point = 0
            end_point = len(bound) - 1

            for i in range(len(bound)):
                # find the breakPoint
                if bound[i] in bound[0:i]:
                    break_point = bound.index(bound[i])  # index() method will return the first item of bound[i]
                    end_point = i
                    sub_boundary = bound[break_point:end_point + 1]
                    break
            if len(sub_boundary) > 2:
                validBound.append(sub_boundary)
            else:
                validBound.append(bound)
            if end_point == len(bound) - 1:
                break
            else:
                bound = bound[0:break_point] + bound[end_point:]

        return [cls(bound) for bound in validBound]
