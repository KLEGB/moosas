"""Ver0.4.3.3 new contour calculation module, more serious and stable"""
from __future__ import annotations

from .geos import *
from .element import MoosasEdge, MoosasWall, MoosasGlazing, MoosasContainer
from .triangulation import triangulate2dFace
from ...utils import searchBy, shapely, np, TopologyError, mixItemListToList
from ...utils.constant import geom
from .planar_graph import TopoNode, TopoBound, TopoEdge, TopoNetwork


def _findPathDepth(node: TopoNode, exitPoint: list[TopoNode],
                   avoidPoint: list[TopoNode] = None, avoidEdge: list[TopoBound] = None,
                   max_depth=geom.PATH_MAX_DEPTH) -> list[TopoNode]:
    """
    Recursive Depth-first search to find a valid path from node to exit points.
    
    Parameters
    ----------
    node : TopoNode
        The starting node for the search.
    exitPoint : list of TopoNode
        List of target exit nodes to reach.
    avoidPoint : list of TopoNode, optional
        Nodes to exclude from the search (default is None, treated as empty list).
    avoidEdge : list of TopoBound, optional
        Edges to avoid traversing; if a connection between two nodes lies on one of these edges, it will be skipped (default is None, treated as empty list).
    max_depth : int, default=geom.PATH_MAX_DEPTH
        Maximum recursion depth allowed to prevent infinite traversal.
    
    Returns
    -------
    list of TopoNode
        A list of nodes representing the path from the input node to an exit point, including both ends. Returns empty list if no path is found.
    """
    """Recursive Depth-first search method to find a valid connection from the target node to the exit point(s)
    -----------------------------------------------
    node: searching node
    exitPoint: exit nodes
    avoidPoint: nodes that would not be searched
    avoidEdge: segments would not be targeted as neighborhood
    max_depth: early exit of the loop

    return: list[TopoNode]
    """
    if avoidPoint is None: avoidPoint = []
    if node in exitPoint: return [node]
    if max_depth == 0:
        raise TopologyError(_findPathDepth, "meet maximum recursion depth")

    for nei in [chilNode for chilNode in node.neighbor if chilNode not in avoidPoint]:
        avoid = False
        for edge in avoidEdge:
            if node in edge.nodeLoop:
                if nei in edge.nodeLoop:
                    if abs(edge.nodeLoop.index(node) - edge.nodeLoop.index(nei)) == 1:
                        avoid = True
                        break
        if not avoid:
            path = _findPathDepth(nei, exitPoint, avoidPoint + [node], avoidEdge, max_depth - 1)
            if len(path) > 0:
                path.append(node)
                return path
    return []


