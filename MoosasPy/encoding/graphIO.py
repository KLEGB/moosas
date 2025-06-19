"""
    This is the i/o module of encodling and representation algorithm. Different from the Moosas+ i/o module, this algorithm do not use pygeos to process geometry !!!
"""
import sys
import os
import numpy as np
import xml.etree.ElementTree as ET
import json
import networkx as nx
from pathlib import Path

def read_geo(file_path):
    """
    读取.geo文件，返回分类、编号、法向量和多边形面的坐标数组.

    Parameters:
        file_path (str): 文件路径.

    Returns:
        tuple: 包含分类、编号、法向量和多边形面的信息.
    """
    cat, idd, normal, faces, holes = [], [], [], [], []

    try:
        with open(file_path, "r", encoding='utf-8') as f:
            read = f.readline().strip()
            
            while read != '':
                if read.startswith("f,"):
                    # Parse the category (opaque, translucent, air wall) and face ID
                    parts = read.split(',')
                    cat.append(str(parts[1]))  # 0, 1, or 2 for category
                    idd.append(str(parts[2]))  # Face ID
                    read = f.readline().strip()
                    continue

                if read.startswith("fn,"):
                    # Parse normal vector (x, y, z)
                    normal_parts = read.split(',')
                    normal_t = np.array([float(normal_parts[1]), float(normal_parts[2]), float(normal_parts[3])])
                    normal.append(normal_t)
                    read = f.readline().strip()
                    continue

                if read.startswith("fv,"):
                    # Parse face vertices
                    vertices = []
                    while read.startswith("fv,"):
                        vertex_parts = read.split(',')
                        vertex = np.array([float(vertex_parts[1]), float(vertex_parts[2]), float(vertex_parts[3])])
                        vertices.append(vertex)
                        read = f.readline().strip()
                    
                    faces.append(np.array(vertices))  # Store face coordinates as arrays
                    holes.append(None)  # Add None for holes if no fh is found
                    continue
                
                if read.startswith("fh,"):
                    # Parse hole vertices in face
                    current_face_holes = {}  # 为每个面创建新的字典
                    while read.startswith("fh,"):
                        vertex_parts = read.split(',')
                        hole_id = int(vertex_parts[1])  # Parse hole ID
                        vertex = np.array([float(vertex_parts[2]), float(vertex_parts[3]), float(vertex_parts[4])])
                        if hole_id not in current_face_holes:
                            current_face_holes[hole_id] = []  
                        current_face_holes[hole_id].append(vertex)
                        read = f.readline().strip()
                    holes[-1] = current_face_holes.copy()  # Replace None with actual holes data
                    continue

                # Read next line
                read = f.readline().strip()



    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    
    for face_holes in holes:
        if face_holes is not None:
            for hole_id in face_holes:
                face_holes[hole_id] = np.array(face_holes[hole_id])
    
    # Return the parsed data
    return np.array(cat), idd, np.array(normal), faces, holes

def write_geo(file_path, cat, idd, normal, faces):
    """
    将分类、编号、法向量和多边形面的信息写入.geo文件。

    Parameters:
        output_file_path (str): 输出文件路径.
        cat (list): 分类列表.
        idd (list): 编号列表.
        normal (list): 法向量列表.
        faces (list): 多边形面信息列表.
    """
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            for i in range(len(cat)):
                # Write face category and ID
                f.write(f"f,{cat[i]},{idd[i]}\n")
                
                # Write normal vector
                normal_vector = normal[i]
                f.write(f"fn,{normal_vector[0]},{normal_vector[1]},{normal_vector[2]}\n")
                
                # Write face vertices
                for vertex in faces[i]:
                    f.write(f"fv,{vertex[0]},{vertex[1]},{vertex[2]}\n")
                
                
                # Write a separator if it's not the last face
                if i != len(cat) - 1:
                    f.write(";\n")
    
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")

def read_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root

def write_adjson (file_path, data):
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(data)
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")

def read_adjson (file_path):
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            data = f.read()
            return data
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

class NumpyEncoder(json.JSONEncoder):
    """处理 numpy 数组的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32):
            return float(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        return super().default(obj)

def graph_to_json(graph, output_dir):
    """导出图数据到JSON文件"""
    # 准备节点数据
    nodes_data = {}
    for node_id, node_attrs in graph.graph.nodes(data=True):
        # 深拷贝并转换所有numpy数据
        node_data = {}
        for key, value in node_attrs.items():
            if isinstance(value, dict):
                node_data[key] = {k: v.tolist() if isinstance(v, np.ndarray) else v 
                                 for k, v in value.items()}
            else:
                node_data[key] = value.tolist() if isinstance(value, np.ndarray) else value
        nodes_data[str(node_id)] = node_data
    
    # 准备边数据
    edges_data = {}
    for u, v, edge_attrs in graph.graph.edges(data=True):
        edge_id = f"{u}_{v}"
        edges_data[edge_id] = {
            "source": str(u),
            "target": str(v),
            "attributes": edge_attrs
        }
    
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    with open(output_path / "nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes_data, f, indent=4, cls=NumpyEncoder)
    
    with open(output_path / "edges.json", "w", encoding="utf-8") as f:
        json.dump(edges_data, f, indent=4, cls=NumpyEncoder)

def json_to_graph(input_dir):
    """从JSON文件读取并重建图数据
    
    Parameters:
        input_dir (str): JSON文件所在的目录路径
        
    Returns:
        nx.Graph: 重建的NetworkX图对象
    """
    input_path = Path(input_dir)
    
    # 读取节点数据
    with open(input_path / "nodes.json", "r", encoding="utf-8") as f:
        nodes_data = json.load(f)
    
    # 读取边数据
    with open(input_path / "edges.json", "r", encoding="utf-8") as f:
        edges_data = json.load(f)
    
    # 创建新的NetworkX图
    G = nx.Graph()
    
    # 添加节点和属性
    for node_id, node_attrs in nodes_data.items():
        # 将列表数据转换回numpy数组
        processed_attrs = {}
        for key, value in node_attrs.items():
            if isinstance(value, dict):
                # 处理嵌套字典
                processed_attrs[key] = {k: np.array(v) if isinstance(v, list) else v 
                                     for k, v in value.items()}
            else:
                # 处理普通属性
                processed_attrs[key] = np.array(value) if isinstance(value, list) else value
        G.add_node(node_id, **processed_attrs)
    
    # 添加边和属性
    for edge_id, edge_data in edges_data.items():
        source = edge_data["source"]
        target = edge_data["target"]
        attributes = edge_data["attributes"]
        G.add_edge(source, target, **attributes)
    
    return G



