import os
import pygeos
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

import xml.etree.ElementTree as ET
from . import convexify
from graphIO import read_geo, write_geo, read_xml
from scipy.spatial.transform import Rotation as R


class OBB:
    """
    Oriented Bounding Box (OBB) Class
    Converts the space and faces into a OBB representation
        center = (x,y,z) # 3D center of the OBB
        scale = (l,w,h)  # 3D scale of the OBB
        rotation = R(3x3) # 3x3 rotation matrix of the OBB
    """

    def create_obb(points, normal, min_scale = 0.1):
        """
        创建点集的定向包围盒 (OBB)，并返回 OBB 参数
        参数:
            points: np.ndarray, (N, 3);
            normal: np.ndarray, (3,);
            min_scale: float，OBB 的最小尺度
        返回:
            obb_params: dict，包含 OBB 相关参数
        """
        # 以z轴和法向量创建相对坐标架
        geometry = pygeos.multipoints(points)
        z_axis = np.array([0,0,1])
        z_r = normal
        
        
        if np.abs(z_r[0]) <= 1e-3 and np.abs(z_r[1]) <= 1e-3:  # 法向量判定                  

            z_r = z_axis
            # 使用 pygeos 计算最小外接矩形（OBB），返回旋转的包围盒
            min_rotated_rectangle = pygeos.minimum_rotated_rectangle(geometry)
            
            # 获取 OBB 参数
            obb_coords = np.array(pygeos.get_coordinates(min_rotated_rectangle, include_z=True)) [:-1] 
            obb_coords = np.nan_to_num(obb_coords, nan=points[0,2])
            obb_coords[:,2] = (np.min(points[:, 2])+ np.max(points[:, 2]))/2

            # 计算边向量
            if len(obb_coords) <= 2:
                centroid = np.mean(points, axis=0)
                x_r, y_r = np.array([1, 0, 0]), np.array([0, 1, 0])
                rotation = np.array([x_r, y_r, z_r])
                rotation_matrix = R.from_matrix(rotation).as_matrix()
                l = max(np.ptp(points[:, 0]), min_scale)
                w = max(np.ptp(points[:, 1]), min_scale)
                h = max(np.ptp(points[:, 2]), min_scale)
        
                original_obb_centroid = centroid

            else:
                x_vec = obb_coords[1] - obb_coords[0]
                y_vec = obb_coords[3] - obb_coords[0]
            
                # 计算范数
                x_norm = np.linalg.norm(x_vec)
                y_norm = np.linalg.norm(y_vec)
                
                # 检查范数并计算单位向量
                if x_norm > 1e-6:
                    x_r = x_vec / x_norm
                else:
                    x_r = np.array([1, 0, 0])  # 默认x方向
                    
                if y_norm > 1e-6:
                    y_r = y_vec / y_norm
                else:
                    y_r = np.array([0, 1, 0])  # 默认y方向

                rotation = np.array([x_r, y_r, z_r])
                rotation_matrix = R.from_matrix(rotation).as_matrix()

                l = np.linalg.norm(obb_coords[1] - obb_coords[0])
                w = np.linalg.norm(obb_coords[3] - obb_coords[0])
                h = max(np.max(points[:, 2])-np.min(points[:, 2]), min_scale) 

                original_obb_centroid = np.mean(obb_coords, axis=0)
            
        else:
            x_r = np.cross(z_r, z_axis)
            y_r = np.cross(z_r, x_r)

            rotation = np.array([x_r, y_r, z_r])
            rotation_matrix = R.from_matrix(rotation).as_matrix()
            

            rotated_points = points.dot(rotation_matrix.T)

            l = max(np.ptp(rotated_points[:, 0]), min_scale)
            w = max(np.ptp(rotated_points[:, 1]), min_scale)
            h = max(np.ptp(rotated_points[:, 2]), min_scale)
            
            centroid = np.mean([
                [np.min(rotated_points[:, 0]), np.min(rotated_points[:, 1]), np.min(rotated_points[:, 2])],
                [np.max(rotated_points[:, 0]), np.max(rotated_points[:, 1]), np.max(rotated_points[:, 2])]
            ], axis=0)
            
            # 反向旋转 OBB 坐标
            original_obb_centroid = np.dot(centroid, rotation_matrix)

        # 返回 OBB 参数
        obb_params = {
            'center': original_obb_centroid,
            'scale': np.array([l,w,h]),
            'rotation': rotation_matrix,
        }

        return obb_params
    
    def plot_obb_and_points(points, obb_params):
        

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        # 提取 OBB 参数
        center = obb_params['center']
        l, w, h = obb_params['scale']
        Rot = obb_params['rotation']

        # 8 个 OBB 角点的偏移量
        offsets = np.array([
            [-l/2, -w/2, -h/2],
            [ l/2, -w/2, -h/2],
            [ l/2,  w/2, -h/2],
            [-l/2,  w/2, -h/2],
            [-l/2, -w/2,  h/2],
            [ l/2, -w/2,  h/2],
            [ l/2,  w/2,  h/2],
            [-l/2,  w/2,  h/2]
        ])

        # 旋转并平移 OBB 角点
        corners = np.dot((np.dot(center, Rot.T) + offsets), Rot)

        # 绘制点云
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c='r', marker='o')

        # 连接 OBB 角点的边来构建立方体
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # 底面边
            [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面边
            [0, 4], [1, 5], [2, 6], [3, 7]   # 连接顶面和底面
        ]

        # 通过 plot 直接绘制 OBB 的边
        for edge in edges:
            ax.plot([corners[edge[0], 0], corners[edge[1], 0]], 
                    [corners[edge[0], 1], corners[edge[1], 1]], 
                    [corners[edge[0], 2], corners[edge[1], 2]], 
                    color='b')