def _divideBoundaryByNode(boundaries: list[TopoBound], nodeList: list[TopoNode]) -> list[TopoBound]:
    """
    Recursively divide boundaries by internal nodes to decompose complex regions into simpler ones.
    
    Parameters
    ----------
    boundaries : list of TopoBound
        List of boundary objects to be subdivided. Each boundary represents a closed loop of nodes.
    nodeList : list of TopoNode
        List of nodes not yet assigned to any boundary. These nodes are candidates for splitting existing boundaries.
    
    Returns
    -------
    list of TopoBound
        A list of simplified, non-overlapping boundary objects resulting from recursive subdivision by internal nodes.
    """
    """recursively divide the boundary(s) by some nodes inside the boundary(s)
    1. build a sub set of the eligible nodes that are not coveredBy by the boundaries
    2. for each boundary:
        2.1 judge whether the boundary is a minimum boundary: do not have other nodes inside it
        2.2 if the boundary is not minimum: depth-first search a path to the boundary from target node
        2.3 divide the boundary by the path
        2.4 check self intersection and put the boundary in the new set
    3. call _divideBoundaryByNode until len(eligible) == 0

    -----------------------------------------------
    boundaries: target list of boundary(s)
    nodeList: nodes that do not belong to any boundary. you can give network.nodes in the first time

    return: list[boundary]
    """

    """1. build a sub set of the network's nodes to accelerate the transverse"""
    netNodeSet = {node for node in nodeList}

    for bound in boundaries:
        netNodeSet = netNodeSet.difference({node for node in bound.nodeLoop})
    nodeList: list[TopoNode] = list(netNodeSet)

    if len(nodeList) > 0:
        nodeListLen = len(nodeList)
        boundarySplit: list[TopoBound] = []

        for bound in boundaries:
            # if len(bound.nodeLoop) < 4:
            #     boundarySplit.append(bound)
            # else:
            inside_node = None
            """2.1 judge whether the boundary is a minimum boundary: do not have other nodes inside it"""
            for node in nodeList:
                if shapely.contains_properly(bound.geometry, node.location):
                    inside_node = node
                    nodeList.remove(node)
                    break

            """2.2 if the boundary is not minimum: depth-first search a path to the boundary from target node"""
            if inside_node is None:
                boundarySplit.append(bound)  # exit and find next boundary
            else:
                try:

                    path1 = _findPathDepth(inside_node, bound.nodeLoop, [inside_node])
                    path2 = _findPathDepth(inside_node, bound.nodeLoop, path1)

                    if len(path2) == 0:
                        # there are inner rings in the loop. find a path to the path1 except for the first and second node
                        path2 = _findPathDepth(inside_node, path1[:-1], path1[-2:])
                        # two paths repeat on the start node!
                        innerRing = TopoBound(list(np.append(path1, np.flip(path2[:-1]))))
                        boundarySplit.append(innerRing)
                        boundarySplit.append(bound)
                    else:
                        # two paths repeat on the start node!
                        pathSplit = TopoBound(list(np.append(path1, np.flip(path2[:-1]))))
                        # also check the self intersect of the split path
                        validPath = TopoBound.selfIntersect(pathSplit)

                        for path in validPath[:-1]:
                            # the inner rings within the pathSplit
                            boundarySplit.append(path)
                        """2.3 divide the boundary by the path"""
                        bound1, bound2 = TopoBound.split(bound, validPath[-1])

                        """2.4 check self intersection and put the boundary in the new set"""
                        boundarySplit += TopoBound.selfIntersect(bound1)
                        boundarySplit += TopoBound.selfIntersect(bound2)
                except TopologyError as e:
                    # print(inside_node,inside_node.neighbor)
                    # print(path1,path2,bound)
                    # failed to find path due to low topology quality
                    print(f"******Warning: {e}")
                    boundarySplit.append(bound)

        if nodeListLen != len(nodeList):
            boundaries = _divideBoundaryByNode(boundarySplit, nodeList)
        else:
            boundaries = boundarySplit
    return boundaries


def _divideBoundaryByEdge(boundaries: list[TopoBound], edgeList: list[TopoBound] | list[TopoEdge]) -> list[TopoBound]:
    """
    Recursively divide boundary polygons using internal edges.
    
    Parameters
    ----------
    boundaries : list of TopoBound
        List of boundary objects to be subdivided. Each boundary represents a polygonal region.
    edgeList : list of TopoBound or list of TopoEdge
        List of edges that may lie inside the boundaries and are used for subdivision. 
        These edges are not part of any existing boundary. If TopoEdge objects are provided, 
        they are converted internally to TopoBound objects.
    
    Returns
    -------
    list of TopoBound
        A list of refined boundary objects resulting from recursive subdivision by eligible edges.
    """
    """recursively divide the boundary(s) by some edges inside the boundary(s)
    1. build a sub set of the eligible edges that are not coveredBy by the boundaries
    2. for each boundary:
        2.1 judge whether the boundary is a minimum boundary: do not have other edges inside it
        2.2 if the boundary is not minimum: divide the boundary by the edge
            2.2.1 if both points of the edge are on the boundary: directly divide it
            2.2.2 if one point not on the boundary: there is an inner ring inside the boundary
                2.2.2.1 try to find another eligible edge on the two boundaries
                2.2.2.2 if true: divide the outer ring with the inner ring and two edges
                2.2.2.3 if not: dump the edge
    3. call _divideBoundaryByEdge until len(eligible) == 0
    -----------------------------------------------
    boundaries: target list of boundary(s)
    edgeList: nodes that do not belong to any boundary. you can give network.nodes in the first time

    return: list[boundary]
    """

    """1. build a sub set of the eligible edges that are not coveredBy by the boundaries"""
    delLine = []
    for i, line in enumerate(edgeList):
        if isinstance(line, TopoEdge):
            edgeList[i] = TopoBound.fromTopoEdge(line)
            line = edgeList[i]
        for bound in boundaries:
            if line.coveredBy(bound):
                delLine.append(i)
                break
    edgeList: list[TopoBound] = list(np.delete(edgeList, delLine))

    if len(edgeList) > 0:
        edgeListLen = len(edgeList)
        boundSplit = []

        """2.1 judge whether the boundary is a minimum boundary: do not have other edges inside it"""
        for bound in boundaries:
            targetBound = None
            for edgeBound in edgeList:
                if edgeBound.connect(bound):
                    targetBound = edgeBound
                    edgeList.remove(edgeBound)
                    break

            if targetBound is None:
                boundSplit.append(bound)
            else:
                """2.2 if the boundary is not minimum: divide the boundary by the edge"""
                if targetBound.nodeLoop[0] in bound.nodeLoop and targetBound.nodeLoop[1] in bound.nodeLoop:
                    """2.2.1 if both points of the edge are on the boundary: directly divide it"""
                    boundSplit += TopoBound.split(bound, targetBound)
                else:
                    """2.2.2 if one point not on the boundary: there is an inner ring inside the boundary"""
                    """2.2.2.1 try to find another eligible edge on the two boundaries"""
                    """2.2.2.2 if true: divide the outer ring with the inner ring and two edges"""
                    """2.2.2.3 if not: dump the edge"""
                    boundSplit += TopoBound.split(bound, targetBound)

        """3. call _divideBoundaryByEdge until len(eligible) == 0"""
        if edgeListLen != len(edgeList):
            boundaries = _divideBoundaryByEdge(boundSplit, edgeList)
        else:
            boundaries = boundSplit
    return boundaries


