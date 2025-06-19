import os
from .convexify import MoosasConvexify
from .graph import MoosasGraph
from .graphIO import read_geo, write_geo

# from ..transformation import transform


def convex_temp():
    cat, idd, normal, faces, holes = read_geo(input_geo_path)
    convex_idd, convex_normal, convex_faces = MoosasConvexify.convexify_faces(idd, normal, faces,
                                                                                          holes)
    write_geo(output_geo_path, convex_idd, convex_normal, convex_faces)


def graph_temp():
    graph = MoosasGraph()
    graph.graph_representation_xml(output_geo_path, input_xml_path)
    graph.draw_graph_3d()
#main
if __name__ == '__main__':
    user_profile = os.environ['USERPROFILE']

    input_geo_path = rf"{user_profile}/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/data/geometry/selection0_out.geo"

    input_xml_path = rf"{user_profile}/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/data/geometry/selection0.xml"

    output_geo_path = "D:/BaiduSyncdisk/Research/202410MOOSAS+/BuildingConvex/data/selection0_convex.geo"
    output_xml_path = "D:/BaiduSyncdisk/Research/202410MOOSAS+/BuildingConvex/data/selection0_convex.xml"

    convex_temp()
    graph_temp()
