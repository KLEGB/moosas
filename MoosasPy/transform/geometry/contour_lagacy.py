from __future__ import annotations

import copy

from .geos import *
from ...models import *
from ...visual.visualization import *
from ...utils.constant import geom

def closed_contour_calculation(model: MoosasModel, bld_level: float):
    """
    Perform closed contour calculation for a given building level in a model.
    
    Parameters
    ----------
    model : MoosasModel
        The building model containing walls and other structural elements.
    bld_level : float
        The building level (elevation) at which to perform the closed contour calculation.
    
    Returns
    -------
    MoosasModel
        The input model updated with detected boundary information at the specified level.
    """
    print(f'Preprocessing in level {bld_level}')
    # 鍒涢€爓all_list
    wall_list = searchBy('level', bld_level, model.wallList)
    # plot_object(model.wallList[wall_list])
    # 鑰冭檻閫氶珮鐨勫
    # for i in range(len(model.wallList)):
    #    if model.wallList[i].level<bld_level and model.wallList[i].toplevel>bld_level:
    #        wall_list.append(i)
    if len(wall_list) == 0:
        return model
    # 1.1 鍒涘缓vec_list,娓呯悊鍑虹敤浜庨棴鍚堣瘑鍒殑闈?
    vec_list, wall_list = useful_wall(wall_list, model)
    # 1.2 鍒涢€犲敮涓€鐐瑰垪琛╨ocation_list / 鐐归摼鎺ョ粍node_list / 瑙掑害缁刟ngle_list
    location_list, node_list, angle_list = construct_node_network(vec_list)
    # 1.3 缈昏瘧vec_list鍧愭爣涓虹紪鍙峰姞蹇繍绠?
    for i in range(len(vec_list)):
        vec_list[i][1] = location_list.index(vec_list[i][1])
        vec_list[i][2] = location_list.index(vec_list[i][2])

    # 2.1 澶у尯鍩熷垎缁?寰楀埌node_groups
    # 閬嶅巻鍒板眿椤堕潰鏃讹紝nodelist浼氫负绌猴紝灏嗘姤閿?
    print('Node groupping.......')
    if len(node_list) == 0: return model
    node_groups = node_Groupping(node_list)

    # plot_plan_in_node(node_list,[],location_list,False,True)
    # print('灏嗚繘琛?.3f灞傚杞粨鎼滅储' % bld_level)
    # 2.2 鎼滅储澶栬疆寤?寰楀埌boundary_list
    print('Nodegroup_outerboundary.......')
    boundary_list = nodegroup_outerboundary(node_groups, node_list, location_list, angle_list)
    # plot_plan_in_node(node_list, [bound for group in boundary_list for bound in group], location_list, False, True)
    # print('灏嗚繘琛?.3f灞傚垎鍓茶疆寤?%bld_level)
    # 鍒涘缓瀛樺偍鍒楄〃boundary_coordinates锛堝瓨鐐瑰簭鍙凤級
    print('\nBoundary dividing.......')
    boundary_coordinates = []
    for bound in boundary_list:
        boundary_coordinates.append(bound)
    for i in range(len(node_groups)):
        # 2.3 鎸夌偣杩唬鍒嗗壊杞粨鑾峰緱鏂扮殑boundary_coordinates
        eligible = [node for node in node_groups[i] if not (node in boundary_list[i])]
        boundary_coordinates[i] = divide_boundary_node(boundary_coordinates[i], node_list, location_list, eligible)

        # 鏍规嵁鍙鍖栫粨鏋滃彲瑙侊紝涓ょ閮藉湪杞粨涓婄殑绾夸粛鏈璇嗗埆
        # 2.4 鎸夌嚎杩唬鍒嗗壊杞粨鑾峰緱鏂扮殑boundary_coordinates
        boundary_coordinates[i] = divide_boundary_edge(boundary_coordinates[i], vec_list, node_groups[i])
    # 2.5 灞曞钩boundarylist骞舵鏌ユ槸鍚﹂『鏃堕拡,杞崲涓篹dge

    print("find %d boundarys in building level" % np.sum([len(b) for b in boundary_coordinates]), bld_level)
    # plot_plan_in_node(node_list, [bound for group in boundary_coordinates for bound in group], location_list, False, True)
    model = document_boundary(boundary_coordinates, location_list, vec_list, model)
    return model