def _divideBoundary(boundaries: list[TopoBound], edgeList: list[TopoBound] | list[TopoEdge]) -> list[TopoBound]:
    """
    Recursively divide boundaries using internal edges to decompose complex regions into minimal boundaries.
    
    Parameters
    ----------
    boundaries : list[TopoBound]
        List of boundary objects to be subdivided. Each boundary is expected to define a closed loop.
    edgeList : list[TopoBound] or list[TopoEdge]
        List of edge-like objects (either `TopoBound` or `TopoEdge`) that may lie inside the boundaries and are used for splitting.
        These edges are typically not yet part of any boundary and represent internal connections or potential splits.
    
    Returns
    -------
    list[TopoBound]
        A list of decomposed boundary objects resulting from recursive subdivision. 
        The output contains only minimal boundaries (i.e., those without any internal edges) and any newly detected inner rings.
    """
    """recursively divide the boundary(s) by some edges inside the boundary(s)
    1. build a sub set of the eligible edges that are not coveredBy by the boundaries
    2. for each boundary:
        2.1 judge whether the boundary is a minimum boundary: do not have other edges inside it
        2.2 if the boundary is not minimum: depth-first search a path to the boundary from the two nodes
        2.3 check path self-intersection:
            2.3.1 if one of the path in None:
                2.3.1.1 means the None nodes have an inner ring. find it and add if the ring is not exist in the boundaries
                2.3.1.2 dump this invalid edge
            2.3.2 add the inner ring inside the split path if the ring is not exist in the boundaries
        2.4 divide the boundary by the path
        2.5 check self intersection and put the boundary in the new set
    3. call _divideBoundaryByEdge until len(eligible) == 0
    -----------------------------------------------
    boundaries: target list of boundary(s)
    edgeList: nodes that do not belong to any boundary. you can give network.nodes in the first time

    return: list[boundary]
    """

    """1. build a sub set of the eligible edges that are not coveredBy by the boundaries"""
    delLine = []
    for i, line in enumerate(edgeList):
        if isinstance(line, TopoEdge):
            edgeList[i] = TopoBound.fromTopoEdge(line)
            line = edgeList[i]
        for bound in boundaries:
            if line.coveredBy(bound):
                delLine.append(i)
                break
    edgeList: list[TopoBound] = list(np.delete(edgeList, delLine))
    if len(edgeList) > 0:
        edgeListLen = len(edgeList)
        boundSplit = []

        """2.1 judge whether the boundary is a minimum boundary: do not have other edges inside it"""
        for bound in boundaries:
            targetEdge = None
            for edgeBound in edgeList:
                midPoint = shapely.points(np.average(shapely.get_coordinates(edgeBound.geometry),axis=0))
                if shapely.contains(bound.geometry,midPoint):
                    targetEdge = edgeBound
                    edgeList.remove(edgeBound)
                    break

            if targetEdge is None:
                boundSplit.append(bound)
            else:
                """2.2 if the boundary is not minimum: depth-first search a path to the boundary from the two nodes"""
                try:

                    path1 = _findPathDepth(targetEdge.nodeLoop[0], bound.nodeLoop, avoidEdge=[targetEdge])
                    path2 = _findPathDepth(targetEdge.nodeLoop[1], bound.nodeLoop, avoidPoint=path1,
                                           avoidEdge=[targetEdge])

                    """2.3.1 if one of the path in None:"""
                    if len(path1) * len(path2) == 0:
                        """2.3.1.1 means there is an inner ring. 
                        find it and add if the ring is not exist in the boundaries
                        There are two possibilities:
                        1) the inner ring contain the targetEdge. find a path from the start to the end.
                        2) the inner ring out of the targetEdge. Just dump the targetEdge, next loop will find it.
                        """
                        innerRing = _findPathDepth(targetEdge.nodeLoop[0], [targetEdge.nodeLoop[1]],
                                                   avoidEdge=[targetEdge])
                        if len(innerRing) > 0:
                            innerRing = np.append(innerRing,[targetEdge.nodeLoop[1]])
                            boundSplit.append(TopoBound(innerRing))
                    else:
                        # connect the path
                        pathSplit = TopoBound(np.append(path1, np.flip(path2)))
                        # also check the self intersect of the split path
                        """2.3.2 add the inner ring inside the split path if the ring is not exist in the boundaries"""
                        validPath = TopoBound.selfIntersect(pathSplit)
                        for path in validPath[:-1]:
                            # the inner rings within the pathSplit
                            boundSplit.append(path)
                        """2.3 divide the boundary by the path"""
                        bound1, bound2 = TopoBound.split(bound, validPath[-1])

                        """2.4 check self intersection and put the boundary in the new set"""
                        boundSplit += TopoBound.selfIntersect(bound1)
                        boundSplit += TopoBound.selfIntersect(bound2)
                except TopologyError as e:
                    # print(inside_node,inside_node.neighbor)
                    # print(path1,path2,bound)
                    # failed to find path due to low topology quality
                    print(f"******Warning: {e}")
                    boundSplit.append(bound)

        """3. call _divideBoundaryByEdge until len(eligible) == 0"""
        if edgeListLen != len(edgeList):
            boundaries = _divideBoundary(boundSplit, edgeList)
        else:
            boundaries = boundSplit
    return boundaries


