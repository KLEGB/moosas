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

from .geometry import MoosasConvexify
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
        model = _glazingToFace(model)
    model = spaceTopology(model, True)
    return faceTopology(model)


def load_model(file_path: str, save_type: str | None = None, **kwargs) -> MoosasModel:
    """Load a model through an I/O adapter, then configure and complete it."""
    from .io import load_model as load_model_file

    model = load_model_file(file_path, save_type, **kwargs)
    configure_model_resources(model)
    return complete_topology(model)


def _convexify_cleaned_model(model: MoosasModel) -> MoosasModel:
    """Run the BuildingConvex-aligned convex split on a cleaned Moosas model."""
    geometry_by_id = {geometry.faceId: geometry for geometry in model.geometryList}
    source_geometry = []
    for element in model.getAllFaces():
        for face_id in mixItemListToList(element.faceId):
            geometry = geometry_by_id.get(face_id)
            if geometry is not None and geometry not in source_geometry:
                source_geometry.append(geometry)

    cat = [geometry.category for geometry in source_geometry]
    idd = [geometry.faceId for geometry in source_geometry]
    normal = [Vector(geometry.normal).array for geometry in source_geometry]
    faces = [shapely.get_coordinates(shapely.get_rings(geometry.face)[0], include_z=True)[:-1]
             for geometry in source_geometry]
    holes = [
        [shapely.get_coordinates(ring, include_z=True)[:-1]
         for ring in shapely.get_rings(geometry.face)[1:]]
        for geometry in source_geometry
    ]

    convex_cat, convex_idd, convex_normal, convex_faces, _ = MoosasConvexify.convexify_faces(
        cat,
        idd,
        normal,
        faces,
        holes,
    )

    convex_model = MoosasModel()
    convex_model.geometryList = [
        MoosasGeometry(
            shapely.polygons(face),
            str(face_id),
            Vector(face_normal),
            int(category),
            [],
            errors='raise',
        )
        for category, face_id, face_normal, face in zip(
            convex_cat,
            convex_idd,
            convex_normal,
            convex_faces,
        )
    ]
    convex_model.geoId = [geometry.faceId for geometry in convex_model.geometryList]
    convex_model.newIndex = len(convex_model.geometryList)
    return convex_model