# 璺緞鎼滅储鐩稿叧
def findpath_depth(node, end: list, node_list: list, block_list: list, last=None, max_depth=geom.PATH_MAX_DEPTH):
    """
    Find a path from the current node to any node in the end list using depth-limited DFS.
    
    Parameters
    ----------
    node : int or hashable
        The current node to start searching from.
    end : list
        List of target nodes; the search stops if any of these nodes are reached.
    node_list : list of lists or dict of lists
        Adjacency list representing the graph; node_list[node] contains neighbors of node.
    block_list : list
        List of nodes that cannot be traversed; paths through these nodes are blocked.
    last : int or hashable, optional
        The previous node in the path to avoid going backwards. Default is None.
    max_depth : int, optional
        Maximum depth to search from the current node. Default is geom.PATH_MAX_DEPTH.
    
    Returns
    -------
    list
        A list of nodes representing the path from `node` to a node in `end`, 
        in reverse order (from end to start). Returns empty list if no path is found 
        within the depth limit or due to blocking.
    """
    if node in end: return [node]
    if max_depth == 0: return []
    neighbor = []
    for nei in node_list[node]:
        if nei == last: continue
        if nei in block_list: continue
        neighbor.append(nei)
    for nei in neighbor:
        path = findpath_depth(nei, end, node_list, block_list, last=node, max_depth=max_depth - 1)
        if path != []:
            path.append(node)
            return path
    return []


def split(linerring: list, splitline: list):
    """
    Split a linear ring by a given split line.
    
    Parameters
    ----------
    linerring : list
        List of nodes representing a linear ring. If the first and last elements are identical, 
        the last element is removed before processing.
    splitline : list
        List of nodes defining the split line. The split starts at the first node of splitline 
        and ends at the last node. This line is used to divide the linerring into two parts.
    
    Returns
    -------
    tuple of list
        A tuple containing two lists: linerring1 and linerring2. These represent the two resulting 
        rings after splitting the original linerring along the splitline. The splitline is included 
        in both output rings in forward order in linerring1 and reverse order in linerring2.
    """
    # Ver1.3 瀹氫綅鍒板垎鍓茬畻娉曟湁闂锛侀噸鍐欐妯″潡
    if linerring[0] == linerring[-1]:
        linerring.pop()
    linerring = np.roll(linerring, len(linerring) - linerring.index(splitline[0]))
    linerring1 = []
    for node in linerring:
        if node == splitline[-1]: break
        linerring1.append(node)
    linerring2 = [node for node in linerring if not (node in linerring1)]
    for node in splitline: linerring2.append(node)
    splitline.reverse()
    for node in splitline: linerring1.append(node)

    return linerring1, linerring2


def polygon_from_node(nodelist: list, location: list):
    """
    Construct a polygon from a list of node indices and their corresponding locations.
    
    Parameters
    ----------
    nodelist : list
        List of indices referring to positions in the location list.
    location : list
        List of point geometries (e.g., Shapely points) corresponding to node locations.
    
    Returns
    -------
    shapely.Geometry
        A polygon geometry constructed from the ordered sequence of points.
    """
    polist = [location[i] for i in nodelist]
    polist = [[shapely.get_x(node), shapely.get_y(node)] for node in polist]
    return shapely.polygons(polist)

