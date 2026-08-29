from __future__ import annotations


def coPlanner(inputFile: str, outputFile: str):
    """
    Solve co-planarity issues in a 3D geometry file by merging co-planar faces and removing redundant edges.
    
    Parameters
    ----------
    inputFile : str
        Path to the input geometry file. Supported formats include *.geo, *.obj, and *.stl.
        Alternatively, a `MoosasModel` object can be passed directly.
    outputFile : str
        Path to the output file. Only *.geo format is supported.
    
    Returns
    -------
    None
    """
    """solve the co-planner issues of the input file: delete the redundant line of the faces
    using the same module in the cleanse process, that finding the co-edge and judge the co-planner
    then merge the elements together.
    ---------------------------------
    inputFile: input *.geo or *.obj or *.stl file
    outputFile: output file (only support *.geo)

    return: None
    """
    from ..model import MoosasModel, MoosasElement, MoosasGeometry
    from .pipeline import _load_geometry_source
    from .importers.geo import writeGeo
    from .geometry.cleanse import _coPlannerCleanse
    from ..utils import shapely
    if isinstance(inputFile, MoosasModel):
        model = inputFile
    else:
        model = _load_geometry_source(inputFile)
    elementList = [MoosasElement(model, geo, level=0, offset=0) for geo in model.geometryList]
    # the _coPlannerCleanse function could find and merge the co-planner elements
    cleanseElement, redundant = _coPlannerCleanse(elementList)

    geometryList = []
    for element in cleanseElement:
        multiFace = shapely.get_parts(element.mergedFace)
        face, holes = [], []
        for f in multiFace:
            rings = shapely.get_rings(f)
            if len(rings) > 1:
                face.append(rings[0])
                holes.append(rings[1:])
            else:
                face.append(rings[0])
                holes.append([])
        for f, h in zip(face, holes):
            geometryList.append(MoosasGeometry(f, f"coPlanner_{len(geometryList)}", element.normal, element.category, h))
    print(f"{len(elementList)} reduce to {len(geometryList)}. Writing...")
    writeGeo(outputFile, geoList=geometryList)


def overlap(inputFile: str, outputFile: str):
    """
    Solve overlap issues in the input geometry file by removing overlapping co-planar faces and merging elements.
    
    Parameters
    ----------
    inputFile : str
        Path to the input geometry file. Supported formats are *.geo, *.obj, or *.stl.
        Alternatively, a `MoosasModel` object can be passed directly.
    outputFile : str
        Path to the output file. Only *.geo format is supported.
    
    Returns
    -------
    None
    """
    """solve the overlap issues of the input file: remove the overlap faces then merge the elements together.
    the overlap would be only done on co-planner faces.

    ---------------------------------
    inputFile: input *.geo or *.obj or *.stl file
    outputFile: output file (only support *.geo)

    return: None
    """
    from ..model import MoosasModel, MoosasElement, MoosasGeometry
    from .pipeline import _load_geometry_source
    from .importers.geo import writeGeo
    from .geometry.cleanse import _groupByNormal, Projection
    from ..utils import shapely, np
    from ..utils.constant import geom
    if isinstance(inputFile, MoosasModel):
        model = inputFile
    else:
        model = _load_geometry_source(inputFile)
    elementList = [MoosasElement(model, geo, level=0, offset=0) for geo in model.geometryList]
    elementGroup = _groupByNormal(elementList, [w.normal for w in elementList])
    treatFaces = 0
    for i, elements in enumerate(elementGroup):
        elements = np.array(elements)
        # project faces to 2d, and group them with the height and faces' category
        proj = Projection(origin=[0, 0, 0], unitZ=elements[0].normal)
        faces = [proj.toUV(ele.face) for ele in elements]
        faceZ = np.array([shapely.get_coordinates(f, include_z=True)[0] for f in faces])[:, 2].flatten()
        # Some upstream geometry loaders may yield object/string Z values.
        # Keep array length aligned with elements and mark invalid values as NaN.
        def _coerce_z(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return np.nan

        faceZ = np.array([_coerce_z(z) for z in faceZ], dtype=float)
        faceZ = np.round(faceZ, 2)
        valid_heights = np.unique(faceZ[~np.isnan(faceZ)])
        for h in valid_heights:
            subElements = elements[np.isclose(faceZ, h, equal_nan=False)]
            if len(subElements) > 0:
                subProj = Projection(origin=[0, 0, 0], unitZ=subElements[0].normal)
                subElementsFaces = [shapely.force_2d(subProj.toUV(ele.face)) for ele in subElements]
                for j, ele in enumerate(subElements):
                    print(f"\rprocessing group {subProj.axisZ} on UVHeight {h}: {j}/{len(subElements)}", end='')
                    for jk in range(j + 1, len(subElements)):
                        if subElements[j].category == ele.category:
                            # check intersection
                            intersection = shapely.intersection(subElementsFaces[j], subElementsFaces[jk],
                                                               grid_size=geom.POINT_PRECISION)
                            if shapely.get_dimensions(intersection) == 2 and shapely.area(
                                    intersection) > geom.AREA_PRECISION:
                                try:
                                    newFaceProj = shapely.difference(subElementsFaces[j], subElementsFaces[jk])
                                    newFace = subProj.toWorld(shapely.force_3d(newFaceProj, z=0))
                                    newFaceId = model.includeGeo(newFace, cat=subElements[j].category)
                                    subElements[j].replaceGeo(newFaceId)
                                    treatFaces+=1
                                except:
                                    pass
    print(f"\n{treatFaces} faces were edited. Writing...")
    geometryList = [ele.faceId for ele in elementList]
    geometryList = model.findFace(geometryList)
    writeGeo(outputFile, geoList=geometryList)
