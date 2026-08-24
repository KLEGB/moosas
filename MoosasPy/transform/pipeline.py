"""Main func of Moosas Geometry Transformation
Licence: Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.
More information of this function:
https://doi.org/10.1007/s12273-023-1081-6
"""
from __future__ import annotations

import os
import os.path
import sys
import time

import shapely

from .stages.assembly import assemble_model, pack_model
from .stages.classification import classify_model
from .stages.cleansing import cleanse_model
from .stages.finalization import attach_shading_content, finalize_model
from .stages.generation import generate_space_boundaries
from .stages.glazing import attach_glazing_to_faces, match_face_glazing
from .stages.options import TransformOptions
from .stages.splitting import prepare_divided_zones, split_wall_intersections
from .stages.topology import build_face_topology, build_space_topology
from .stages.validation import validate_model
from .geometry.convexify import convexify_model
from .geometry.standardize import standardize_model
from .geometry.air_boundary import copy_air_boundaries
from .io import load_model as loadModel
from .io import model_from_file as modelFromFile
from .io import save_model as saveModel
from .geometry.cleanse import *
from .geometry.contour import packing_edges, outerBoundary
from .geometry.element import MoosasEdge, MoosasFace, MoosasFloor, MoosasGeometry, MoosasSpace
from .geometry.geos import *
from .geometry.spaceGen import CCRSpaceGeneration
from ..models import MoosasModel
from ..model_resources import configure_model_resources
from ..utils import mixItemListToList
from ..utils.constant import geom
from ..utils.tools import searchBy, path


def complete_topology(model: MoosasModel) -> MoosasModel:
    """Attach glazing and rebuild topology for a model loaded by an I/O adapter."""
    attached_glazing = sum(
        len(getattr(element, "glazingElement", []))
        for elements in (getattr(model, "wallList", []), getattr(model, "faceList", []))
        for element in elements
    )
    glazing_count = len(getattr(model, "glazingList", [])) + len(getattr(model, "skylightList", []))
    if glazing_count and attached_glazing == 0:
        model = attach_glazing_to_faces(model)
    model = build_space_topology(model, True)
    return build_face_topology(model)


def load_model(file_path: str, save_type: str | None = None, **kwargs) -> MoosasModel:
    """Load a model through an I/O adapter, then configure and complete it."""
    from .io import load_model as load_model_file

    model = load_model_file(file_path, save_type, **kwargs)
    configure_model_resources(model)
    return complete_topology(model)


def transform(input_path: str, input_type: str = None,
              output_path: str = None, output_type: str = None,
              method=CCRSpaceGeneration,
              options: TransformOptions = TransformOptions(),
              stdout=sys.stdout) -> MoosasModel:
    """
    Convert geometric data to structured spatial model with optional processing.

    Parameters
    ----------
    input_path : str
        Path to input geometry file. Supported formats:
        - *.obj : Wavefront OBJ format
        - *.xml : Custom XML structure
        - *.stl : STL format (future support)
        - *.geo : Stream format (future support)

    output_path : str, optional
        Output path for structured spatial data. Supported formats:
        - *.spc : Steam format with space/element descriptions
        - *.xml : Tree-structured XML format
        - *.json : JSON equivalent of XML structure
        - *.idf : EnergyPlus input with default thermal settings
        - *.rdf : RDF knowledge graph (Turtle format)

    input_type : str, optional
        Explicit input format specification (e.g., 'obj', 'xml').
        Auto-detected from input_path suffix if None.

    output_type : str, optional
        Explicit output format specification.
        Auto-detected from output_path suffix if None.

    method : callable, optional
        Space generation algorithm (default: CCRSpaceGeneration). Options:
        - VFGSpaceGeneration (L. Jones 2013)
        - BTGSpaceGeneration (H. Chen 2018)
        - CCRSpaceGeneration (J. Xiao 2023)

    options : TransformOptions, optional
        Shared configuration for classification, cleansing, assembly, and finalization.

    stdout : object, optional
        Output stream for transformation logs (default: sys.stdout).

    Returns
    -------
    MoosasModel
        Structured spatial model with properties (More information could be found in models module):
        - spacesList : List[MoosasSpace] - Spatial units with thermal properties
        - wallList : List[MoosasWall] - Architectural components
        - buildingTemplate : dict -  dictionary of the termal building templates and properties
        - weather : MoosasWeather - weather object and information

    Examples
    --------
    >>> from MoosasPy.transform.geometry.spaceGen import CCRSpaceGeneration
    >>> model = transform('test.obj', method=CCRSpaceGeneration)
    >>> model.save('output.xml', fmt='xml')

    Energy analysis example:
    >>> from MoosasPy import energyAnalysis
    >>> results = energyAnalysis(model)
    >>> print(f"Total energy demand: {results['total']['cooling'] + results['total']['heating']} kWh")

    Notes
    -----
    1. For RDF/XML output, use `.saveModel()` instead of output_path
    2. IDF generation includes default thermal settings from ASHRAE 90.1
    3. Geometry standardization reduces model fidelity for simulation efficiency
    """

    # redirect stdout
    if isinstance(stdout, str):
        if os.path.isfile(stdout):
            stdout = open(stdout, 'w+')
    sysout = sys.stdout
    sys.stdout = stdout
    t0 = time.time()
    # load model from file
    print('LOADING: ', end='')
    model = modelFromFile(input_path, input_type)
    configure_model_resources(model)
    print('import face number:', len(model.geoId))

    if model is None:  # zero len space will cause serve errors
        return

    # transformation
    model = structured(model, options=options, generation_method=method, t0=t0)

    # export the model
    if output_path is not None:
        if isinstance(output_path, str):
            saveModel(model, output_path, output_type)
        else:
            for oP, oS in zip(output_path, output_type):
                saveModel(model, oP, oS)

    sys.stdout = sysout
    # print(len(model.spaceList))
    # print(len(model.voidList))
    # input()
    return model