# 杞粨璇嗗埆鏂规硶
def useful_wall(wall_list, model):
    """
    Filter out invalid, zero-length, duplicate, and isolated walls from a wall list.
    
    Parameters
    ----------
    wall_list : list of int
        List of wall indices to be filtered.
    model : object
        Model object containing a `wallList` attribute, where each element is a wall 
        with methods `force_2d()` and attributes `height` representing geometric and 
        dimensional properties.
    
    Returns
    -------
    list of int
        Filtered list of wall indices with invalid, zero-length, duplicate, and 
        isolated walls removed.
    """
    # 1.1.1 鍘婚櫎闆堕暱搴︾嚎銆佹棤鏁堢嚎銆侀噸绾?
    vec_list = []
    wall_list = [i for i in wall_list if model.wallList[i].force_2d() != None]
    wall_list = [i for i in wall_list if model.wallList[i].height > 0.9]
    # plot_object(model.wallList[wall_list], color='black')
    for i in wall_list:
        line = model.wallList[i].force_2d()
        vec_list.append([i,
                         shapely.get_point(line, 0),
                         shapely.get_point(line, 1)
                         ])
    for vec in vec_list:
        if vec[1] == vec[2]:
            wall_list.remove(vec[0])
    for i in range(len(vec_list)):
        for j in range(i + 1, len(vec_list)):
            if vec_list[i][1] in vec_list[j] and vec_list[i][2] in vec_list[j]:
                try:
                    wall_list.remove(vec_list[i][0])
                except:
                    pass

    # plot_object(model.wallList[wall_list], color='black')
    # 1.1.2 鍘婚櫎wall_list瀛ょ珛绾?
    def remove_wall(wall_list):
        """
        Remove walls that do not meet connectivity criteria and generate a list of wall vectors.
        
        Parameters
        ----------
        wall_list : list of int
            List of indices referring to walls in `model.wallList`. Each wall is processed 
            to extract its 2D geometric representation using `force_2d()`.
        
        Returns
        -------
        tuple of (numpy.ndarray, list of int)
            A tuple containing:
            - vec_list: A numpy array of shape (N, 3) where each row contains 
              [wall_index, start_point, end_point] for each directed segment of the remaining walls.
            - wall_list: Modified list of wall indices that satisfy the connectivity condition 
              (both endpoints shared by at least two other points in the simplified point set).
        """
        vec_list_simple = []
        for i in wall_list:
            line = model.wallList[i].force_2d()
            vec_list_simple.append(shapely.get_point(line, 0))
            vec_list_simple.append(shapely.get_point(line, 1))
        vec_list_simple = np.array(vec_list_simple)
        for i in wall_list:
            line = model.wallList[i].force_2d()
            point0 = shapely.get_point(line, 0)
            point1 = shapely.get_point(line, 1)
            sum0 = np.sum([1 for vec in vec_list_simple if shapely.equals_exact(point0, vec, tolerance=geom.POINT_PRECISION)])
            sum1 = np.sum([1 for vec in vec_list_simple if shapely.equals_exact(point1, vec, tolerance=geom.POINT_PRECISION)])
            if not (sum0 >= 2 and sum1 >= 2):
                wall_list.remove(i)
        return wall_list

    wall_list_len = 0
    while wall_list_len != len(wall_list):
        wall_list_len = len(wall_list)
        wall_list = remove_wall(wall_list)
        # plot_object(model.wallList[wall_list], color='black')

    # 1.1.3 鍒涢€爒ec_list
    vec_list = []
    for i in wall_list:
        line = model.wallList[i].force_2d()
        vec_list.append([i, shapely.get_point(line, 0), shapely.get_point(line, 1)])
        vec_list.append([i, shapely.get_point(line, 1), shapely.get_point(line, 0)])
    vec_list = [vec_list[i] for i in range(len(vec_list))
                if vec_list[i][1] != None and vec_list[i][2] != None]
    # plot_object(model.wallList[wall_list], color='black')
    return np.array(vec_list), wall_list