def outerBoundary(model: MoosasContainer, bld_level: float) -> list[shapely.Geometry]:
    """
    Calculate the outer boundary of a network at a specified building level.
    
    Parameters
    ----------
    model : MoosasContainer
        The model containing topological edges to retrieve the network from.
    bld_level : float
        The building level at which to retrieve the network.
    
    Returns
    -------
    list[shapely.Geometry]
        A list of shapely Geometry objects representing the outer boundaries of each network component.
    """
    """only Calculate the outer boundary of a network

     ---------------------------------
    bld_level: building level to retrieve in float
    model: get topoEdge from this model

    return: list[shapely.Geometry]
    """

    network = TopoNetwork.inLevel(bld_level, model)
    if network.edges is None or network.nodes is None:
        return None
    networks = TopoNetwork.splitNetwork(network)
    print(f'\rTOPOLOGY: in {bld_level}: Calculate outer Boundary', end='')
    """calculate the outer boundaries (the biggest boundaries) of each network"""
    boundaries = [network.outerBoundary() for network in networks]
    return [bound.geometry for boundList in boundaries for bound in boundList]


def closed_contour_calculation(model: MoosasContainer, bld_level: float) -> MoosasContainer:
    """
    Calculate closed contours at a specified building level and update the model with boundary information.
    
    Parameters
    ----------
    model : MoosasContainer
        The input model containing topological edges to be processed.
    bld_level : float
        The building level at which to compute the closed contours.
    
    Returns
    -------
    MoosasContainer
        The updated model with recorded boundary information from the contour calculation.
    """
    """calculate the closed contour in the given building level.
    This method start with the network.inLevel method to build a network.
    the recognized boundaries will be recorded into the MoosasModel.

    ---------------------------------
    bld_level: building level to retrieve in float
    model: get topoEdge from this model

    return: model:MoosasModel
    """

    """build the network and split it"""
    network = TopoNetwork.inLevel(bld_level, model)
    if network.edges is None or network.nodes is None:
        return model
    # for ed in network.edges:
    #     print(shapely.get_coordinates([ed.fromP.location,ed.toP.location]).tolist())

    networks = TopoNetwork.splitNetwork(network)
    print(f'\rTOPOLOGY: in {bld_level}: Calculate outer Boundary', end='')
    """calculate the outer boundaries (the biggest boundaries) of each network"""
    boundaries: list[list[TopoBound]] = [network.outerBoundary() for network in networks]

    print(f'\rTOPOLOGY: in {bld_level}: Dividing boundary', end='')
    boundariesNew = []

    for boundGroup, network in zip(boundaries, networks):
        """divide the boundaries by node or edges inside"""
        boundGroup = _divideBoundary(boundGroup, network.edges)
        boundariesNew += boundGroup

    # 2.5 展平 boundary_list，检查是否顺时针并转换为 edge。
    print(f'\rTOPOLOGY: in {bld_level}: find {len(boundariesNew)} boundaries')
    model = _documentBoundary(np.array(boundariesNew).flatten(), model)

    return model


