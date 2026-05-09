from __future__ import annotations

import json

import networkx as nx
from scipy.spatial.transform import Rotation as R

from ..utils import np, path, shapely

FACE_PARAM_TEMPLATE = {
    "t": None,
    "v": None,
    "c": None,
    "s": None,
    "r": None,
    "n": None,
    "l": 0,
}

SPACE_PARAM_TEMPLATE = {
    "c": None,
    "s": None,
    "r": None,
    "l": 0,
}


def create_obb(points, normal, min_scale=0.1):
    """
    Create an oriented bounding box (OBB) for a set of points.
    """
    points = np.asarray(points, dtype=float)
    normal = np.asarray(normal, dtype=float)
    if len(points) == 0:
        raise ValueError("points must not be empty")
    if np.linalg.norm(normal) <= 1e-8:
        normal = np.array([0.0, 0.0, 1.0], dtype=float)
    else:
        normal = normal / np.linalg.norm(normal)

    geometry = shapely.multipoints(points)
    z_axis = np.array([0.0, 0.0, 1.0], dtype=float)
    z_r = normal

    if np.abs(z_r[0]) <= 1e-3 and np.abs(z_r[1]) <= 1e-3:
        z_r = z_axis
        min_rotated_rectangle = shapely.minimum_rotated_rectangle(geometry)
        obb_coords = np.array(
            shapely.get_coordinates(min_rotated_rectangle, include_z=True)
        )[:-1]
        obb_coords = np.nan_to_num(obb_coords, nan=points[0, 2])
        obb_coords[:, 2] = (np.min(points[:, 2]) + np.max(points[:, 2])) / 2

        if len(obb_coords) <= 2:
            centroid = np.mean(points, axis=0)
            x_r = np.array([1.0, 0.0, 0.0], dtype=float)
            y_r = np.array([0.0, 1.0, 0.0], dtype=float)
            rotation_matrix = R.from_matrix(np.array([x_r, y_r, z_r])).as_matrix()
            l = max(np.ptp(points[:, 0]), min_scale)
            w = max(np.ptp(points[:, 1]), min_scale)
            h = max(np.ptp(points[:, 2]), min_scale)
            original_obb_centroid = centroid
        else:
            x_vec = obb_coords[1] - obb_coords[0]
            y_vec = obb_coords[3] - obb_coords[0]

            x_norm = np.linalg.norm(x_vec)
            y_norm = np.linalg.norm(y_vec)
            x_r = x_vec / x_norm if x_norm > 1e-6 else np.array([1.0, 0.0, 0.0], dtype=float)
            y_r = y_vec / y_norm if y_norm > 1e-6 else np.array([0.0, 1.0, 0.0], dtype=float)

            rotation_matrix = R.from_matrix(np.array([x_r, y_r, z_r])).as_matrix()
            l = max(np.linalg.norm(obb_coords[1] - obb_coords[0]), min_scale)
            w = max(np.linalg.norm(obb_coords[3] - obb_coords[0]), min_scale)
            h = max(np.max(points[:, 2]) - np.min(points[:, 2]), min_scale)
            original_obb_centroid = np.mean(obb_coords, axis=0)
    else:
        x_r = np.cross(z_r, z_axis)
        if np.linalg.norm(x_r) <= 1e-8:
            x_r = np.array([1.0, 0.0, 0.0], dtype=float)
        else:
            x_r = x_r / np.linalg.norm(x_r)

        y_r = np.cross(z_r, x_r)
        if np.linalg.norm(y_r) <= 1e-8:
            y_r = np.array([0.0, 1.0, 0.0], dtype=float)
        else:
            y_r = y_r / np.linalg.norm(y_r)

        rotation_matrix = R.from_matrix(np.array([x_r, y_r, z_r])).as_matrix()
        rotated_points = points.dot(rotation_matrix.T)

        l = max(np.ptp(rotated_points[:, 0]), min_scale)
        w = max(np.ptp(rotated_points[:, 1]), min_scale)
        h = max(np.ptp(rotated_points[:, 2]), min_scale)

        centroid = np.mean(
            [
                [
                    np.min(rotated_points[:, 0]),
                    np.min(rotated_points[:, 1]),
                    np.min(rotated_points[:, 2]),
                ],
                [
                    np.max(rotated_points[:, 0]),
                    np.max(rotated_points[:, 1]),
                    np.max(rotated_points[:, 2]),
                ],
            ],
            axis=0,
        )
        original_obb_centroid = np.dot(centroid, rotation_matrix)

    return {
        "center": original_obb_centroid,
        "scale": np.array([l, w, h], dtype=float),
        "rotation": rotation_matrix,
    }