def construct_node_network(vec_list):
    """
    Construct a node network from a list of vectors.
    
    Parameters
    ----------
    vec_list : list of tuple
        A list where each element is a tuple containing vector information.
        Each tuple is expected to have at least three elements: 
        (ignored, source_point, target_point), where source_point and target_point 
        are points (e.g., coordinates or identifiers) representing connections.
    
    Returns
    -------
    location_list : list
        List of unique points (nodes) extracted from the second element of each tuple in vec_list.
    node_list : list of numpy.ndarray
        List where each element is an array of indices representing connected nodes 
        to the corresponding node in location_list, sorted by angular order.
    angle_list : list of numpy.ndarray
        List where each element is an array of angles corresponding to the direction 
        of connected vectors from the node, sorted in ascending order.
    """
    # 1.2.1 鍒涢€犲敮涓€鐐瑰垪琛╨ocation_list / 鐐归摼鎺ョ粍node_list
    unique_set = set()
    for point_item in vec_list:
        unique_set.add(point_item[1])
    location_list = list(unique_set)
    node_list = [[0] for i in range(len(location_list))]
    for vec in vec_list:
        node_list[location_list.index(vec[1])].append(vec[2])
    for i in range(len(node_list)): node_list[i].pop(0)
    # 1.2.2 璁＄畻鍚戦噺瑙抋ngle_list
    angle_list = copy.deepcopy(node_list)
    for i in range(len(angle_list)):
        for j in range(len(angle_list[i])):
            vec = Vector(node_list[i][j]).array - Vector(location_list[i]).array
            angle_list[i][j] = Vector(vec).quickAngle()
    # 1.2.3 浣跨敤angle_list涓簄ode_list鎺掑簭
    node_list = [np.array(node_list[i])[np.argsort(angle_list[i])] for i in range(len(node_list))]
    angle_list = [np.array(angle_list[i])[np.argsort(angle_list[i])] for i in range(len(angle_list))]
    # 1.3.1 缈昏瘧node_list鍧愭爣涓虹紪鍙峰姞蹇繍绠?
    for i in range(len(node_list)):
        for j in range(len(node_list[i])):
            node_list[i][j] = location_list.index(node_list[i][j])
    return location_list, node_list, angle_list


def node_Groupping(node_list):
    """
    Group nodes based on their connectivity.
    
    Parameters
    ----------
    node_list : list of list
        A list where each element is a list representing connections or edges from a node.
        Nodes with more than one connection are considered eligible for grouping.
    
    Returns
    -------
    list of list
        A list of groups, where each group is a list of indices representing connected nodes.
    """
    node_groups: list = []
    eligible = [i for i in range(len(node_list)) if len(node_list[i]) > 1]
    while len(eligible) > 0:
        start = eligible[0]
        group = []

        def findpath_breadth(node):
            """
            Perform a breadth-first search to find a path from the start node and group connected nodes.
            
            Parameters
            ----------
            node : object
                The current node being processed in the graph. Expected to be a hashable type.
            start : object
                The starting node for the breadth-first traversal. Must be present in the graph.
            node_list : dict
                A dictionary mapping each node to a list of its neighboring nodes.
            eligible : set
                A set of nodes that are eligible to be visited during traversal.
            node_groups : list
                A list that accumulates groups of connected nodes; updated in-place.
            group : list
                A temporary list storing the current group of connected nodes during traversal.
            
            Returns
            -------
            list
                Updated list of node groups, where each group is a list of connected nodes.
            """
            if node in group: return False
            if not (node in eligible): return False
            group.append(node)
            eligible.remove(node)
            for nei in node_list[node]:
                findpath_breadth(nei)
            return True

        findpath_breadth(start)
        node_groups.append(group)
    return node_groups