class MoosasGraph:
    """
    图化模块
    用于将建筑空间转为结构化有向图
    1   将空间识别为定向包容盒(oriented bounding box)
        表征参数: 5维向量(length, )

        边表征参数：
            space-face：方向；面属性（floor wall roof）
            face-face：关系（相接、附着、属于   ）
        需要调整的地方：
            geo_out编号与xml一一对应，所以在重新生成geo后的编号也要调整，需要建立一个geo_out与geo_convex之间的索引字典

            获取新的xml的索引方式：
                感觉得重新调整一下输出xml的格式，先分割面生成新的geo_out再transform，要不然很麻烦
                
                创建面节点（geo_convex）
                创建基于原xml的标准图（）

    """
    def __init__(self):
        """初始化一个空的有向图、空void、空面"""
        self.graph = nx.DiGraph() 
        self.spaces = []
        self.faces = []
        self.positions = {}

    def graph_representation(self, geo_path, xml_path, _is_cleaned=True):
        """
            Parse .xml and associated .geo files and build the ADSIM graph
            Args:  
                geo_path(str): *.geo file path
                xml_path(str): *.xml file path
            Returns:
                graph
        """
        faces_id = []
        faces_category =[]
        faces_normal = []
        faces_vertices = []

        spaces_id = []
        spaces_area = []
        
        # 0.0   Initialize the read file
        faces_category, faces_id, faces_normal, faces_vertices, faces_holes = read_geo(geo_path)
        root = read_xml(xml_path)

        # 1   Create a dictionary mapping Uid and faceId, Adding face nodes (FROM .geo) and face edges (FROM .xml)
        dict_u = {}

        for elem in root.findall('face') + root.findall('wall') + root.findall('glazing') + root.findall('skylight'):
            face_id = elem.find('faceId').text
            uid = elem.find('Uid').text
            
            dict_u[uid] = [face_id]
            if face_id in faces_id:
                i = faces_id.index(face_id)
            else:
                print(f"Skipping edge addition: Face '{face_id}' does not exist.")
                continue

            face = {
                'category': faces_category[i],
                'id': faces_id[i],
                'normal': np.array(faces_normal[i]),
                'vertices': np.array(faces_vertices[i])
            }

            self.faces.append(face)
            
            obb_params = OBB.create_obb(np.array(faces_vertices[i]), np.array(faces_normal[i]))
            
            # OBB.plot_obb_and_points(face['vertices'], obb_params)
            
            face_params = {
                "v": face['vertices'], # 3D vertices of the OBB
                "c": obb_params['center'], # 3D center of the OBB
                "s": obb_params['scale'], # 3D scale of the OBB
                "r": obb_params['rotation'], # 3x3 rotation matrix
                "t": None, # face type: floor, wall, roof
                "k_h": None, # heat transfer index
                "shgc": None, # solar heat gain coefficient
                "r_l": None, # light refelectance
                "t_l": None, # light transmittance
            }

            if int(float(faces_category[i])) == 2:
                face_params["t"] = "airwall"

            if int(float(faces_category[i])) == 1:
                face_params["t"] = "window"

            self.graph.add_node(uid, node_type="face", face_params=face_params)

        for face in root.findall('face') + root.findall('wall') + root.findall('glazing') + root.findall('skylight'):
            
            uid = face.find('Uid').text
            glazing_element = face.find('glazingId')
            shading_element = face.find('shadingId')
            
            glazingid = glazing_element.text if glazing_element is not None else None
            shadingid = shading_element.text if shading_element is not None else None
      
            if glazingid is not None:

                glazings = glazingid.split()
                for glazing in glazings:
                    face_id = face.find('faceId').text
                    if face_id in faces_id:
                        if glazing in self.graph.nodes:
                            if "face_params" in self.graph.nodes[glazing]:
                                self.graph.add_edge(uid, glazing, attr='glazing')
                            else:
                                print(f"Skipping edge addition: Node glazing '{glazing}' does not defined.")
                        else:
                                print(f"Skipping edge addition: Node glazing '{glazing}' does not exist.")
                    else:
                        print(f"Skipping edge addition: Face '{face_id}' does not exist.")
                        continue
            if shadingid is not None:
                shadings = shadingid.split()
                for shading in shadings:
                    self.graph.add_edge(uid, shading, attr='shading')
                    self.graph.nodes[shading]["face_params"]["t"] = "shading"
                    
            neighbors = face.find('neighbor')

            if neighbors is not None:
                for edge in neighbors.findall('edge'):
                    edge_keys = edge.text.split()
                    for key in edge_keys:
                        self.graph.add_edge(uid, key)

        # 2  Adding space nodes and face-space edges
        for space in root.findall('space'):
            
            space_id = space.find('id').text.strip() 
            space_area = space.find('area')

            spaces_id.append(space_id)
            spaces_area.append(space_area)

            if space.find('is_void').text == 'False':  
                self.graph.add_node(space_id, node_type="space") 
            else:
                self.graph.add_node(space_id, node_type="void")
 

            # Find all <topology> nodes under the <space> node, add edges, and the surface attribute
            topology = space.find('topology')
            
            space_boundary_verts = []

            if topology is not None:
                floors = topology.find('floor/face')
                if floors is not None:
                    floors_id = floors.text
                    if floors_id in self.graph.nodes:
                        self.graph.nodes[floors_id]["face_params"]["t"] = "floor"
                        self.graph.add_edge(space_id, floors_id, attr='floor')
                        space_boundary_verts.append(self.graph.nodes[floors_id]["face_params"]["v"])
                    else:
                        print(f"Skipping edge addition: Node floor '{floors_id}' does not exist.")

                ceilings = topology.find('ceiling/face')
                if ceilings is not None:
                    ceilings_id = ceilings.text
                    if ceilings_id in self.graph.nodes:
                        self.graph.nodes[ceilings_id]["face_params"]["t"] = "floor"
                        self.graph.add_edge(space_id, ceilings_id, attr='ceiling')
                        space_boundary_verts.append(self.graph.nodes[ceilings_id]["face_params"]["v"])
                    else:
                        print(f"Skipping edge addition: Node ceiling '{ceilings_id}' does not exist.")

                walls = topology.findall('edge/wall')
                for wall in walls:
                    wall_id = wall.find('Uid').text
                    if wall_id in self.graph.nodes:
                        self.graph.nodes[wall_id]["face_params"]["t"] = "wall"
                        self.graph.add_edge(space_id, wall_id, attr='wall')
                        space_boundary_verts.append(self.graph.nodes[wall_id]["face_params"]["v"])
                    else:
                        print(f"Skipping edge addition: Node wall '{wall_id}' does not exist.")

            obb_params = OBB.create_obb(np.concatenate(space_boundary_verts, axis=0), np.array([0,0,1]))
            #OBB.plot_obb_and_points(np.concatenate(space_boundary_verts, axis=0), obb_params)

            space_params = {
                "c": obb_params['center'],
                "s": obb_params['scale'],
                "r": obb_params['rotation'],
                "a": space_area.text
            }

            self.graph.nodes[space_id]["space_params"] = space_params


        #3  clean the graph nodes without edges
        if _is_cleaned:
            for node in list(self.graph.nodes()):
                if self.graph.degree(node) == 0:
                    self.graph.remove_node(node)
                    print (f"Removing node: {node}")

    def draw_graph_3d(self, file_path, _fig_show =False):
        """绘制图结构的三维表示"""
        fig = plt.figure(figsize=(20, 10))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=30, azim=15)  # 设置仰角为30度，方位角为45度


        colors = {
            'window': '#FFBE7A',
            'shading': '#999999',
            'floor': '#82B0D2',
            'wall': '#8ECFC9',
            'airwall': '#E7DAD2',
            'space': '#FA7F6F',
            'void': 'white',
            None: 'white'  
        }
        
        # 绘制节点
        for node in self.graph.nodes():
            if 'face_params' in self.graph.nodes[node]:
                center = self.graph.nodes[node]['face_params']['c']
                
                node_type = self.graph.nodes[node]['face_params']['t']

                color = colors.get(node_type, 'brown')
                
                ax.scatter(center[0], center[1], center[2], 
                        c=color, s=25, edgecolors='k')

            if 'space_params' in self.graph.nodes[node]:
                center = self.graph.nodes[node]['space_params']['c']
                if self.graph.nodes[node]['node_type'] == 'void':
                    color = colors['void']
                else:
                    color = colors['space']
                ax.scatter(center[0], center[1], center[2], 
                        c=color, s=50, edgecolors='k')

        
        # 绘制边
        for edge in self.graph.edges():
            start_node, end_node = edge
            if ('face_params' in self.graph.nodes[start_node] and 
                'face_params' in self.graph.nodes[end_node]):
                
                start_pos = self.graph.nodes[start_node]['face_params']['c']
                end_pos = self.graph.nodes[end_node]['face_params']['c']

                # 获取边的属性
                edge_attr = self.graph.edges[edge].get('attr', 'default')
                edge_color = '#999999' if edge_attr == 'default' else 'orange'
                
                # 绘制边
                ax.plot([start_pos[0], end_pos[0]],
                    [start_pos[1], end_pos[1]],
                    [start_pos[2], end_pos[2]],
                    color=edge_color, linestyle='-', alpha=0.05)

            if ('space_params' in self.graph.nodes[start_node] and 
                'face_params' in self.graph.nodes[end_node]):
                
                start_pos = self.graph.nodes[start_node]['space_params']['c']
                end_pos = self.graph.nodes[end_node]['face_params']['c']

                # 获取边的属性
                edge_attr = self.graph.edges[edge].get('attr', 'default')
                edge_color = 'gray' 
                
                # 绘制边
                ax.plot([start_pos[0], end_pos[0]],
                    [start_pos[1], end_pos[1]],
                    [start_pos[2], end_pos[2]],
                    color=edge_color, linestyle='--', alpha=0.5)
                    
        # 添加图例

        x_vals, y_vals, z_vals = [], [], []
    
        for node in self.graph.nodes():
            if 'face_params' in self.graph.nodes[node]:
                center = self.graph.nodes[node]['face_params']['c']
                x_vals.append(center[0])
                y_vals.append(center[1])
                z_vals.append(center[2])

            if 'space_params' in self.graph.nodes[node]:
                center = self.graph.nodes[node]['space_params']['c']
                x_vals.append(center[0])
                y_vals.append(center[1])
                z_vals.append(center[2])   
        # 计算中心点和最大范围，确保 xyz 轴比例一致
        x_mid = (min(x_vals) + max(x_vals)) / 2
        y_mid = (min(y_vals) + max(y_vals)) / 2
        z_mid = (min(z_vals) + max(z_vals)) / 2
        max_range = max(max(x_vals) - min(x_vals), 
                        max(y_vals) - min(y_vals), 
                        max(z_vals) - min(z_vals)) / 2

        ax.set_xlim(x_mid - max_range, x_mid + max_range)
        ax.set_ylim(y_mid - max_range, y_mid + max_range)
        ax.set_zlim(z_mid - max_range, z_mid + max_range)

        # 确保 xyz 轴比例一致


        # 放大显示图形
        ax.dist = 5  # 减小该值可以放大图形，默认值通常是10
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                    markerfacecolor=v, label=k if k else 'face', 
                    markersize=8)
            for k, v in colors.items()
        ]
        #ax.legend(handles=legend_elements)
        
        plt.axis('off')
        ax.set_axis_off()
        #plt.title('Building Graph 3D Visualization')
        if _fig_show:
            plt.show()
        plt.savefig(file_path)
        plt.close()

    def nodes(self):
        """获取图中的所有节点"""
        return self.graph.nodes(data=True)

    def edges(self):
        """获取图中的所有边"""
        return self.graph.edges(data=True)
    
  
    def graph_representation_legacy(self, geo_path):
        
        # 为共享顶点分配唯一索引
        def assign_vertex_indices(faces_vertices):
            vertex_dict = {}
            vertex_index = 0
            faces_with_indices = []
            
            for vertices in faces_vertices:
                indexed_vertices = []
                for vertex in vertices:
                    vertex_tuple = tuple(vertex)
                    if vertex_tuple not in vertex_dict:
                        vertex_dict[vertex_tuple] = vertex_index
                        vertex_index += 1
                    indexed_vertices.append(vertex_dict[vertex_tuple])
                faces_with_indices.append(indexed_vertices)
            return faces_with_indices, vertex_dict

        # 优化后的共享顶点判断函数，使用索引比较
        def shared_vertices_by_index(face1, face2):
            vertices1 = set(face1['vertex_indices'])
            vertices2 = set(face2['vertex_indices'])
            shared_count = len(vertices1 & vertices2)  # 计算交集中的顶点数量
            return shared_count >= 2

    
        faces_category, faces_id, faces_normal, faces_vertices = convexify.read_geo(geo_path)

        
        faces_with_indices, vertex_dict = assign_vertex_indices(faces_vertices)

        # 初始化面集合
        for i in range(len(faces_id)):
            face = {
                'category': faces_category[i],
                'id': faces_id[i],
                'normal': np.array(faces_normal[i]),
                'vertices': np.array(faces_vertices[i]),  # 原始顶点
                'vertex_indices': faces_with_indices[i]    # 顶点索引
            }
            self.faces.append(face)

        # 为每个非 category=1 的面添加节点
        for face in self.faces:
            if face['category'] != 1:
                centroid = np.mean(face['vertices'], axis=0)
                self.face_graph.add_node(face['id'], pos=centroid)
                self.positions[face['id']] = centroid

        # 添加共享顶点的边
        for i, face1 in enumerate(self.faces):
            for j, face2 in enumerate(self.faces):
                if i != j and shared_vertices_by_index(face1, face2):
                    self.face_graph.add_edge(face1['id'], face2['id'])