def _split_tokens(value: str | None) -> list[str]:
    if value is None:
        return []
    return [token for token in value.split() if token]


def _parse_vector(text: str | None) -> np.ndarray | None:
    tokens = _split_tokens(text)
    if not tokens:
        return None
    try:
        return np.array([float(token) for token in tokens], dtype=float)
    except ValueError:
        return None


def _geometry_lookup(model) -> dict[str, dict]:
    lookup = {}
    for geo in model.geometryList:
        rings = shapely.get_rings(geo.face)
        boundary = np.array(
            shapely.get_coordinates(rings[0], include_z=True)[:-1],
            dtype=float,
        )
        normal = np.array(
            shapely.get_coordinates(geo.normal, include_z=True)[0],
            dtype=float,
        )
        lookup[geo.faceId] = {
            "face_id": geo.faceId,
            "category": int(float(geo.category)),
            "vertices": boundary,
            "normal": normal,
            "area": float(shapely.area(geo.face)),
        }
    return lookup


def _resolve_geometries(face_ids: list[str], geo_lookup: dict[str, dict]) -> list[dict]:
    return [geo_lookup[face_id] for face_id in face_ids if face_id in geo_lookup]


def _primary_geometry(geometries: list[dict]) -> dict | None:
    if not geometries:
        return None
    return max(geometries, key=lambda item: item["area"])


def _node_type_from_categories(categories: list[int], current_type: str | None = None) -> str | None:
    if any(cat == 2 for cat in categories):
        return "airwall"
    if any(cat in (1, 5, 6) for cat in categories):
        return "window"
    return current_type


class NumpyEncoder(json.JSONEncoder):
    """
    JSON encoder that handles numpy arrays and scalar types.
    """

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        return super().default(obj)