def _documentBoundary(boundaries: Iterable[TopoBound], model: MoosasContainer) -> MoosasContainer:
    """
    Reverse boundary orientation if necessary and append boundary edges to model.
    
    Parameters
    ----------
    boundaries : Iterable[TopoBound]
        An iterable of TopoBound objects representing boundaries, each containing a geometry and edge loop.
    model : MoosasContainer
        The container model to which boundary edge lists will be added.
    
    Returns
    -------
    MoosasContainer
        The updated model with boundary edge lists appended to its boundaryList attribute.
    """
    for i, bound in enumerate(boundaries):
        if not is_ccw(bound.geometry):
            bound.reverse()
        model.boundaryList.append([model.wallList[edge.modelId] for edge in bound.edgeLoop])
    return model


def _merge_tiny_partitions(partitions):
    """Merge sub-room slivers into the neighbor sharing their longest edge."""
    partitions = list(partitions)
    while True:
        tiny_index = next(
            (index for index, part in enumerate(partitions) if shapely.area(part) < geom.ROOM_MIN_AREA),
            None,
        )
        if tiny_index is None:
            return partitions

        tiny = partitions[tiny_index]
        neighbors = []
        for index, part in enumerate(partitions):
            if index == tiny_index:
                continue
            shared_length = shapely.length(
                shapely.intersection(shapely.boundary(tiny), shapely.boundary(part))
            )
            if shared_length > geom.POINT_PRECISION:
                neighbors.append((shared_length, index))
        if not neighbors:
            return partitions

        neighbor_index = max(neighbors)[1]
        merged = shapely.union(tiny, partitions[neighbor_index])
        keep = [
            part for index, part in enumerate(partitions)
            if index not in (tiny_index, neighbor_index)
        ]
        partitions = keep + [merged]


def _is_core_boundary(edge):
    return bool(edge.wall) and all(
        any(str(face_id).startswith("core_wall_") for face_id in mixItemListToList(wall.faceId))
        for wall in edge.wall
    )


def _direct_child_holes(edge, edges):
    """Return only the immediately nested boundaries inside an edge."""
    boundary = edge.force_2d()
    contained = [
        candidate.force_2d()
        for candidate in edges
        if candidate is not edge
        and shapely.contains_properly(boundary, candidate.force_2d())
    ]
    return [
        candidate
        for candidate in contained
        if not any(
            other is not candidate
            and shapely.contains_properly(other, candidate)
            for other in contained
        )
    ]


def _replace_one_sided_air_boundaries(boundaries, walls):
    """Use a coincident opaque wall when an air wall bounds only one contour."""
    occurrence_count = {}
    for boundary in boundaries:
        for wall in boundary:
            occurrence_count[wall] = occurrence_count.get(wall, 0) + 1

    replacements = {}
    opaque_walls = [wall for wall in walls if not wall.is_air_boundary]
    for wall, count in occurrence_count.items():
        if not wall.is_air_boundary or count != 1:
            continue
        replacement = next(
            (
                candidate
                for candidate in opaque_walls
                if candidate.level == wall.level
                and equals(candidate.force_2d(), wall.force_2d())
            ),
            None,
        )
        if replacement is not None:
            replacements[wall] = replacement

    return [
        [replacements.get(wall, wall) for wall in boundary]
        for boundary in boundaries
    ]