def nodegroup_outerboundary(node_groups, node_list, location_list, angle_list):
    """
    Compute the outer boundary of each node group based on geometric and angular relationships.
    
    Parameters
    ----------
    node_groups : list of list of int
        A list of node groups, where each group is a list of node indices.
    node_list : list of list of int
        Adjacency list representation of the graph; node_list[i] contains the neighbors of node i.
    location_list : list of object
        List of point objects representing the spatial location of each node; supports coordinate extraction via shapely.
    angle_list : list of list of float
        For each node, a list of angles (in radians) to its neighboring nodes, aligned with node_list.
    
    Returns
    -------
    list of list of list of int
        A list corresponding to each node group. Each element is a list of closed loops (sub-boundaries),
        where each loop is represented as a list of node indices forming an outer or inner boundary.
    """
    boundary_list = []
    for group in node_groups:
        # 瀵筺ode杩涜浜屾鍏抽敭璇嶆帓搴忥紝绗竴鍏抽敭璇嶄负x鍧愭爣(鏈€澶?锛岀浜屽叧閿瘝涓簓鍧愭爣(鏈€灏?,鍗冲彸涓嬭
        group_xy = np.array(
            [[node, shapely.get_x(location_list[node]), shapely.get_y(location_list[node])] for node in group])
        max_x = np.max(group_xy.T[1])
        group_xy = group_xy[[i for i in range(len(group)) if group_xy[i][1] == max_x]]
        start_node = int(group_xy[np.argmin(group_xy.T[2])][0])  # start_node: 寮€濮嬭妭鐐圭紪鍙?
        end_node = node_list[start_node][0]  # end_node: 缁撴潫鑺傜偣缂栧彿
        last_node = start_node  # last_node: 涓婁竴涓妭鐐圭紪鍙?
        outer_boundary = [start_node, end_node]  # outer_boundary: 鐢ㄤ簬璁板綍澶栬疆寤?
        # plot_plan_in_node(node_list, [outer_boundary], location_list, save=False, show=True)
        is_valid = True

        # Ver1.3: 鐢ㄤ簬闃叉寰幆閬嶅巻锛岃褰曟瘡娆＄殑閫夋嫨
        nextNodeDict = {}
        while end_node != start_node and is_valid:
            # 璁＄畻鏉ユ簮鏂瑰悜
            # print(start_node, end_node, last_node, outer_boundary)
            last_node_vec = Vector(location_list[last_node]).array
            end_node_vec = Vector(location_list[end_node]).array
            vec_last = last_node_vec - end_node_vec
            node_list_T = [item for item in node_list[end_node] if item != last_node]
            angle_list_T = [angle_list[end_node][i] for i in range(len(angle_list[end_node])) if
                            node_list[end_node][i] != last_node]
            # 鎵惧埌鏉ユ簮鏂瑰悜椤烘椂閽堢涓€涓偣
            next_node = node_list_T[0]
            for i in range(len(angle_list_T)):
                if angle_list_T[i] > Vector(vec_last).quickAngle():
                    if end_node in nextNodeDict.keys():
                        # Ver1.3: 鐢ㄤ簬闃叉寰幆閬嶅巻锛岃褰曟瘡娆＄殑閫夋嫨
                        if node_list_T[i] == nextNodeDict[end_node]:
                            continue
                    next_node = node_list_T[i]
                    # Ver1.3: 鐢ㄤ簬闃叉寰幆閬嶅巻锛岃褰曟瘡娆＄殑閫夋嫨(濡堢殑鎬讳笉鍙兘缁欐垜缁忚繃涓夋鍚э紵锛燂紵锛?
                    nextNodeDict[end_node] = next_node
                    break
            # 鏇存柊last_node鍜宔nd_node鍜宱uter_boundary
            outer_boundary.append(next_node)
            # print(outer_boundary)
            # print(location_list[next_node])
            # plot_plan_in_node(node_list, [outer_boundary], location_list, save=False, show=True)
            print('\r' + 'Iteration:' + str(len(outer_boundary)), end='')
            if len(outer_boundary) > 10000:
                print()
                print('***Error: iteration collasped. Dump the group')
                print(location_list[next_node])
                is_valid = False
            last_node = end_node
            end_node = next_node

        if is_valid:
            # plot_plan_in_node(node_list, [outer_boundary], location_list, save=False, show=True)
            # Ver1.3 寰幆缁撴潫锛屾柇寮€鑷氦閮ㄥ垎
            new_outer_boundary = []
            while len(outer_boundary) > 0:
                sub_boundary = []
                break_point = 0
                end_point = len(outer_boundary) - 1
                for i in range(len(outer_boundary)):
                    # 鎼滅储鏂偣
                    if outer_boundary[i] in outer_boundary[0:i]:
                        break_point = outer_boundary.index(outer_boundary[i])
                        end_point = i
                        sub_boundary = outer_boundary[break_point:end_point]
                        sub_boundary.append(sub_boundary[0])
                        break
                if len(sub_boundary) > 2:
                    new_outer_boundary.append(sub_boundary)
                if end_point == len(outer_boundary) - 1:
                    break
                else:
                    outer_boundary = outer_boundary[0:break_point] + outer_boundary[end_point:]
            boundary_list.append(new_outer_boundary)
        else:
            boundary_list.append([])
    # plot_plan_in_node(node_list, boundary_list, location_list, save=False, show=True)

    return boundary_list