class MoosasGraph:
    """
    Graph module that converts building spaces into a structured graph representation.
    """

    def __init__(self):
        self.graph = nx.Graph()

    def nodes(self):
        return self.graph.nodes(data=True)

    def edges(self):
        return self.graph.edges(data=True)

    def graph_representation_from_model(self, root, geo_lookup):
        uid_to_face_ids = {}
        face_elements = {}

        face_like_elements = (
            list(root.findall("face"))
            + list(root.findall("wall"))
            + list(root.findall("glazing"))
            + list(root.findall("skylight"))
        )

        for element in face_like_elements:
            uid = element.findtext("Uid")
            if not uid:
                continue
            uid_to_face_ids[uid] = _split_tokens(element.findtext("faceId"))
            face_elements[uid] = element
            self.graph.add_node(
                uid,
                node_type="face",
                face_params=FACE_PARAM_TEMPLATE.copy(),
            )

        for space in root.findall("space"):
            sid = space.findtext("id")
            if not sid:
                continue
            is_void = space.findtext("is_void") == "True"
            self.graph.add_node(
                sid,
                node_type="void" if is_void else "space",
                space_params=SPACE_PARAM_TEMPLATE.copy(),
            )

        for element in face_like_elements:
            uid = element.findtext("Uid")
            if not uid:
                continue
            neighbors = element.find("neighbor")
            if neighbors is None:
                continue
            for edge in neighbors.findall("edge"):
                for neighbor_uid in _split_tokens(edge.text):
                    if neighbor_uid in self.graph:
                        self.graph.add_edge(uid, neighbor_uid, adj="adjacent")

        for element in list(root.findall("face")) + list(root.findall("wall")):
            uid = element.findtext("Uid")
            if not uid:
                continue
            for glazing_uid in _split_tokens(element.findtext("glazingId")):
                if glazing_uid in self.graph:
                    self.graph.add_edge(uid, glazing_uid, adj="glazing")

        for space in root.findall("space"):
            sid = space.findtext("id")
            if not sid or sid not in self.graph:
                continue
            topology = space.find("topology")
            if topology is None:
                continue

            for floor in topology.findall("floor/face"):
                floor_id = floor.text
                if floor_id in self.graph.nodes:
                    self.graph.nodes[floor_id]["face_params"]["t"] = "floor"
                    self.graph.add_edge(sid, floor_id, attr="floor", layer=0)

            for ceiling in topology.findall("ceiling/face"):
                ceiling_id = ceiling.text
                if ceiling_id in self.graph.nodes:
                    self.graph.nodes[ceiling_id]["face_params"]["t"] = "floor"
                    self.graph.add_edge(sid, ceiling_id, attr="ceiling", layer=0)

            for wall in topology.findall("edge/wall"):
                wall_id = wall.findtext("Uid")
                if wall_id in self.graph.nodes:
                    self.graph.nodes[wall_id]["face_params"]["t"] = "wall"
                    self.graph.add_edge(sid, wall_id, attr="wall", layer=0)

        for nodeid, node in self.graph.nodes(data=True):
            if node.get("node_type") == "face":
                geometries = _resolve_geometries(uid_to_face_ids.get(nodeid, []), geo_lookup)
                primary_geometry = _primary_geometry(geometries)
                if primary_geometry is None:
                    continue

                combined_vertices = np.concatenate(
                    [geometry["vertices"] for geometry in geometries],
                    axis=0,
                )
                face_normal = _parse_vector(face_elements[nodeid].findtext("normal"))
                if face_normal is None:
                    face_normal = primary_geometry["normal"]

                obb = create_obb(combined_vertices, face_normal)
                current_type = node["face_params"].get("t")
                node["face_params"].update(
                    {
                        "t": _node_type_from_categories(
                            [geometry["category"] for geometry in geometries],
                            current_type=current_type,
                        ),
                        "v": primary_geometry["vertices"],
                        "c": obb["center"],
                        "s": obb["scale"],
                        "r": obb["rotation"],
                        "n": face_normal,
                    }
                )

            if node.get("node_type") in ("space", "void"):
                boundary_verts = []
                for fid in self.graph.neighbors(nodeid):
                    edge_data = self.graph.get_edge_data(nodeid, fid)
                    if edge_data is None:
                        continue
                    if edge_data.get("attr") not in ("floor", "ceiling", "wall"):
                        continue
                    face_params = self.graph.nodes[fid].get("face_params", {})
                    if face_params.get("v") is not None:
                        boundary_verts.append(face_params["v"])

                if not boundary_verts:
                    continue

                verts = np.concatenate(boundary_verts, axis=0)
                obb = create_obb(verts, np.array([0.0, 0.0, 1.0], dtype=float))
                node["space_params"].update(
                    {
                        "c": obb["center"],
                        "s": obb["scale"],
                        "r": obb["rotation"],
                    }
                )

        return self.graph

    def clean_isolated_nodes(self):
        for node in list(self.graph.nodes()):
            if self.graph.degree(node) == 0:
                self.graph.remove_node(node)

    def clean_airwall_nodes(self):
        airwalls = [
            node_id
            for node_id, data in self.graph.nodes(data=True)
            if data.get("node_type") == "face"
            and data.get("face_params", {}).get("t") == "airwall"
        ]

        for airwall in airwalls:
            if airwall not in self.graph:
                continue

            neighbors = list(self.graph.neighbors(airwall))
            for neighbor in neighbors:
                if neighbor == airwall:
                    continue

                neighbor_data = self.graph.nodes[neighbor]
                if (
                    neighbor_data.get("node_type") == "face"
                    and neighbor_data.get("face_params", {}).get("t") == "airwall"
                ):
                    continue

                for next_neighbor in list(self.graph.neighbors(neighbor)):
                    if next_neighbor in (airwall, neighbor):
                        continue

                    edge_data = dict(self.graph.get_edge_data(neighbor, next_neighbor) or {})
                    if not self.graph.has_edge(airwall, next_neighbor):
                        self.graph.add_edge(airwall, next_neighbor, **edge_data)

                if self.graph.has_edge(airwall, neighbor):
                    self.graph.remove_edge(airwall, neighbor)

                if neighbor in self.graph:
                    self.graph.remove_node(neighbor)

    def embed_outer_layer_edges(self, max_layers: int = 3):
        for node, data in self.graph.nodes(data=True):
            if data.get("node_type") == "face":
                data["face_params"]["l"] = 0
            if data.get("node_type") in ["space", "void"]:
                data["space_params"]["l"] = 0

        graph = self.graph
        layer = 1
        temp_graph = graph.copy()

        while layer <= max_layers:
            candidates = set()
            for node, data in temp_graph.nodes(data=True):
                if data.get("node_type") != "face":
                    continue
                connected_spaces = [
                    neighbor
                    for neighbor in temp_graph.neighbors(node)
                    if temp_graph.nodes[neighbor].get("node_type") == "space"
                ]
                if len(connected_spaces) == 1:
                    candidates.add(node)

            current_layer_faces = set()
            for face_node in candidates:
                if layer == 1:
                    current_layer_faces.add(face_node)
                    continue

                face_data = temp_graph.nodes[face_node]
                face_type = face_data.get("face_params", {}).get("t")
                is_self_transparent = face_type in ["window", "airwall"]

                has_transparent_neighbor = False
                if not is_self_transparent:
                    for neighbor in temp_graph.neighbors(face_node):
                        neighbor_data = temp_graph.nodes[neighbor]
                        if neighbor_data.get("node_type") != "face":
                            continue
                        neighbor_type = neighbor_data.get("face_params", {}).get("t")
                        edge_data = temp_graph.get_edge_data(face_node, neighbor)
                        if (
                            neighbor_type in ["window", "airwall"]
                            and edge_data
                            and edge_data.get("adj") in ["adjacent", "glazing"]
                        ):
                            has_transparent_neighbor = True
                            break

                if is_self_transparent or has_transparent_neighbor:
                    current_layer_faces.add(face_node)

            transparent_nodes = set()
            for face_node in current_layer_faces:
                for neighbor in temp_graph.neighbors(face_node):
                    neighbor_data = temp_graph.nodes[neighbor]
                    if neighbor_data.get("node_type") != "face":
                        continue
                    face_type = neighbor_data.get("face_params", {}).get("t")
                    edge_data = temp_graph.get_edge_data(face_node, neighbor)
                    if (
                        face_type in ["window", "airwall"]
                        and edge_data
                        and edge_data.get("adj") in ["adjacent", "glazing"]
                    ):
                        transparent_nodes.add(neighbor)

            current_layer_faces.update(transparent_nodes)
            if not current_layer_faces:
                break

            for face_node in current_layer_faces:
                graph.nodes[face_node]["face_params"]["l"] = layer

            for face_node in current_layer_faces:
                for neighbor in graph.neighbors(face_node):
                    if graph.nodes[neighbor].get("node_type") != "space":
                        continue
                    graph.nodes[neighbor]["space_params"]["l"] = layer
                    if graph.has_edge(neighbor, face_node):
                        graph[neighbor][face_node]["layer"] = layer

            remove_nodes = set()
            for node in temp_graph.nodes:
                node_data = temp_graph.nodes[node]
                if (
                    node_data.get("node_type") == "space"
                    and graph.nodes[node]["space_params"]["l"] == layer
                ):
                    remove_nodes.add(node)
                if node_data.get("node_type") == "face":
                    face_type = node_data.get("face_params", {}).get("t")
                    if (
                        face_type in ["window", "airwall"]
                        and graph.nodes[node]["face_params"]["l"] == layer
                    ):
                        remove_nodes.add(node)

            temp_graph.remove_nodes_from(remove_nodes)
            layer += 1

        return self.graph

    def graph_edit(
        self,
        _isolated_clean=True,
        _airwall_clean=True,
        _outer_layer_edge_embedding=True,
    ):
        if _isolated_clean:
            self.clean_isolated_nodes()

        if _airwall_clean:
            self.clean_airwall_nodes()

        if _outer_layer_edge_embedding:
            self.embed_outer_layer_edges()

        return self.graph