def packing_edges(model: MoosasContainer, divided_zones) -> MoosasContainer:
    """
    Packs edges into a MoosasContainer by validating and processing boundary lists, and optionally subdividing complex faces into simpler polygons.
    
    Parameters
    ----------
    model : MoosasContainer
        The container object holding wall, edge, boundary, and level lists to be processed.
        Modified in place by appending valid edges and walls, and removing processed ones.
    divided_zones : bool
        If True, enables the subdivision of complex 2D faces into simpler polygons using triangulation.
        Air walls are added to represent internal divisions, and original edges are replaced with new constructed edges.
    
    Returns
    -------
    MoosasContainer
        The updated model with validated and potentially subdivided edges, newly added air walls (if applicable),
        and remaining unassigned walls marked in `wall_remain`.
    """

    model.boundaryList = _replace_one_sided_air_boundaries(
        model.boundaryList,
        model.wallList,
    )
    faceSet = set(model.wallList)
    for edge in model.boundaryList:
        # print(edge)
        if len(edge) < 3:
            print("******Warning: TopologyError, boundary less than 3 edges")
            continue
        try:
            the_edge = MoosasEdge(edge)
            if the_edge.is_valid():
                model.edgeList.append(the_edge)
                faceSet.difference_update(edge)
            # else:
            #     print([e.force_2d() for e in edge])

        except GeometryError:
            print("******Warning: GeometryError, something occurred and the boundary was skipped")


    """Divide the boundaries into simple polygons"""
    if divided_zones:
        model.edgeList = [
            edge for edge in model.edgeList
            if edge.area >= geom.ROOM_MIN_AREA or _is_core_boundary(edge)
        ]
        for levelIdx, bldLevel in enumerate(model.levelList):
            edges = np.array(model.edgeList)[searchBy('level', bldLevel, model.edgeList)]
            for edgeIdx, edge in enumerate(edges):
                # ``contains`` considers a geometry to contain itself.  That
                # made the current boundary an identical "hole", so a
                # concave footprint was passed to the convexifier with its
                # exterior removed and could not be divided.  A hole must lie
                # strictly inside the boundary instead.
                holes = _direct_child_holes(edge, edges)
                newEdges, _ = triangulate2dFace(edge.force_2d(), holes)
                newEdges = _merge_tiny_partitions(newEdges)
                if len(newEdges) > 1:
                    walls = list(np.array(model.wallList)[searchBy('level', bldLevel, model.wallList)])
                    source_boundary = shapely.boundary(edge.force_2d())
                    for new_edge in newEdges:
                        coordinates = shapely.get_coordinates(new_edge)
                        for start, end in zip(coordinates[:-1], coordinates[1:]):
                            segment = shapely.linestrings([start, end])
                            if shapely.length(segment) <= geom.POINT_PRECISION:
                                continue
                            if MoosasEdge.matchWall(segment, walls) is None:
                                is_internal_partition = not shapely.covered_by(
                                    segment,
                                    shapely.buffer(source_boundary, geom.POINT_PRECISION),
                                )
                                air_wall = MoosasWall.fromProjection(
                                    segment,
                                    bottom=bldLevel,
                                    top=model.levelList[levelIdx + 1],
                                    model=model,
                                    airBoundary=is_internal_partition,
                                )
                                model.wallList = np.append(model.wallList, air_wall)
                                walls.append(air_wall)
                    newConstructEdges = []
                    for ed in newEdges:
                        try:
                            newConstructEdges += [MoosasEdge.selectWall(ed, walls)]
                        except GeometryError as gE:
                            print(f"******Warning: {gE}")
                    newEdges = newConstructEdges
                    model.edgeList.remove(edge)
                    model.edgeList += newEdges
                print(f'\rTOPOLOGY: in {bldLevel}: Dividing zones {edgeIdx}/{len(edges)}', end='')

    model.wall_remain = list(faceSet)
    model.shadingList = np.append(model.shadingList, list(faceSet))
    print()
    print('PACKING: Identified boundaries', len(model.edgeList))
    return model