def divide_boundary_node(boundary_iteration, node_list, location_list, eligible):
    """
    Iteratively splits boundary nodes by inserting eligible interior nodes to refine polygonal regions.
    
    Parameters
    ----------
    boundary_iteration : list of list of int
        A list of boundary node sequences, where each inner list represents a polygonal boundary 
        defined by node indices.
    node_list : dict or list of lists
        Graph-like structure representing connections between nodes; used during depth-first search 
        to find paths between nodes.
    location_list : array-like of shapely.Point or similar geometric points
        List of point coordinates corresponding to each node, indexed by node ID; used for spatial 
        containment checks.
    eligible : list of int
        List of node indices that are candidates for insertion into boundaries if they lie inside 
        a given region.
    
    Returns
    -------
    list of list of int
        Refined list of boundary node sequences after iterative splitting; each inner list is a 
        resulting polygon boundary with inserted nodes, ensuring no eligible interior nodes remain.
    """
    # 杩唬鍒嗗壊杞粨-鐐?
    ContinueSplit = True
    while len(eligible) > 0 and ContinueSplit:

        ContinueSplit = False
        new_boundary_coordinates = []
        # 鍒ゆ柇鏄惁涓烘渶灏忚疆寤?
        for j in range(len(boundary_iteration)):
            node_of_region = boundary_iteration[j]
            if len(node_of_region) < 4: continue
            inside_node = None
            region = polygon_from_node(node_of_region, location_list)
            for node in eligible:
                if shapely.contains_properly(region, location_list[node]):
                    inside_node = node
                    ContinueSplit = True
                    break
            # 鑻ラ潪鏈€灏忚矾寰勶紝鎵ц娣卞害鎼滅储骞跺垎鍓茶疆寤?
            if inside_node == None:
                new_boundary_coordinates.append(node_of_region)
            else:
                path1 = findpath_depth(inside_node, node_of_region, node_list, [inside_node])
                path2 = findpath_depth(inside_node, node_of_region, node_list, path1)
                path2.reverse()
                # Ver1.3: 鍒嗗壊鐐瑰閲嶅浜嗭紒锛侊紒
                for ip in range(1, len(path2)): path1.append(path2[ip])
                # Ver1.3: 鍘婚櫎鑷氦鐨勫唴鍦?
                repeat = True
                while repeat:
                    repeat = False
                    for q in range(1, len(path1) - 1):
                        if path1[q] in path1[:q]:
                            break_point = path1[:q].index(path1[q])
                            path1 = path1[:break_point] + path1[q:]
                            repeat = True
                            break
                # plot_plan_in_node(node_list, [boundary_iteration[j]], location_list, save=False, show=True)
                # plot_plan_in_node(node_list, [path1], location_list, save=False, show=True)
                try:
                    region1, region2 = split(node_of_region, path1)
                    new_boundary_coordinates.append(region1)
                    new_boundary_coordinates.append(region2)
                except:
                    pass
                # 鏇存柊eligible
                eligible = [node for node in eligible if not (node in path1)]
        # 鏇存柊璇roup鐨勮疆寤撳垪琛?
        boundary_iteration = new_boundary_coordinates

    return boundary_iteration