def graph_to_dict(graph: MoosasGraph) -> dict:
    nodes_data = {}
    for node_id, node_attrs in graph.graph.nodes(data=True):
        node_data = {}
        for key, value in node_attrs.items():
            if isinstance(value, dict):
                node_data[key] = {
                    sub_key: sub_value.tolist() if isinstance(sub_value, np.ndarray) else sub_value
                    for sub_key, sub_value in value.items()
                }
            else:
                node_data[key] = value.tolist() if isinstance(value, np.ndarray) else value
        nodes_data[str(node_id)] = node_data

    edges_list = []
    for u, v, edge_attrs in graph.graph.edges(data=True):
        edges_list.append(
            {
                "source": str(u),
                "target": str(v),
                "attributes": edge_attrs,
            }
        )

    return {
        "nodes": nodes_data,
        "edges": edges_list,
    }


def buildGraph(
    model,
    clean_isolated=True,
    clean_airwall=True,
    outer_layer_edge_embedding=True,
) -> MoosasGraph:
    graph = MoosasGraph()
    graph.graph_representation_from_model(
        model.buildXml(writeGeometry=False),
        _geometry_lookup(model),
    )
    graph.graph_edit(
        _isolated_clean=clean_isolated,
        _airwall_clean=clean_airwall,
        _outer_layer_edge_embedding=outer_layer_edge_embedding,
    )
    return graph


def writeGraph(
    file_path,
    model,
    clean_isolated=True,
    clean_airwall=True,
    outer_layer_edge_embedding=True,
) -> str:
    """
    Write the building graph to a JSON file directly from a Moosas model.
    """
    path.checkBuildDir(file_path)
    graph = buildGraph(
        model,
        clean_isolated=clean_isolated,
        clean_airwall=clean_airwall,
        outer_layer_edge_embedding=outer_layer_edge_embedding,
    )
    graph_data = graph_to_dict(graph)
    json_object = json.dumps(graph_data, indent=4, cls=NumpyEncoder)
    with open(file_path, "w", encoding="utf-8") as outfile:
        outfile.write(json_object)
    return json_object
