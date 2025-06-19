from __future__ import annotations

import copy

from .geos import *
from ..models import *
from pythonDist.MoosasPy.visual.visualization import *
from ..utils.constant import geom

def closed_contour_calculation(model: MoosasModel, bld_level: float):
    print(f'Preprocessing in level {bld_level}')
    # 创造wall_list
    wall_list = searchBy('level', bld_level, model.wallList)
    # plot_object(model.wallList[wall_list])
    # 考虑通高的墙
    # for i in range(len(model.wallList)):
    #    if model.wallList[i].level<bld_level and model.wallList[i].toplevel>bld_level:
    #        wall_list.append(i)
    if len(wall_list) == 0:
        return model
    # 1.1 创建vec_list,清理出用于闭合识别的面
    vec_list, wall_list = useful_wall(wall_list, model)
    # 1.2 创造唯一点列表location_list / 点链接组node_list / 角度组angle_list
    location_list, node_list, angle_list = construct_node_network(vec_list)
    # 1.3 翻译vec_list坐标为编号加快运算
    for i in range(len(vec_list)):
        vec_list[i][1] = location_list.index(vec_list[i][1])
        vec_list[i][2] = location_list.index(vec_list[i][2])

    # 2.1 大区域分组,得到node_groups
    # 遍历到屋顶面时，nodelist会为空，将报错
    print('Node groupping.......')
    if len(node_list) == 0: return model
    node_groups = node_Groupping(node_list)

    # plot_plan_in_node(node_list,[],location_list,False,True)
    # print('将进行%.3f层外轮廓搜索' % bld_level)
    # 2.2 搜索外轮廓,得到boundary_list
    print('Nodegroup_outerboundary.......')
    boundary_list = nodegroup_outerboundary(node_groups, node_list, location_list, angle_list)
    # plot_plan_in_node(node_list, [bound for group in boundary_list for bound in group], location_list, False, True)
    # print('将进行%.3f层分割轮廓'%bld_level)
    # 创建存储列表boundary_coordinates（存点序号）
    print('\nBoundary dividing.......')
    boundary_coordinates = []
    for bound in boundary_list:
        boundary_coordinates.append(bound)
    for i in range(len(node_groups)):
        # 2.3 按点迭代分割轮廓获得新的boundary_coordinates
        eligible = [node for node in node_groups[i] if not (node in boundary_list[i])]
        boundary_coordinates[i] = divide_boundary_node(boundary_coordinates[i], node_list, location_list, eligible)

        # 根据可视化结果可见，两端都在轮廓上的线仍未被识别
        # 2.4 按线迭代分割轮廓获得新的boundary_coordinates
        boundary_coordinates[i] = divide_boundary_edge(boundary_coordinates[i], vec_list, node_groups[i])
    # 2.5 展平boundarylist并检查是否顺时针,转换为edge

    print("find %d boundarys in building level" % np.sum([len(b) for b in boundary_coordinates]), bld_level)
    # plot_plan_in_node(node_list, [bound for group in boundary_coordinates for bound in group], location_list, False, True)
    model = document_boundary(boundary_coordinates, location_list, vec_list, model)
    return model

# 路径搜索相关
def findpath_depth(node, end: list, node_list: list, block_list: list, last=None, max_depth=geom.PATH_MAX_DEPTH):
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
    # Ver1.3 定位到分割算法有问题！重写此模块
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
    polist = [location[i] for i in nodelist]
    polist = [[pygeos.get_x(node), pygeos.get_y(node)] for node in polist]
    return pygeos.polygons(polist)