def divide_boundary_edge(boundary_iteration, vec_list, node_groups):
    """
    Divide boundary edges based on given node groups and vector list.
    
    Parameters
    ----------
    boundary_iteration : int
        The current iteration index for the boundary processing.
    vec_list : list of array_like
        List of vectors representing line segments or edges in the boundary.
    node_groups : list of tuple
        List of tuples, each containing node indices that define a group of connected nodes.
    
    Returns
    -------
    list of array_like
        A list of divided boundary edge vectors resulting from the grouping and iteration.
    """
    # 鏁寸悊绾挎缁?
    def overlaps_in_node(geo1_node: list, geo2_node: list):
        """Check if two nodes overlap in a geometric sequence and process boundary edges accordingly.
        
        Parameters
        ----------
        geo1_node : list
            List representing the first geometric node sequence.
        geo2_node : list
            List of two elements representing the second geometric node to check for overlap in geo1_node.
        
        Returns
        -------
        bool
            True if the two nodes are adjacent in geo1_node, False otherwise.
        """
        try:
            id1 = geo1_node.index(geo2_node[0])
            id2 = geo1_node.index(geo2_node[1])
        except:
            return False
        if np.abs(id1 - id2) == 1: return True
        # if np.abs(id1-id2)==len(geo1_node)-1:return True
        return False

    edge_group1 = []
    edge_group2 = []
    for vec in vec_list:
        if vec[1] in node_groups:
            if not (vec[0] in edge_group2):
                edge_group1.append([vec[1], vec[2]])
                edge_group2.append(vec[0])
    eligible_edge = copy.deepcopy(edge_group1)
    for edge in edge_group1:
        for bound in boundary_iteration:
            if overlaps_in_node(bound[0:-1], edge) or overlaps_in_node(bound[0:-1], [edge[1], edge[0]]):
                eligible_edge.remove(edge)
                break
    new_boundary_coordinates = copy.deepcopy(boundary_iteration)
    # 鎶婁笂杩扮帺鎰忓効鎬艰繘鍘?
    for edge in eligible_edge:
        for bound in new_boundary_coordinates:
            if (edge[0] in bound) and (edge[1] in bound):
                ring1, ring2 = split(bound, edge)
                new_boundary_coordinates.remove(bound)
                new_boundary_coordinates.append(ring1)
                new_boundary_coordinates.append(ring2)
                break
    boundary_iteration = new_boundary_coordinates
    return boundary_iteration


def document_boundary(boundary_coordinates, location_list, vec_list, model):
    """
    Constructs and appends boundary edges to the model based on boundary coordinates.
    
    Parameters
    ----------
    boundary_coordinates : list of list of int
        A nested list where each sublist contains node indices defining a polygonal boundary.
    location_list : list
        List of node locations; used to construct polygons for orientation checking.
    vec_list : list of tuples
        List of vectors, each represented as a tuple (index, node1, node2), 
        used to find corresponding wall elements between nodes.
    model : object
        A model object containing a `wallList` attribute (list of wall elements) 
        and a `boundaryList` attribute (list to which constructed boundaries are appended).
    
    Returns
    -------
    model : object
        The input model object with updated `boundaryList` containing lists of wall elements 
        representing each detected boundary.
    """
    new_boundary_coordinates = []
    for i in boundary_coordinates:
        for j in i:
            if not is_ccw(polygon_from_node(j, location_list)):
                j.reverse()
            new_boundary_coordinates.append(j)

    boundary_coordinates = new_boundary_coordinates
    # 杞崲
    for path in boundary_coordinates:
        boundary_edge = []

        for i in range(len(path) - 1):
            # print(path[i],path[i+1])
            for vec in vec_list:
                if (vec[1] == path[i] and vec[2] == path[i + 1]) or (vec[2] == path[i] and vec[1] == path[i + 1]):
                    # print(vec)
                    boundary_edge.append(model.wallList[vec[0]])
                    break

        boundary_edge_show = ''
        for edge in boundary_edge:
            boundary_edge_show += str(edge.faceId) + '-'
        # print('Find a boundary,faceId:', boundary_edge_show)
        # plot_object(boundary_edge)
        model.boundaryList.append(boundary_edge)
    return model