def structured(
    model: MoosasModel,
    *,
    options: TransformOptions = TransformOptions(),
    generation_method=CCRSpaceGeneration,
    t0=0,
) -> MoosasModel:
    """
    Convert a draft model with unstructured geometric data to structured spatial model with optional processing.

    Parameters
    ----------
    model : MoosasModel
        a model only include geometry information (model.geometryList)


    generation_method : callable, optional
        Space generation algorithm (default: CCRSpaceGeneration). Options:
        - VFGSpaceGeneration (L. Jones 2013)
        - BTGSpaceGeneration (H. Chen 2018)
        - CCRSpaceGeneration (J. Xiao 2023)

    options : TransformOptions, optional
        Shared configuration for all transformation stages.

    Returns
    -------
    MoosasModel
        Structured spatial model with properties (More information could be found in models module):
        - spacesList : List[MoosasSpace] - Spatial units with thermal properties
        - wallList : List[MoosasWall] - Architectural components
        - buildingTemplate : dict -  dictionary of the termal building templates and properties
        - weather : MoosasWeather - weather object and information

    """
    if model is None:  # zero len space will cause several errors
        return

    did_convexify = False
    while True:
        t1 = time.time()

        model = classify_model(model, options.triangulate_faces, options.break_wall_vertical)

        model.faceList = np.array(model.faceList)
        model.wallList = np.array(model.wallList)
        model.glazingList = np.array(model.glazingList)

        model, originalWall = cleanse_model(
            model,
            solve_duplicated=options.solve_duplicated,
            solve_redundant=options.solve_redundant,
            solve_overlap=options.solve_overlap,
            match_glazing=attach_glazing_to_faces,
        )
        model = split_wall_intersections(model, options.break_wall_horizontal)
        t2 = time.time()
        t3 = time.time()

        if options.divided_zones and not did_convexify:
            model = convexify_model(model)
            did_convexify = True
            continue

        break

    """Floor identification of closed areas: // This is the hatch algorithm of AutoCAD, and the effect is average 
    when there are too many chaotic lines, so it is necessary to add the impurity removal process 
    1. Organize the list for each floor: vec_list & node_list 

        1.1 Clear Isolated Lines and Generate ----vec_list-> [Point 
        Coordinates][Line ID][Point Coordinates] 
            1.1.1 Take out the vertices of wall.force_2d() into vec_list->[point 
            coordinates][line id]; The point coordinate retains the decimal point according to the tolerance 
            ****Important:Each line will appear twice, 
            respectively at the point 1 = the beginning of the line / the point 1 = the end of the line **** 
            1.1.2 For each line, look for the lines it adjaces: Extract the endpoints, traverse the same number 
            of vec_list endpoints< delete the line segment if 2; 
            1.1.3 Regenerate vec_list->[point coordinates][line id][point coordinates] 

        1.2 Generate vertex association vertices----node_list->[[Point 1, Point 2, Point 3...], 
        [Point 4, Point 5, Point 6...],...] 
            1.2.1 Group the vec_list into 1 sub-axis (point 1 coordinate) axis 
            3----node_list-> [[point coordinate 1, point coordinate 2, point coordinate 3...], [point coordinate 4, 
            point coordinate 5, point coordinate 6...],...] Save point coordinates location_list-> [point 1 coordinates, 
            point 2 coordinates...] 
            1.2.2 Calculate the quadrant angle of each sub-array point-to-point, in order to speed up 
            the calculation, directly use the method of [1,0] point multiplication + quadrant, see vector.angle()() for 
            details; 
            1.2.3 Sort node_list-> according to angle [[dot 1, dot 2, dot 3...], [dot 4, dot 5, dot 6...],
            ...] (Let the row with a small angle be in front of it, speed up the traversal) 

        1.3 Translate all coordinates into numbers according to location_list 
            1.3.1 Traversal location_list.index() to update vec_list->[dot id][line id][dot id] 
            1.3.2 Traversing location_list.index() to update node_list->[[1,2,3...],[4,5,6...],...] 

    2. According 
        to the sorted node_list, use the depth-first search + right-hand spiral rule to find the smallest closed area: 
        bound_list 
        2.1 Use breadth-first search for large area grouping of node_list 

        2.2 Find the maximum closed profile 
        bound for each large area and merge into the bound_list https://www.bilibili.com/video/BV1E44y1N75e/ 
            2.2.1 Find the point with the largest x value, 
            take the vector.angle()() with the smallest target as the starting direction, 
            and record the source direction vec_last 
            2.2.2 Find the smallest line angular to the last_node_vec vector.angle()() 
            for the next direction, update the vec_last 
            2.2.3 Repeat until you return to the original point 

        2.3 Determine whether the contour in the bound_list contains points (geos.contains), 
        and use this point to cut the contour 
            2.3.1 Create eligible_list represent points that are not outlined 
            2.3.2 Iterate through the boundary_list and 
            eligible_list of the same group to determine whether the boundary has a line 
            2.3.3 When there is a line, 
            call the depth-first search to find the two paths without duplicate points at both ends of the line to the 
            boundary to form a dividing line (one of the reverse is then connected) 
            2.3.4 Split() split() into two boundaries 
            according to the dividing line (break the boundary into two parts at the middle point of the found split path) 
            2.3.5 Repeat 2.3 until all contours are inside the smallest closed area (no dots) 

        2.4 Simple wire cutting profiles that are not recognized 
            2.4.1 Sorting out unrecognized simple lines can be done with shapely.overlaps() 
            or faster overlaps_from_node(). 
            2.4.2 Same as 2.3.4 

        2.5 Flatten the boundary_list to make sure all the shapes are 
        clockwise, and then get the segment group according to the vec_list query 
    """

    """1nd level space boundaries topology"""
    model = prepare_divided_zones(model, options.divided_zones, copy_air_boundaries)

    # CCR method

    # # BTG method
    model = generate_space_boundaries(model, generation_method)
    t4 = time.time()

    model = assemble_model(
        model,
        divided_zones=options.divided_zones,
        solve_overlap=options.solve_overlap,
        pack_model=pack_model,
    )
    """
    Packaging Moosasspace:
        1.1 Package Moosasedge to identify windows based on force_2d() and shapely.contains
        1.2 According to the level of the moosasedge group, 
        shapely.contains() gets the included slabs and feeds them to the model. MoosasFloor
        1.3 Successfully match the moosasedge of the floor, 
        above its level, shapely.contains() gets the first ceiling encountered and feeds it to the model. MoosasFloor
        1.4 Two models. Moosasfloor is combined with a model.Moosasedge to form a model.MoosasSpace
    """
    t5 = time.time()

    model = finalize_model(
        model,
        break_wall_vertical=options.break_wall_vertical,
        attach_shading=options.attach_shading,
        standardize=options.standardize,
        build_space_topology=build_space_topology,
        build_face_topology=build_face_topology,
        standardize_model=standardize_model,
        validate=validate_model,
    )
    t6 = time.time()
    t7 = time.time()

    print("-" * 20)
    print('Program finish. Summary:')
    # originalWall

    model.setCategory(False)
    model.summary()
    print('-' * 20)
    print(f"I/O                {'%.3fs' % (t1 - t0)}\t{'%.1f' % ((t1 - t0) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t1 - t0) / (t7 - t0) * 50))
    print(f"Data Structuring   {'%.3fs' % (t2 - t1)}\t{'%.1f' % ((t2 - t1) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t2 - t1) / (t7 - t0) * 50))
    print(f"Data Cleansing     {'%.3fs' % (t3 - t2)}\t{'%.1f' % ((t3 - t2) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t3 - t2) / (t7 - t0) * 50))
    print(f"1LSB Calculation   {'%.3fs' % (t4 - t3)}\t{'%.1f' % ((t4 - t3) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t4 - t3) / (t7 - t0) * 50))
    print(f"Space Construction {'%.3fs' % (t5 - t4)}\t{'%.1f' % ((t5 - t4) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t5 - t4) / (t7 - t0) * 50))
    print(f"2LSB Calculation   {'%.3fs' % (t6 - t5)}\t{'%.1f' % ((t6 - t5) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t6 - t5) / (t7 - t0) * 50))
    print(f"Content attachment {'%.3fs' % (t7 - t6)}\t{'%.1f' % ((t7 - t6) / (t7 - t0) * 100)}%\t",
          '\u25A0' * int((t7 - t6) / (t7 - t0) * 50))
    print(f"Total Duration     {'%.3fs' % (t7 - t0)}\t100%")

    return model






