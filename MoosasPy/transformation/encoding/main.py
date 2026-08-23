import os
from ..geometry.convexify import MoosasConvexify
from .graph import MoosasGraph
from .graphIO import read_geo, write_geo

# from ..transformation import transform


def convex_temp():
    """
    Apply convexification to geometric data read from a file and write the result to another file.
    
    Parameters
    ----------
    None : 
        This function does not take any parameters. It uses global variables `input_geo_path` and `output_geo_path` 
        to specify the input and output file paths, respectively.
    
    Returns
    -------
    None
        This function does not return any value. It performs file reading, convexification of faces, and file writing as side effects.
    """
    cat, idd, normal, faces, holes = read_geo(input_geo_path)
    convex_cat, convex_idd, convex_normal, convex_faces, _ = MoosasConvexify.convexify_faces(
        cat,
        idd,
        normal,
        faces,
        holes,
    )
    write_geo(output_geo_path, convex_cat, convex_idd, convex_normal, convex_faces)


def graph_temp():
    """Create and visualize a 3D graph from XML representation.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
        This function does not return any value. It generates and displays a 3D graph as a side effect.
    """
    graph = MoosasGraph()
    graph.graph_representation_xml(output_geo_path, input_xml_path)
    graph.draw_graph_3d()
#main
if __name__ == '__main__':
    user_profile = os.environ['USERPROFILE']

    input_geo_path = ""

    input_xml_path = ""

    output_geo_path = ""
    output_xml_path = ""

    convex_temp()
    graph_temp()