def transform(input_path: str, input_type: str = None,
              output_path: str = None, output_type: str = None,
              method=CCRSpaceGeneration,
              solve_duplicated=True, solve_redundant=True, solve_overlap=True, triangulate_faces=True,
              break_wall_vertical=True, break_wall_horizontal=True,
              attach_shading=False,
              divided_zones=False, standardize=False,
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

    solve_duplicated : bool, optional
        Resolve walls with identical 2D projections (default: True).

    solve_redundant : bool, optional
        Merge coplanar faces/walls (default: True).

    solve_overlap : bool, optional
        Detect wall overlaps/containments (default: True).

    triangulate_faces : bool, optional
        Triangulate horizontal faces with holes (default: True).

    break_wall_vertical : bool, optional
        Vertically segment walls by building levels (default: True).

    break_wall_horizontal : bool, optional
        Horizontally segment walls at intersections (default: True).

    attach_shading : bool, optional
        Attach unused faces as shading/thermal mass (default: False).

    divided_zones : bool, optional
        Enable the convexified Moosas geometry flow before final space
        generation (default: False).

    standardize : bool, optional
        Simplify output geometry representations (default: False).

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
    >>> from MoosasPy.transformation.geometry.spaceGen import CCRSpaceGeneration
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
    model = structured(model, solve_duplicated, solve_redundant, solve_overlap, triangulate_faces, break_wall_vertical,
                       break_wall_horizontal, attach_shading, divided_zones, standardize, generationMethod=method,
                       t0=t0)

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


def structured(model: MoosasModel,
               solve_duplicated=True, solve_redundant=False, solve_overlap=False, triangulate_faces=True,
               break_wall_vertical=True, break_wall_horizontal=False, attach_shading=True, divided_zones=False,
               standardize=False, generationMethod=CCRSpaceGeneration, t0=0) -> MoosasModel:
    """
    Convert a draft model with unstructured geometric data to structured spatial model with optional processing.

    Parameters
    ----------
    model : MoosasModel
        a model only include geometry information (model.geometryList)


    generationMethod : callable, optional
        Space generation algorithm (default: CCRSpaceGeneration). Options:
        - VFGSpaceGeneration (L. Jones 2013)
        - BTGSpaceGeneration (H. Chen 2018)
        - CCRSpaceGeneration (J. Xiao 2023)

    solve_duplicated : bool, optional
        Resolve walls with identical 2D projections (default: True).

    solve_redundant : bool, optional
        Merge coplanar faces/walls (default: True).

    solve_overlap : bool, optional
        Detect wall overlaps/containments (default: True).

    triangulate_faces : bool, optional
        Triangulate horizontal faces with holes (default: True).

    break_wall_vertical : bool, optional
        Vertically segment walls by building levels (default: True).

    break_wall_horizontal : bool, optional
        Horizontally segment walls at intersections (default: True).

    attach_shading : bool, optional
        Attach unused faces as shading/thermal mass (default: False).

    divided_zones : bool, optional
        Enable the convexified Moosas geometry flow before final space
        generation (default: False).

    standardize : bool, optional
        Simplify output geometry representations (default: False).

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

        model = _classification(model, triangulate_faces, break_wall_vertical)

        model.faceList = np.array(model.faceList)
        model.wallList = np.array(model.wallList)
        model.glazingList = np.array(model.glazingList)

        """solve redundant coincident edge for faces that have the same factor"""
        if solve_redundant:
            model = cleanseCoplannerLine(model)

        """***We must solve invalid walls.***"""
        model = cleanseInvalidWall(model)
        model = cleanseInvalidFace(model)
        """match glazing"""
        model = _glazingToFace(model)
        t2 = time.time()

        '''
        Deduplication processing: Since the horizontal side has no effect on the recognition result, 
        only the result based on force2d() on the vertical side is deduplicated

        1. Filter elevations according to the total area of the elevation floor 
        **The total area is too low, usually sunshades or staircase landings that are not related to the analysis

        2. Use match() to determine the exact overlapping projection lines, and remove one of them directly

        3. Use contains(A,B) to determine the inclusion relationship between large surface A and small surface B:
            3.1 Use match(A,B) to determine whether there is a small surface C 
            on the other side after interrupting the large surface A
            3.2 If there is no small surface, use the broken force_2d () line combined with the elevation to complete 
            a simple wall surface and replace the original large surface (do not modify the reading data)

        4 Call the dissolve method on three invalid polygons
            4.1 The bottom elevation and the top elevation are the same/(under fuzzy recognition) 
            the length is zero/the bottom or top surface has only one point
            4.2 Invoke the rewrite overlaps algorithm to find adjacent faces
            4.3 Call dissolve to delete the polygon regardless of whether it is successful or not
        '''
        originalWall = [len(searchBy('level', bld_level, model.wallList)) for bld_level in model.levelList]

        """solve redundant coincident edge again after include curtains"""
        if solve_redundant:
            model = cleanseCoplannerLine(model)

        """solve duplicated walls that the 2d projections are the same."""
        if solve_duplicated:
            model = cleanseDuplicatedWall(model)

        """***We must solve invalid walls.***"""
        model = cleanseInvalidWall(model)
        model = cleanseInvalidFace(model)

        """solve contained walls that the 2d projections are overlapped by others."""
        if solve_overlap:
            model = cleanseOverlapWall(model)
            model = cleanseOverlapFace(model)

        """solve the intersection of walls on 2d space"""
        if break_wall_horizontal:
            model = solveIntersectionVertical(model)
            model = cleanseInvalidWall(model)
        t3 = time.time()

        if divided_zones and not did_convexify:
            model = _convexify_cleaned_model(model)
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
    if divided_zones:
        """flatten and copy air boundary in all levels to minimize the zones"""
        model = _copy_air_boundaries(model)

    # CCR method

    # # BTG method
    model = generationMethod(model)
    t4 = time.time()

    """
    Packaging Moosasspace:
        1.1 Package Moosasedge to identify windows based on force_2d() and shapely.contains
        1.2 According to the level of the moosasedge group, 
        shapely.contains() gets the included slabs and feeds them to the model. MoosasFloor
        1.3 Successfully match the moosasedge of the floor, 
        above its level, shapely.contains() gets the first ceiling encountered and feeds it to the model. MoosasFloor
        1.4 Two models. Moosasfloor is combined with a model.Moosasedge to form a model.MoosasSpace
    """
    model = packing_edges(model, divided_zones)
    if solve_overlap:
        model = solveIntersectionHorizontal(model)
    model = _packing_model(model, solve_overlap)
    model = _pack_attic_spaces(model)
    t5 = time.time()

    """2nd level space boundaries topology"""
    model = spaceTopology(model, break_wall_vertical)
    model = faceTopology(model)
    t6 = time.time()
    if attach_shading:
        """attach isolated walls and faces"""
        model = _attach_shading(model)
    if standardize:
        model = _standardize(model)
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


def _classification(model: MoosasModel, triangulate_faces=True, break_wall_vertical=True) -> MoosasModel | None:
    """
        Structuring data by elevation:
        In principle, all changes are made only for MoosasGeometry, ensuring a unique faceId
        1. Point multiplication vectors distinguish horizontal/vertical planes and are packaged into
        a MoosasFace/MoosasWall** Levels are automatically assigned or generated during __init__ packing process
        2. Find the transparent object with geo_category=1 and pack it into MoosasGlazing/MoosasSkylight
            2.1 Conversion of glazing to curtain wall for bottom elevation close to floor slab (glazingId==faceId)
        3. Interrupt the wall at full height, and update the bottom projection set self.
        __botProjection at different levels
        4. Call force_2d() to match the window
            4.1 Call the rewrite dwithin method to fuzzily match the window wall
            4.2 Windows that do not match the wall are considered curtain walls

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        triangulate_faces : bool, optional
            Triangulate horizontal faces with holes (default: True).

        break_wall_vertical : bool, optional
            Vertically segment walls by building levels (default: True).

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """
    # predefine faces with the note of category.
    print(f'\rLOADING: Predefining existing tag on faces...', end='')
    ClearId = []
    for i in range(len(model.geoId)):
        geo = model.geometryList[i]
        if geo.category == -1:
            geo.setCategory()
            model.shadingList.append(MoosasElement(model, geo))
            ClearId.append(geo.faceId)

        elif geo.category == 4:
            ClearId.append(geo.faceId)
            geo.setCategory()
            face = MoosasFace(model, geo)
            model.faceList.append(face)
            if not face.level in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()

        elif geo.category == 6:
            ClearId.append(geo.faceId)
            geo.setCategory()
            face = MoosasSkylight(model, geo)
            model.skylightList.append(face)
            if not face.level in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()

    for i in range(len(model.geoId)):
        geo = model.geometryList[i]
        if geo.category == 3:
            ClearId.append(geo.faceId)
            geo.setCategory()
            model.wallList.append(MoosasWall(model, geo))
        elif geo.category == 5:
            ClearId.append(geo.faceId)
            geo.setCategory()
            model.glazingList.append(MoosasGlazing(model, geo))

    print()
    # triangulate the faces with holes
    if triangulate_faces:
        delfaces = []
        for i, geo in enumerate(model.geometryList):
            if geo.faceId in ClearId: continue
            print(f'\rLOADING: triangulate horizontal faces {i + 1}/{len(model.geoId)}', end='')
            if np.abs(Vector.dot(geo.normal, shapely.points([0, 0, 1]))) >= geom.HORIZONTAL_ANGLE_THRESHOLD:
                if len(geo.holes) > 0:
                    proj = Projection.fromPolygon(geo.face)
                    geoProj = proj.toUV(geo.face)
                    holesProj = [proj.toUV(h) for h in geo.holes]
                    newHorGeoProj, _ = triangulate2dFace(geoProj, holesProj)
                    newHorGeos = [proj.toWorld(newHorGeo) for newHorGeo in newHorGeoProj]
                    for newHorGeo in newHorGeos:
                        try:
                            model.includeGeo(newHorGeo, cat=geo.category)
                        except GeometryError as ge:
                            print(f"******Warning: {ge}")
                    delfaces.append(i)

        model.geoId = list(np.delete(model.geoId, delfaces))
        model.geometryList = list(np.delete(model.geometryList, delfaces))
        print(f'\t\tprocessing faces: {len(delfaces)}')

    # print('wall:', len(model.wallList))
    # print('glazing:', len(model.glazingList))
    # print('skylight:', len(model.skylightList))
    # print('face:', len(model.faceList))
    for i, geo in enumerate(model.geometryList):
        if geo.faceId in ClearId: continue
        print(f'\rLOADING: Filtering horizontal faces {i + 1}/{len(model.geoId)}', end='')
        if np.abs(Vector.dot(geo.normal, shapely.points([0, 0, 1]))) >= 0.99:
            if geo.category != 0:
                # print(' skylight',end='')
                face = MoosasSkylight(model, geo)
                model.skylightList.append(face)
            else:
                # print(' opaque', end='')
                face = MoosasFace(model, geo)
                model.faceList.append(face)
            # print(face.level)
            if not face.level in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()
    print()
    # Ver1.3 move the incline wall here
    for i, geo in enumerate(model.geometryList):
        if geo.faceId in ClearId: continue
        print(f'\rLOADING: Filtering inclined faces {i + 1}/{len(model.geoId)}', end='')
        if 0.99 > np.abs(Vector.dot(geo.normal, shapely.points([0, 0, 1]))) >= geom.HORIZONTAL_ANGLE_THRESHOLD:
            # horizontal faces!
            if geo.category != 0:
                # print(' skylight',end='')
                face = MoosasSkylight(model, geo)
                model.skylightList.append(face)
            else:
                # print(' opaque', end='')
                face = MoosasFace(model, geo)
                model.faceList.append(face)
            # print(face.level)
            if not face.level in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()

    if len(model.levelList) == 0:
        return None

    model = cleanseDuplicatedLevel(model)
    print(f'\t\ttotal horizontal faces: {len(model.faceList)} skylights: {len(model.skylightList)}')

    if break_wall_vertical:
        # Ver2.0 break the walls into each level
        wallList = [model.geoId[i] for i in range(len(model.geoId)) if
                    np.abs(Vector.dot(model.geometryList[i].normal,
                                      shapely.points([0, 0, 1]))) < geom.HORIZONTAL_ANGLE_THRESHOLD]
        for i, idd in enumerate(wallList):
            if idd in ClearId: continue
            model = _break_vertical_faces(model, idd)
            print(f'\rLOADING: Break walls {i + 1}/{len(wallList)}', end='')
        wallList_new = [model.geoId[i] for i in range(len(model.geoId)) if
                        np.abs(Vector.dot(model.geometryList[i].normal,
                                          shapely.points([0, 0, 1]))) < geom.HORIZONTAL_ANGLE_THRESHOLD]
        # print(f'break walls: {len(wallList) - wallcount}')
        print(f'\t\t\tadd walls:{len(wallList_new) - len(wallList)}')

    for i, geo in enumerate(model.geometryList):
        if geo.faceId in ClearId: continue
        print(f'\rLOADING: Filtering vertical faces {i + 1}/{len(model.geoId)}', end='')
        if np.abs(Vector.dot(geo.normal, shapely.points([0, 0, 1]))) < geom.HORIZONTAL_ANGLE_THRESHOLD:
            # this is the vertical face锛?
            if geo.category != 0:
                # print(' glazing',end='')
                model.glazingList.append(
                    MoosasGlazing(model, geo))
            else:
                # print(' wall', end='')
                model.wallList.append(MoosasWall(model, geo))

    print(f"\t\ttotal vertical faces: {len(model.wallList)} glazings: {len(model.glazingList)}")

    # from .IO import writeGeo
    # geoList = []
    # for ele in list(model.wallList)+list(model.glazingList)+list(model.faceList)+list(model.skylightList):
    #     geoList += mixItemListToList(ele.geometry)
    # writeGeo(r'E:\PycharmProjects\moosas\test\breakwall.geo', geoList=geoList)
    # raise Exception

    # # force2d for each wall and glazing, identify the isolated elements
    # print("LOADING: Identifying shadings",end='')
    # def validIntersect(geo1, geo2):
    #     intersect = shapely.intersection(geo1, geo2)
    #     if shapely.get_dimensions(intersect) == 0:
    #         twins = shapely.points(shapely.get_coordinates(geo1))
    #         if shapely.distance(twins[0],intersect) < geom.POINT_PRECISION:
    #             return 1
    #         if shapely.distance(twins[1],intersect) < geom.POINT_PRECISION:
    #             return 1
    #         return 2
    #     return 0
    #
    # # examining method predefining shading
    # prs,total = 0,len(model.wallList)+len(model.glazingList)
    # for bld_level in model.levelList:
    #     wallShading,glsShading = [],[]
    #     wallsIdx,glazingsIdx = searchBy('level', bld_level,model.wallList),searchBy('level', bld_level,model.glazingList)
    #     walls,glazings = np.array(model.wallList)[wallsIdx],np.array(model.glazingList)[glazingsIdx]
    #
    #     w2d,g2d = [ele.force_2d() for ele in walls], [ele.force_2d() for ele in glazings]
    #
    #     # treat wall
    #     for wi,wall in enumerate(w2d):
    #         prs+=1
    #         print(f"\rLOADING: Identifying shadings: {prs}/{total}", end='')
    #         isoWall=0
    #         for wallOther in w2d[wi+1:]:
    #             if isoWall >= 2:
    #                 break
    #             else:
    #                 isoWall+=validIntersect(wall,wallOther)
    #
    #         if isoWall < 2:
    #             for glsOther in g2d:
    #                 if isoWall >= 2:
    #                     break
    #                 else:
    #                     isoWall += validIntersect(wall, glsOther)
    #         if isoWall<2:
    #             wallShading.append(wallsIdx[wi])
    #
    #     # treat gls
    #     for gi,gls in enumerate(g2d):
    #         prs += 1
    #         print(f"\rLOADING: Identifying shadings: {prs}/{total}", end='')
    #         isoWall=0
    #         for glsOther in g2d[gi+1:]:
    #             if isoWall >= 2:
    #                 break
    #             else:
    #                 isoWall += validIntersect(gls, glsOther)
    #         if isoWall < 2:
    #             for wallOther in w2d:
    #                 if isoWall >= 2:
    #                     break
    #                 else:
    #                     isoWall += validIntersect(gls, wallOther)
    #         if isoWall<2:
    #             glsShading.append(glazingsIdx[gi])
    #
    #     shadingElements = np.append(np.array(model.wallList)[wallShading],np.array(model.glazingList)[glsShading])
    #     model.wallList = list(np.delete(model.wallList, wallShading))
    #     model.glazingList = list(np.delete(model.glazingList, glsShading))
    #     model.shadingList = list(np.append(model.shadingList, shadingElements))
    #     from .IO import writeGeo
    #     geoList = []
    #     for geo in model.shadingList:
    #         geoList += mixItemListToList(geo.geometry)
    #     writeGeo(r'E:\PycharmProjects\moosas\test\breakwall.geo', geoList=model.shadingList)
    #     raise Exception
    # print(f"\t\ttotal shadings: {len(model.shadingList)}")

    return model


def _matchFaceGlazing(face: MoosasFace | MoosasWall, glazing: MoosasSkylight | MoosasGlazing) -> bool:
    """
    attach the glazing element to the face or wall element.
    the faces topology would be directly added and do not need further treatment.

    Parameters
    ----------
    face : MoosasFace | MoosasWall
        any input MoosasFace | MoosasWall as potential parent face

    glazing : MoosasSkylight | MoosasGlazing
        any input MoosasSkylight | MoosasGlazing as potential child face

    Returns
    -------
    bool
        True if successfully matched.
    """

    a = face.force_2d(region=True)
    b = glazing.force_2d(region=True)
    if shapely.get_dimensions(a) == shapely.get_dimensions(b) and shapely.get_dimensions(a) == 1:
        for p in shapely.points(shapely.get_coordinates(b)):
            if not shapely.distance(a, p) <= 2 * geom.POINT_PRECISION:
                return False
        face.add_glazing(glazing)
        return True
    else:
        if shapely.contains(face.force_2d(region=True), glazing.force_2d(region=True)):
            face.add_glazing(glazing)
            return True
        else:
            return False


def _glazingToFace(model: MoosasModel) -> MoosasModel:
    """
        check each glazings and skylights to find their parent faces.
        if not found, the glazings/ skylights will be changed to a curtain wall or glass roof, whose faceId == glazingId
        but still need to have a copy in model.glazingList/model.skylightList

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """
    """grouping with normal"""
    glsCount = 0
    validGlsCount = 0
    # eleList = np.append(model.glazingList,model.wallList)
    # eleType = np.array([1]*len(model.glazingList)+[0]*len(model.wallList))
    # normalList = np.array([faceNormal(mixItemListToList(ele.face)[0]) for ele in eleList])
    # from .geometry.cleanse import _groupByNormal
    # eleIdxGroup = _groupByNormal(list(range(len(eleList))) , normalList)
    # for eleIds in eleIdxGroup:
    #     elements,_types = eleList[eleIds],eleType[eleIds]
    #     glazings,walls = elements[_types==1],elements[_types==0]

    for bld_level in model.levelList:
        windowList = np.array(model.glazingList)[searchBy('level', bld_level, model.glazingList)]
        wallList = np.array(model.wallList)[searchBy('level', bld_level, model.wallList)]
        w2d = [w.force_2d() for w in wallList]
        for window in windowList:
            glsCount += 1
            print(f"\rLOADING: Matching glazing {glsCount}/{len(model.glazingList)}", end='')
            located = False
            dist = np.argsort([shapely.distance(window.force_2d(), w) for w in w2d])
            # print(shapely.distance(window.force_2d(), wallList[dist][0].force_2d()))
            for wall in wallList[dist][:min(5, len(wallList))]:
                if _matchFaceGlazing(wall, window):
                    located = True
                    validGlsCount += 1
                    break

            if not located:
                # print(window.force_2d(region=True),bld_level)
                curtain = MoosasWall(model, faceId=window.faceId)
                curtain.add_glazing(window)
                model.wallList = list(np.append(model.wallList, [curtain]))

    print("\tmatched glazings: ", validGlsCount)
    """match skylight"""
    print(f"\rLOADING: Matching skylight", end='')
    validSkyCount = 0
    for glsCount, skylight in enumerate(model.skylightList):
        print(f"\rLOADING: Matching skylight {glsCount}/{len(model.skylightList)}", end='')
        floor = np.array(model.faceList)[searchBy('level', skylight.level, model.faceList)]
        located = False
        for fl in floor:
            if _matchFaceGlazing(fl, skylight):
                located = True
                validSkyCount += 1
                break

        if not located:
            skyfloor = MoosasFace(model=model, faceId=skylight.faceId)
            skyfloor.add_glazing(skylight)
            model.faceList = list(np.append(model.faceList, [skyfloor]))
    print("\t\t\tmatched skylight: ", validSkyCount)
    return model


def _break_vertical_faces(model: MoosasModel, faceId) -> MoosasModel:
    """
        break a vertical face by the building level it crosses

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        faceId : str
            the faceId of the input geometry to break

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """

    geo: MoosasGeometry = model.geometryList[model.geoId.index(faceId)]
    cat = geo.category
    geo: shapely.Geometry = geo.face
    z = [coor[2] for coor in shapely.get_coordinates(geo, include_z=True)]

    # check where the wall's bottom lays
    top = np.max(z)
    bot = np.min(z)
    bot_level, top_level = -1, len(model.levelList) - 1
    for bldLevelIndex in range(len(model.levelList)):
        if bot >= model.levelList[bldLevelIndex]:
            bot_level = bldLevelIndex
        if top >= model.levelList[bldLevelIndex]:
            top_level = bldLevelIndex

    if bot_level == len(model.levelList) - 1:
        # the wall is located above the roof
        return model
    elif top <= model.levelList[bot_level + 1]:
        # a typical wall do not cross a floor
        return model
    else:
        # print(shapely.get_coordinates(geo, include_z=True))
        # # try making the wall valid
        # try:
        #     geo: shapely.Geometry = makeValid(geo)[0]
        #     if geo is None:
        #         return model
        # except GeometryError:
        #     return model

        # Pseudo-dynamic array working_faces:
        # The cut newFace is appended to the end of the working_faces and then checked;
        # Faces that cannot be cut are placed in finished_faces
        finish_faces = []
        working_faces = [geo]
        while len(working_faces) > 0:
            face = working_faces.pop()
            miniFace = True  # hint decides that whether the face has been cut
            z = [coor[2] for coor in shapely.get_coordinates(face, include_z=True)]

            for bld_level in model.levelList[bot_level + 1: top_level + 1]:
                if np.min(z) + geom.POINT_PRECISION < bld_level < np.max(
                        z) - geom.POINT_PRECISION:  # valid cutting level
                    # spliter = section(face, bld_level, segment=False)
                    # if spliter is not None:
                    splitfaces = splitOnZ(face, bld_level)
                    if splitfaces is not None:
                        if len(splitfaces[0]) * len(splitfaces[1]) > 0:
                            # z = [coor[2] for coor in shapely.get_coordinates(splitfaces[0][0], include_z=True)]
                            # z = [coor[2] for coor in shapely.get_coordinates(splitfaces[1][0], include_z=True)]
                            # print(len(splitfaces[0]),len(splitfaces[1]),bld_level, cat)
                            working_faces = list(np.append(working_faces, splitfaces[0]))
                            working_faces = list(np.append(working_faces, splitfaces[1]))
                            miniFace = False
                            break
            if miniFace:
                finish_faces.append(face)
        working_faces = finish_faces
        # print(faceId,bot,top,model.levelList[bot_level],model.levelList[bot_level + 1],len(working_faces))
        # if faceId=='0_19':raise Exception
        if len(working_faces) > 1:
            model.removeGeo(faceId)
            for face in working_faces:
                try:
                    model.includeGeo(face, cat=cat)
                except GeometryError:
                    pass
        return model


def _order_connected_walls(walls: list) -> list | None:
    """Order walls into one closed 2D ring without changing their geometry."""
    if len(walls) < 3:
        return None
    remaining = list(walls)
    ordered = [remaining.pop(0)]
    current_end = shapely.get_coordinates(ordered[0].force_2d())[-1]
    tolerance = 2 * geom.POINT_PRECISION
    while remaining:
        for index, candidate in enumerate(remaining):
            coordinates = shapely.get_coordinates(candidate.force_2d())
            if np.linalg.norm(coordinates[0] - current_end) <= tolerance:
                current_end = coordinates[-1]
                ordered.append(remaining.pop(index))
                break
            if np.linalg.norm(coordinates[-1] - current_end) <= tolerance:
                current_end = coordinates[0]
                ordered.append(remaining.pop(index))
                break
        else:
            return None
    first_coordinates = shapely.get_coordinates(ordered[0].force_2d())
    if np.linalg.norm(current_end - first_coordinates[0]) > tolerance and np.linalg.norm(current_end - first_coordinates[-1]) > tolerance:
        return None
    return ordered


def _pack_attic_spaces(model: MoosasModel) -> MoosasModel:
    """Create normal spaces closed by existing inclined roof faces and eave walls."""
    inclined_faces = [
        face for face in model.faceList
        if geom.HORIZONTAL_ANGLE_THRESHOLD <= abs(np.asarray(face.normal, dtype=float)[2]) < 0.99
    ]
    remaining = list(inclined_faces)
    roof_components = []
    while remaining:
        component = [remaining.pop(0)]
        changed = True
        while changed:
            changed = False
            component_edges = {edge for face in component for edge in face.getEdgeStr()}
            for face in list(remaining):
                if component_edges.intersection(face.getEdgeStr()):
                    component.append(face)
                    remaining.remove(face)
                    changed = True
        roof_components.append(component)

    added = []
    used_walls = set()
    for roof_faces in roof_components:
        roof_edges = {edge for face in roof_faces for edge in face.getEdgeStr()}
        eave_walls = [wall for wall in model.wallList if wall not in used_walls and roof_edges.intersection(wall.getEdgeStr())]
        ordered_walls = _order_connected_walls(eave_walls)
        if ordered_walls is None:
            continue
        try:
            attic_edge = MoosasEdge(ordered_walls)
        except GeometryError:
            continue

        base_faces = []
        for face in model.faceList:
            if abs(np.asarray(face.normal, dtype=float)[2]) < 0.99 or abs(face.level - attic_edge.level) > geom.LEVEL_MAX_OFFSET:
                continue
            try:
                if overlapArea(face.force_2d(), attic_edge.force_2d()) > geom.AREA_PRECISION:
                    base_faces.append(face)
            except GeometryError:
                continue
        if not base_faces:
            continue
        unique_base_faces = []
        covered = None
        for face in sorted(base_faces, key=lambda item: item.Uid):
            footprint = face.force_2d()
            uncovered = footprint if covered is None else shapely.difference(footprint, covered)
            if shapely.area(uncovered) > geom.AREA_PRECISION:
                unique_base_faces.append(face)
                covered = footprint if covered is None else shapely.union_all([covered, footprint])
        try:
            attic_floor = MoosasFloor(unique_base_faces)
            attic_ceiling = MoosasFloor(roof_faces)
            attic = MoosasSpace(attic_floor, attic_edge, attic_ceiling, space_type="attic")
        except GeometryError:
            continue
        if attic.is_void():
            continue
        model.floorList.append(attic_floor)
        model.ceilingList.append(attic_ceiling)
        model.spaceList.append(attic)
        used_walls.update(ordered_walls)
        added.extend(roof_faces)

    if added:
        added_set = set(added)
        model.face_remain = [face for face in model.face_remain if face not in added_set]
        model.shadingList = np.array([face for face in model.shadingList if face not in added_set])
        print(f'PACKING: Build attic spaces: {len(added_set)} roof faces attached')
    return model

def _packing_model(model: MoosasModel, solve_overlap) -> MoosasModel:
    """
        Packaging MoosasSpace:
            1.1 searching floor and ceiling shadow the MoosasEdge, and use the edge to split those faces.
                1.1.1 this boolean calculation only work for the flat planes.
                if the plane is incline it is seldom used as a floor.
                we ignore them since the boolean only works for 2LSB calculation.
            1.2 determine whether the edge is solid space or void space based on the identified result

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """

    """search for floors"""

    print('\rPACKING: Match floors', end='')
    faceSet = set([member for member in model.faceList])
    topology = [{'floor': None, 'ceiling': None} for _ in model.edgeList]
    prs = 0
    for bld_level in model.levelList:
        edge = searchBy('level', bld_level, model.edgeList)
        face = searchBy('level', bld_level, model.faceList)
        for edx, i in enumerate(edge):
            prs += 1
            try:
                totalShadowArea = 0
                matchFaces = []
                for j in face:
                    intersectArea = overlapArea(model.edgeList[i].force_2d(), model.faceList[j].force_2d())
                    if intersectArea > geom.AREA_PRECISION:
                        totalShadowArea += intersectArea
                        matchFaces.append(model.faceList[j])

                floorFaces = MoosasFloor(matchFaces)
                if solve_overlap and totalShadowArea < model.edgeList[i].area - geom.AREA_PRECISION:
                    floorFaces = _capFloorSimple(model.edgeList[i].force_2d(), bld_level, model, floorFaces)
                topology[i]['floor'] = floorFaces
                model.floorList.append(floorFaces)

                if totalShadowArea != 0 and floorFaces.area < geom.ROOM_MIN_AREA:
                    print(f'\n******Warning: GeometryError floor faces too small in {floorFaces.Uid}')
                faceSet = faceSet.difference(set(matchFaces))
                print(f'\rPACKING: Match floors:{prs}/{len(model.edgeList)}\t\t\ttotal floors: {len(model.floorList)}',
                      end='')
            except GeometryError:
                print(f'\n******Warning: GeometryError: floor faces, pass')
                pass

    print()
    """search for ceilings"""
    print('\rPACKING: Match ceilings', end='')
    prs = 0
    for bld_level, top_level in zip(model.levelList[:-1], model.levelList[1:]):
        edge = searchBy('level', bld_level, model.edgeList)
        face = searchBy('level', top_level, model.faceList)
        for i in edge:
            prs += 1
            try:
                totalShadowArea = 0
                matchFaces = []
                for j in face:
                    edge2d = model.edgeList[i].force_2d(top=True) if shapely.is_valid(
                        model.edgeList[i].force_2d(top=True)) else model.edgeList[i].force_2d()
                    intersectArea = overlapArea(edge2d, model.faceList[j].force_2d())
                    if intersectArea > geom.AREA_PRECISION:
                        totalShadowArea += intersectArea
                        # if intersectArea < model.faceList[j].area - geom.AREA_PRECISION and solve_overlap:
                        #     # this holes need continue dividing
                        #     theFloor = model.faceList[j].parentFloors
                        #     for fl in theFloor:
                        #         try:
                        #             fl.face.remove(model.faceList[j])
                        #         except:
                        #             pass
                        #     newF = splitFaces(model.faceList[j], model.edgeList[i])
                        #     if newF is not None:
                        #         newFin, newFout = newF
                        #         for fl in theFloor:
                        #             for fc in [newFin] + newFout:
                        #                 fl.face.append(fc)
                        #                 fc.parentFloors.append(fl)
                        #         matchFaces.append(newFin)
                        #     else:
                        #         matchFaces.append(model.faceList[j])
                        # else:
                        #     matchFaces.append(model.faceList[j])

                        matchFaces.append(model.faceList[j])

                if len(matchFaces) > 0:
                    floorFaces = MoosasFloor(matchFaces)
                    topology[i]['ceiling'] = floorFaces
                    model.ceilingList.append(floorFaces)
                    if totalShadowArea != 0 and floorFaces.area < geom.ROOM_MIN_AREA:
                        print(f'******Warning: GeometryError, ceiling faces too small in {floorFaces.Uid}')

                faceSet = faceSet.difference(set(matchFaces))
                print(
                    f'\rPACKING: Match ceilings:{prs}/{len(model.edgeList)}\t\ttotal ceils {len(model.ceilingList)} ',
                    end='')
            except GeometryError:
                print(f'******Warning: GeometryError, ceiling faces, pass')
                pass
    model.face_remain = list(faceSet)
    model.shadingList = np.append(model.shadingList, list(faceSet))
    spaceToAdd = []
    for i, edge in enumerate(model.edgeList):
        # if topology[i]['floor'] is not None:
        #     if makeValid(topology[i]['floor'].force_2d(), error='') is None:
        #         topology[i]['floor'] = None
        #
        # if topology[i]['ceiling'] is not None:
        #     if makeValid(topology[i]['ceiling'].force_2d(), error='') is None:
        #         topology[i]['ceiling'] = None

        spaceToAdd += [MoosasSpace(
            topology[i]['floor'],
            model.edgeList[i],
            topology[i]['ceiling']
        )]
    print()
    """attach void to space"""
    spcCount = 0
    for bld_level in model.levelList:
        spacesList: list[MoosasSpace] = np.array(spaceToAdd)[searchBy('level', bld_level, spaceToAdd)]
        for i, space in enumerate(spacesList):
            spcCount += 1
            print(f"\rPACKING: attach void to space {spcCount}/{len(spaceToAdd)}", end='')
            for j, other in enumerate(spacesList[i:]):
                if space != other:
                    if shapely.contains_properly(space.force_2d(), other.force_2d()):
                        if other.is_void() and space not in other.void:
                            space.add_void(other)
                        else:
                            newVoid = MoosasSpace(None, other.edge, None)
                            model.voidList.append(newVoid)
                        # plot_object(spacesList,space,colors=['black','red'])

                    if shapely.contains_properly(other.force_2d(), space.force_2d()):
                        if space.is_void() and other not in space.void:
                            other.add_void(space)
                        else:
                            newVoid = MoosasSpace(None, space.edge, None)
                            model.voidList.append(newVoid)
                        # plot_object(spacesList,other,colors=['black','red'])
    print()
    """packing both solid space and void space"""
    for space in spaceToAdd:
        if not space.is_void():
            model.spaceList.append(space)
        else:
            # print(space.id, space.void)
            # plot_object(space.edge,space.floor,colors=['black','red'],filled=True)
            model.voidList.append(space)

        print('\rPACKING: Build a space:', space.id,
              'Bld_level=', space.level,
              'Bld_area=%.2f' % space.area,
              end='')
    print()
    return model


def _capFloor(boundary: shapely.Geometry, level, model: MoosasModel,
              baseFloor: MoosasFloor | None = None) -> MoosasFloor:
    """
        cap a boundary using MoosasFloor, based on the floor input.
        faces in the base floor will be split and move to the new floor.
        glazing will also be split and tested to apply to any faces.

        Parameters
        ----------
        boundary : shapely.Geometry
            the void boundary to cap (2d or 3d)

        level : float
            the z value of the boundary, it would not be automatically identified.

        model : MoosasModel
            any input MoosasModel

        baseFloor : MoosasFloor | None , optional
            if any floor faces were located (potentially) in the boundary, it could be reuse in this module

        Returns
        -------
        MoosasFloor
            The MooosasFloor object matched the boundary
    """
    floorFace: list[MoosasFace] = []
    remainFace: list[MoosasFace] = []
    apertureFace: list[MoosasSkylight] = [] if baseFloor is None else baseFloor.glazingElement
    baseFace: list[MoosasFace] = [] if baseFloor is None else baseFloor.face

    # find useful parts from the based face
    for f in baseFace:
        multiFaces = shapely.multipolygons(mixItemListToList(f.face))
        useful = shapely.intersection(boundary, multiFaces, grid_size=geom.POINT_PRECISION)
        if not shapely.is_empty(useful):
            useful = shapely.get_parts(useful)
            for _useful in useful:
                _useful = shapely.force_3d(_useful, z=level)
                if shapely.get_dimensions(_useful) != 2: continue
                idx = model.includeGeo(_useful, Vector([0, 0, 1]).geometry, cat=0)
                model.faceList.append(MoosasFace(model=model, faceId=idx))
                floorFace.append(model.faceList[-1])

            remainPart = shapely.difference(multiFaces, boundary, grid_size=geom.POINT_PRECISION)
            if not shapely.is_empty(remainPart):
                remainPart = shapely.get_parts(remainPart)
                for _remain in remainPart:
                    _remain = shapely.force_3d(_remain, z=level)
                    if shapely.get_dimensions(_remain) != 2: continue
                    idx = model.includeGeo(_remain, Vector([0, 0, 1]).geometry, cat=0)
                    model.faceList.append(MoosasFace(model, idx))
                    remainFace.append(model.faceList[-1])

    # minus the boundary by those useful faces
    for f in floorFace:
        multiFaces = shapely.multipolygons(mixItemListToList(f.face))
        boundary = shapely.difference(boundary, multiFaces)

    # construct aperture
    if not shapely.is_empty(boundary):
        boundary = shapely.get_parts(boundary)
        for bound in boundary:
            try:
                bound = shapely.force_3d(bound, z=level)
                idx = model.includeGeo(bound, Vector([0, 0, 1]).geometry, cat=2)  # aperture
                model.faceList.append(MoosasFace(model, idx))
                model.skylightList.append(MoosasSkylight(model, idx))
                model.faceList[-1].add_glazing(model.skylightList[-1])
                floorFace.append(model.faceList[-1])
            except GeometryError:
                continue

    # add glazing to faces
    for gls in apertureFace:
        matched = False
        for _face in floorFace:
            if _matchFaceGlazing(_face, gls):
                matched = True
                break
        if not matched:
            for _face in remainFace:
                if _matchFaceGlazing(_face, gls):
                    break

    # all require faced
    return MoosasFloor(floorFace)


def _capFloorSimple(boundary: shapely.Geometry, level, model: MoosasModel,
                    baseFaces: MoosasFloor | None = None) -> MoosasFloor:
    """
        cap a boundary using MoosasFloor, based on the floor input.
        faces in the base floor will be split and move to the new floor.
        glazing will also be split and tested to apply to any faces.

        Parameters
        ----------
        boundary : shapely.Geometry
            the void boundary to cap (2d or 3d)

        level : float
            the z value of the boundary, it would not be automatically identified.

        model : MoosasModel
            any input MoosasModel

        baseFloor : MoosasFloor | None , optional
            if any floor faces were located (potentially) in the boundary, it could be reuse in this module

        Returns
        -------
        MoosasFloor
            The MooosasFloor object matched the boundary
    """
    floorFace: list[MoosasFace] = [] if baseFaces is None else baseFaces.face
    model.faceList = list(model.faceList)
    model.skylightList = list(model.skylightList)
    # minus the boundary by those useful faces
    for f in floorFace:
        multiFaces = shapely.multipolygons(mixItemListToList(f.face))
        boundary = shapely.difference(boundary, multiFaces)

    # construct air boundary
    if not shapely.is_empty(boundary):
        boundary = shapely.get_parts(boundary)
        for bound in boundary:
            bound = shapely.force_3d(bound, z=level)
            idx = model.includeGeo(bound, Vector([0, 0, 1]).geometry, cat=2)  # aperture
            model.faceList.append(MoosasFace(model, idx))
            model.skylightList.append(MoosasSkylight(model, idx))
            model.faceList[-1].add_glazing(model.skylightList[-1])
            floorFace.append(model.faceList[-1])
    # all require faced
    return MoosasFloor(floorFace)


def _findVoidAbove(voidWithFloor: MoosasSpace) -> MoosasSpace | None:
    """
        find the void above for an void, which can be potentially merged together.

        Parameters
        ----------
        voidWithFloor : MoosasSpace
            the void as MoosasSpace (voidWithFloor.is_void()==True)
            which must contain a floor (voidWithFloor.floor is not None)

        Returns
        -------
        MoosasSpace | None
            The void object above, or None
    """
    model: MoosasModel = voidWithFloor.parent
    voidTopLevel = model.levelList.index(voidWithFloor.level)
    if voidTopLevel == len(model.levelList) - 1:
        return None
    else:
        voidTopLevel = model.levelList[voidTopLevel + 1]
        topVoidList = np.array(model.voidList)[searchBy('level', voidTopLevel, model.voidList)]
        for topVoid in topVoidList:
            if topVoid.floor is None:
                if shapely.contains(voidWithFloor.force_2d(top=True), topVoid.force_2d()):
                    return topVoid
                elif shapely.contains(topVoid.force_2d(), voidWithFloor.force_2d(top=True)):
                    return topVoid
    return None


def _findCoCeiling(spaceBottom: MoosasSpace, spaceTop: MoosasSpace) -> (MoosasFloor, MoosasFloor):
    """
        find the overlap part of the floor, clip and regenerate the floors.

        Parameters
        ----------
        spaceBottom : MoosasSpace
            bottom space

        spaceTop : MoosasSpace
            top space

        Returns
        -------
        MoosasFloor , MoosasFloor
            The bottom floor and the top floor.
    """
    model: MoosasModel = spaceBottom.parent
    z = spaceTop.edge.elevation
    co1 = spaceBottom.ceiling.face if spaceBottom.ceiling else []
    co2 = spaceTop.floor.face if spaceTop.floor else []
    allCoFaces = list(set(co1) | set(co2))
    intersection = shapely.intersection(spaceBottom.force_2d(True), spaceTop.force_2d(), grid_size=geom.POINT_PRECISION)
    print(spaceBottom.force_2d(True), spaceTop.force_2d(), intersection)
    ceilingFace = shapely.difference(spaceBottom.force_2d(True), intersection, grid_size=geom.POINT_PRECISION)
    floorFace = shapely.difference(spaceTop.force_2d(), intersection, grid_size=geom.POINT_PRECISION)
    ceilingFace = shapely.force_3d(ceilingFace, z=z)
    floorFace = shapely.force_3d(floorFace, z=z)

    if shapely.is_empty(intersection):
        raise Exception("space disjoint")
    else:
        intersection = _capFloor(spaceTop.force_2d(), spaceTop.level, model, MoosasFloor(allCoFaces))
        if not shapely.is_empty(floorFace):
            includedFaces = []
            for f in mixItemListToList(shapely.get_parts(floorFace)):
                try:
                    idx = model.includeGeo(f, Vector([0, 0, 1]).geometry)
                    includedFaces.append(MoosasFace(model, idx))
                except GeometryError:
                    continue
            floorFace = includedFaces
            floorFace = _capFloor(spaceTop.force_2d(), spaceTop.level, model,
                                  MoosasFloor(floorFace))
            floorFace = floorFace.face + intersection.face
        else:
            floorFace = intersection.face
        if not shapely.is_empty(ceilingFace):
            includedFaces = []
            for f in mixItemListToList(shapely.get_parts(ceilingFace)):
                try:
                    idx = model.includeGeo(f, Vector([0, 0, 1]).geometry)
                    includedFaces.append(MoosasFace(model, idx))
                except GeometryError:
                    continue

            ceilingFace = includedFaces
            ceilingFace = _capFloor(spaceTop.force_2d(), spaceTop.level, model,
                                    MoosasFloor(ceilingFace))
            ceilingFace = ceilingFace.face + intersection.face
        else:
            ceilingFace = intersection.face
        ceiling = MoosasFloor(ceilingFace)
        floor = MoosasFloor(floorFace)
        return ceiling, floor


def spaceTopology(model: MoosasModel, break_wall_vertical=True) -> MoosasModel:
    """
    extract the space topology in the model.
    This module should be run after loading a file.

    1.calculate the containment of spaces and void.
    2.join void together if they can be a complete space.
    3.calculate the topology for edge,ceiling and floor.

    besides, the isOuter attribute of all Element will be decided here.
    the space information has already recorded in the elements.
    we only need to retrieve them and create a neighborhood relations

    Parameters
    ----------
    model : MoosasModel
        any input MoosasModel

    Returns
    -------
    MoosasModel
        The model for further transformation or analysis.
    """


    model.faceList = list(model.faceList)
    if break_wall_vertical:
        """join void into spaces"""
        print(f'\r2LSB: Checking void connection', end='')
        for i, void in enumerate(model.voidList):
            print(f'\r2LSB: Checking void connection {i}/{len(model.voidList)}', end='')
            # first, find a void with valid floor as the ground
            if void.floor is not None:
                if overlapArea(void.floor.force_2d(), void.edge.force_2d()) > void.area - geom.AREA_PRECISION:
                    metaVoids: list[MoosasSpace] = [void]
                    # find the void above to join them
                    while metaVoids[-1] is not None:
                        metaVoids.append(_findVoidAbove(metaVoids[-1]))
                    # Drop duplicated void (bottom void)
                    metaVoids.pop()
                    metaVoidsDelete = [s for s in metaVoids]
                    # if metaVoid is valid, add aperture to the space
                    if metaVoids[-1].ceiling is not None:
                        # copy all void to construct space
                        for j, v in enumerate(metaVoids):
                            metaVoids[j] = MoosasSpace(v.floor, v.edge, v.ceiling)

                        # add floors and ceilings to these spaces
                        for spaceBottom, spaceTop in zip(metaVoids[:-1], metaVoids[1:]):
                            spaceBottom.ceiling, spaceTop.floor = _findCoCeiling(spaceBottom, spaceTop)
                            # print([f.face for f in spaceBottom.ceiling.face])
                            model.ceilingList.append(spaceBottom.ceiling)
                            model.floorList.append(spaceTop.floor)

                        print(f'\n2LSB: Add{metaVoids} to space list.')
                        model.spaceList = list(np.append(model.spaceList, metaVoids))
                        model.voidList = list(set(model.voidList) - set(metaVoidsDelete))

        print()
    print(f'\r2LSB: Recording Boundary topology', end='')
    # regenerate id and record space-face topology
    for spId, space in enumerate(model.spaceList):
        ids = space.regenerateId()

    for spId, space in enumerate(model.spaceList):
        print(f"\r2LSB: Recording Boundary topology {spId}/{len(model.spaceList)}", end='')
        moFaces = space.getAllFaces(to_dict=True)

        # to avoid recalculating the wall, we only add once here
        for element in moFaces['MoosasWall']:
            if len(element.space) > 1:
                element.isOuter = False
                if element.space[0] == space.id:
                    space.add_neighbor(element.space[1], element)
                else:
                    space.add_neighbor(element.space[0], element)
        for element in moFaces['MoosasFloor']:
            if len(element.space) > 1:
                element.isOuter = False
                if element.space[0] == space.id:
                    space.add_neighbor(element.space[1], element)
                    model.spaceIdDict[element.space[1]].add_neighbor(space.id, element)
                else:
                    space.add_neighbor(element.space[0], element)
                    model.spaceIdDict[element.space[0]].add_neighbor(space.id, element)

    print()

    return model


def faceTopology(model: MoosasModel) -> MoosasModel:
    """
        extrude the face topology in the model.
        This module should be run after loading a file.

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """
    edgeDict = {}
    faces = model.getAllFaces(dumpUseless=True)
    faces = list(faces['MoosasWall']) + list(faces['MoosasFace'])
    for idf, face in enumerate(faces):
        print(f"\r2LSB: Extracting Faces topology {idf}/{len(faces)}", end='')
        if not isinstance(face, MoosasGlazing) or isinstance(face, MoosasSkylight):
            edgeStr = face.getEdgeStr()
            for edge in edgeStr:
                if edge not in edgeDict:
                    edgeDict[edge] = [face]
                else:
                    edgeDict[edge].append(face)

    print()
    for edIdx, edge in enumerate(edgeDict.keys()):
        print(f"\r2LSB: Extracting Faces topology {edIdx}/{len(edgeDict)}", end='')
        if len(edgeDict[edge]) > 1:
            for i in range(len(edgeDict[edge]) - 1):
                edgeDict[edge][i].neighbor[edge] = []
                for j in range(i + 1, len(edgeDict[edge])):
                    edgeDict[edge][i].neighbor[edge].append(edgeDict[edge][j].Uid)
                    if edge not in edgeDict[edge][j].neighbor:
                        edgeDict[edge][j].neighbor[edge] = []
                    edgeDict[edge][j].neighbor[edge].append(edgeDict[edge][i].Uid)

    print()
    return model


def _attach_shading(model: MoosasModel) -> MoosasModel:
    """
        attach shading elements to glazings.
        if the elements locate in the space, they will be treated as internal mass.
        if the elements locate outside, they will be allocated to the closed windows銆?

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """

    check_shading = np.array(model.wall_remain + model.face_remain)
    mask = [True] * len(check_shading)
    for eleidx, element in enumerate(check_shading):
        print(f'\rCONTENT: attach internal thermal mass:{eleidx}/{len(check_shading)}', end='')
        spaceList = searchBy('level', element.level, model.spaceList)
        for i in spaceList:
            if shapely.contains(model.spaceList[i].force_2d(), element.force_2d()):
                model.spaceList[i].addInternalMass(element)
                mask[i] = False
                break

    check_shading = check_shading[mask]
    print()
    for i, face in enumerate(check_shading):
        print(f'\rCONTENT: attach shading element:{i}/{len(check_shading)}', end='')
        centroid = face.getWeightCenter()
        bld_level = [level for level in model.levelList if level < centroid[2]]
        if len(bld_level) > 0:
            glazing = list(np.array(model.glazingList)[searchBy('level', bld_level[-1], model.glazingList)])
            glazing += list(np.array(model.skylightList)[searchBy('level', bld_level[-1], model.skylightList)])
            if len(glazing) == 0: continue
            target_glazing = [glazing[0], 10000.0]
            face_2d = face.force_2d()
            for gls in glazing:
                dis = shapely.distance(face_2d, gls.force_2d())
                if dis < target_glazing[1]:
                    target_glazing = [gls, dis]
            if target_glazing[1] < 1.5:
                target_glazing[0].shading.append(face)
    print()
    return model


def _copy_air_boundaries(model: MoosasModel) -> MoosasModel:
    """
        copy all the air boundaries in different level.

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """
    wallNew = []
    for levelIdx, bld_level in enumerate(model.levelList[:-1]):
        outerBound = outerBoundary(model, bld_level)
        if outerBound is not None:
            wallInLevel = np.array(model.wallList)[searchBy("level", bld_level, model.wallList)]
            for wid, w in enumerate(model.wallList):
                print(f'\rTOPOLOGY: Copy air boundaries in level {bld_level} {wid}/{len(model.wallList)}', end='')
                if w.level != bld_level:
                    for bound in outerBound:
                        if shapely.contains(bound, w.force_2d()):
                            # hit the range of the boundary of bld_level
                            found = False
                            for wIL in wallInLevel:
                                if equals(wIL.force_2d(), w.force_2d()):
                                    found = True
                                elif contains(wIL.force_2d(), w.force_2d()) or contains(w.force_2d(), wIL.force_2d()):
                                    wallNew.append(MoosasWall.fromProjection(w.force_2d(),
                                                                             bottom=wIL.level + wIL.offset,
                                                                             top=wIL.toplevel + wIL.topoffset,
                                                                             model=model))
                                    found = True
                            if not found:
                                wallNew.append(MoosasWall.fromProjection(w.force_2d(),
                                                                         bottom=bld_level,
                                                                         top=model.levelList[levelIdx + 1],
                                                                         model=model,
                                                                         airBoundary=True))
                            break
    print()
    model.wallList = list(np.append(model.wallList, wallNew))
    # solve containBy since some intermediate walls were added
    model = cleanseOverlapWall(model)
    return model


def _standardize(model: MoosasModel) -> MoosasModel:
    """
        standardize the walls and faces to simplify the model.

        Parameters
        ----------
        model : MoosasModel
            any input MoosasModel

        Returns
        -------
        MoosasModel
            The model for further transformation or analysis.
    """
    moFaces = model.getAllFaces()
    for idx, element in enumerate(moFaces):
        try:
            # MoosasFace.representation() flattens to its average elevation.
            # Keep existing inclined roof/skylight geometry intact.
            if isinstance(element, MoosasFace) and abs(np.asarray(element.normal, dtype=float)[2]) < 0.99:
                continue
            geo = element.representation()
            cat = mixItemListToList(element.category)[0] if isinstance(element, MoosasSkylight) or isinstance(element,
                                                                                                              MoosasGlazing) else 0
            geoId = model.includeGeo(geo, element.normal, cat=cat)
            element.replaceGeo(geoId)
            print(f'\rIO: standardizing faces {idx}/{len(moFaces)}', end='')
        except GeometryError as e:
            print("******Waring: GeometryError, this face would not be standardized")
    print()

    return model