# 轮廓识别方法
def useful_wall(wall_list, model):
    # 1.1.1 去除零长度线、无效线、重线
    vec_list = []
    wall_list = [i for i in wall_list if model.wallList[i].force_2d() != None]
    wall_list = [i for i in wall_list if model.wallList[i].height > 0.9]
    # plot_object(model.wallList[wall_list], color='black')
    for i in wall_list:
        line = model.wallList[i].force_2d()
        vec_list.append([i,
                         pygeos.get_point(line, 0),
                         pygeos.get_point(line, 1)
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
    # 1.1.2 去除wall_list孤立线
    def remove_wall(wall_list):
        vec_list_simple = []
        for i in wall_list:
            line = model.wallList[i].force_2d()
            vec_list_simple.append(pygeos.get_point(line, 0))
            vec_list_simple.append(pygeos.get_point(line, 1))
        vec_list_simple = np.array(vec_list_simple)
        for i in wall_list:
            line = model.wallList[i].force_2d()
            point0 = pygeos.get_point(line, 0)
            point1 = pygeos.get_point(line, 1)
            sum0 = np.sum([1 for vec in vec_list_simple if pygeos.equals_exact(point0, vec, tolerance=geom.POINT_PRECISION)])
            sum1 = np.sum([1 for vec in vec_list_simple if pygeos.equals_exact(point1, vec, tolerance=geom.POINT_PRECISION)])
            if not (sum0 >= 2 and sum1 >= 2):
                wall_list.remove(i)
        return wall_list

    wall_list_len = 0
    while wall_list_len != len(wall_list):
        wall_list_len = len(wall_list)
        wall_list = remove_wall(wall_list)
        # plot_object(model.wallList[wall_list], color='black')

    # 1.1.3 创造vec_list
    vec_list = []
    for i in wall_list:
        line = model.wallList[i].force_2d()
        vec_list.append([i, pygeos.get_point(line, 0), pygeos.get_point(line, 1)])
        vec_list.append([i, pygeos.get_point(line, 1), pygeos.get_point(line, 0)])
    vec_list = [vec_list[i] for i in range(len(vec_list))
                if vec_list[i][1] != None and vec_list[i][2] != None]
    # plot_object(model.wallList[wall_list], color='black')
    return np.array(vec_list), wall_list


def construct_node_network(vec_list):
    # 1.2.1 创造唯一点列表location_list / 点链接组node_list
    unique_set = set()
    for point_item in vec_list:
        unique_set.add(point_item[1])
    location_list = list(unique_set)
    node_list = [[0] for i in range(len(location_list))]
    for vec in vec_list:
        node_list[location_list.index(vec[1])].append(vec[2])
    for i in range(len(node_list)): node_list[i].pop(0)
    # 1.2.2 计算向量角angle_list
    angle_list = copy.deepcopy(node_list)
    for i in range(len(angle_list)):
        for j in range(len(angle_list[i])):
            vec = Vector(node_list[i][j]).array - Vector(location_list[i]).array
            angle_list[i][j] = Vector(vec).quickAngle()
    # 1.2.3 使用angle_list为node_list排序
    node_list = [np.array(node_list[i])[np.argsort(angle_list[i])] for i in range(len(node_list))]
    angle_list = [np.array(angle_list[i])[np.argsort(angle_list[i])] for i in range(len(angle_list))]
    # 1.3.1 翻译node_list坐标为编号加快运算
    for i in range(len(node_list)):
        for j in range(len(node_list[i])):
            node_list[i][j] = location_list.index(node_list[i][j])
    return location_list, node_list, angle_list


def node_Groupping(node_list):
    node_groups: list = []
    eligible = [i for i in range(len(node_list)) if len(node_list[i]) > 1]
    while len(eligible) > 0:
        start = eligible[0]
        group = []

        def findpath_breadth(node):
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
    boundary_list = []
    for group in node_groups:
        # 对node进行二段关键词排序，第一关键词为x坐标(最大)，第二关键词为y坐标(最小),即右下角
        group_xy = np.array(
            [[node, pygeos.get_x(location_list[node]), pygeos.get_y(location_list[node])] for node in group])
        max_x = np.max(group_xy.T[1])
        group_xy = group_xy[[i for i in range(len(group)) if group_xy[i][1] == max_x]]
        start_node = int(group_xy[np.argmin(group_xy.T[2])][0])  # start_node: 开始节点编号
        end_node = node_list[start_node][0]  # end_node: 结束节点编号
        last_node = start_node  # last_node: 上一个节点编号
        outer_boundary = [start_node, end_node]  # outer_boundary: 用于记录外轮廓
        # plot_plan_in_node(node_list, [outer_boundary], location_list, save=False, show=True)
        is_valid = True

        # Ver1.3: 用于防止循环遍历，记录每次的选择
        nextNodeDict = {}
        while end_node != start_node and is_valid:
            # 计算来源方向
            # print(start_node, end_node, last_node, outer_boundary)
            last_node_vec = Vector(location_list[last_node]).array
            end_node_vec = Vector(location_list[end_node]).array
            vec_last = last_node_vec - end_node_vec
            node_list_T = [item for item in node_list[end_node] if item != last_node]
            angle_list_T = [angle_list[end_node][i] for i in range(len(angle_list[end_node])) if
                            node_list[end_node][i] != last_node]
            # 找到来源方向顺时针第一个点
            next_node = node_list_T[0]
            for i in range(len(angle_list_T)):
                if angle_list_T[i] > Vector(vec_last).quickAngle():
                    if end_node in nextNodeDict.keys():
                        # Ver1.3: 用于防止循环遍历，记录每次的选择
                        if node_list_T[i] == nextNodeDict[end_node]:
                            continue
                    next_node = node_list_T[i]
                    # Ver1.3: 用于防止循环遍历，记录每次的选择(妈的总不可能给我经过三次吧？？？）
                    nextNodeDict[end_node] = next_node
                    break
            # 更新last_node和end_node和outer_boundary
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
            # Ver1.3 循环结束，断开自交部分
            new_outer_boundary = []
            while len(outer_boundary) > 0:
                sub_boundary = []
                break_point = 0
                end_point = len(outer_boundary) - 1
                for i in range(len(outer_boundary)):
                    # 搜索断点
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
    # 迭代分割轮廓-点
    ContinueSplit = True
    while len(eligible) > 0 and ContinueSplit:

        ContinueSplit = False
        new_boundary_coordinates = []
        # 判断是否为最小轮廓
        for j in range(len(boundary_iteration)):
            node_of_region = boundary_iteration[j]
            if len(node_of_region) < 4: continue
            inside_node = None
            region = polygon_from_node(node_of_region, location_list)
            for node in eligible:
                if pygeos.contains_properly(region, location_list[node]):
                    inside_node = node
                    ContinueSplit = True
                    break
            # 若非最小路径，执行深度搜索并分割轮廓
            if inside_node == None:
                new_boundary_coordinates.append(node_of_region)
            else:
                path1 = findpath_depth(inside_node, node_of_region, node_list, [inside_node])
                path2 = findpath_depth(inside_node, node_of_region, node_list, path1)
                path2.reverse()
                # Ver1.3: 分割点处重复了！！！
                for ip in range(1, len(path2)): path1.append(path2[ip])
                # Ver1.3: 去除自交的内圈
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
                # 更新eligible
                eligible = [node for node in eligible if not (node in path1)]
        # 更新该group的轮廓列表
        boundary_iteration = new_boundary_coordinates

    return boundary_iteration


def divide_boundary_edge(boundary_iteration, vec_list, node_groups):
    # 整理线段组
    def overlaps_in_node(geo1_node: list, geo2_node: list):
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
    # 把上述玩意儿怼进去
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
    new_boundary_coordinates = []
    for i in boundary_coordinates:
        for j in i:
            if not is_ccw(polygon_from_node(j, location_list)):
                j.reverse()
            new_boundary_coordinates.append(j)

    boundary_coordinates = new_boundary_coordinates
    # 转换
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