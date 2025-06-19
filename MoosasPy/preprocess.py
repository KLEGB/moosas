from __future__ import annotations


def coPlanner(inputFile: str, outputFile: str):
    """solve the co-planner issues of the input file: delete the redundant line of the faces
    using the same module in the cleanse process, that finding the co-edge and judge the co-planner
    then merge the elements together.
    ---------------------------------
    inputFile: input *.geo or *.obj or *.stl file
    outputFile: output file (only support *.geo)

    return: None
    """
    from .models import MoosasModel, MoosasElement, MoosasGeometry
    from .IO import modelFromFile, writeGeo
    from .geometry.cleanse import _coPlannerCleanse
    from .utils import pygeos
    if isinstance(inputFile, MoosasModel):
        model = inputFile
    else:
        model = modelFromFile(inputFile)
    elementList = [MoosasElement(model, geo, level=0, offset=0) for geo in model.geometryList]
    # the _coPlannerCleanse function could find and merge the co-planner elements
    cleanseElement, redundant = _coPlannerCleanse(elementList)

    geometryList = []
    for element in cleanseElement:
        multiFace = pygeos.get_parts(element.mergedFace)
        face, holes = [], []
        for f in multiFace:
            rings = pygeos.get_rings(f)
            if len(rings) > 1:
                face.append(rings[0])
                holes.append(rings[1:])
            else:
                face.append(rings[0])
                holes.append([])
        for f, h in zip(face, holes):
            geometryList.append(MoosasGeometry(f, element.faceId, element.normal, element.category, h))
    print(f"{len(elementList)} reduce to {len(geometryList)}. Writing...")
    writeGeo(outputFile, geoList=geometryList)


def overlap(inputFile: str, outputFile: str):
    """solve the overlap issues of the input file: remove the overlap faces then merge the elements together.
    the overlap would be only done on co-planner faces.

    ---------------------------------
    inputFile: input *.geo or *.obj or *.stl file
    outputFile: output file (only support *.geo)

    return: None
    """
    from .models import MoosasModel, MoosasElement, MoosasGeometry
    from .IO import modelFromFile, writeGeo
    from .geometry.cleanse import _groupByNormal, Projection
    from .utils import pygeos, np
    from .utils.constant import geom
    if isinstance(inputFile, MoosasModel):
        model = inputFile
    else:
        model = modelFromFile(inputFile)
    elementList = [MoosasElement(model, geo, level=0, offset=0) for geo in model.geometryList]
    elementGroup = _groupByNormal(elementList, [w.normal for w in elementList])
    treatFaces = 0
    for i, elements in enumerate(elementGroup):
        elements = np.array(elements)
        # project faces to 2d, and group them with the height and faces' category
        proj = Projection(origin=[0, 0, 0], unitZ=elements[0].normal)
        faces = [proj.toUV(ele.face) for ele in elements]
        faceZ = np.array([pygeos.get_coordinates(f, include_z=True)[0] for f in faces])[:,2].flatten()
        faceZ = np.round(faceZ, 2)
        for h in np.unique(faceZ):
            subElements = elements[faceZ == h]
            if len(subElements) > 0:
                subProj = Projection(origin=[0, 0, 0], unitZ=subElements[0].normal)
                subElementsFaces = [pygeos.force_2d(subProj.toUV(ele.face)) for ele in subElements]
                for j, ele in enumerate(subElements):
                    print(f"\rprocessing group {subProj.axisZ} on UVHeight {h}: {j}/{len(subElements)}", end='')
                    for jk in range(j + 1, len(subElements)):
                        if subElements[j].category == ele.category:
                            # check intersection
                            intersection = pygeos.intersection(subElementsFaces[j], subElementsFaces[jk],
                                                               grid_size=geom.POINT_PRECISION)
                            if pygeos.get_dimensions(intersection) == 2 and pygeos.area(
                                    intersection) > geom.AREA_PRECISION:
                                try:
                                    newFaceProj = pygeos.difference(subElementsFaces[j], subElementsFaces[jk])
                                    newFace = subProj.toWorld(pygeos.force_3d(newFaceProj, z=0))
                                    newFaceId = model.includeGeo(newFace, cat=subElements[j].category)
                                    subElements[j].replaceGeo(newFaceId)
                                    treatFaces+=1
                                except:
                                    pass
    print(f"\n{treatFaces} faces were edited. Writing...")
    geometryList = [ele.faceId for ele in elementList]
    geometryList = model.findFace(geometryList)
    writeGeo(outputFile, geoList=geometryList)