# 去重方法
from __future__ import annotations
import copy
import numpy as np
import pygeos

from .element import *
from ..utils.tools import searchBy
from ..utils.constant import geom
from .geos import equals, overlapEdge, Vector
from ..encoding.convexify import triangulate2dFace


def _groupByNormal(listToGroup: list, listOfNormal: list[pygeos.Geometry | np.ndarray]) -> list[list]:
    """group the items by their normal.
        The items with same factor (both positive and negative) will be pushed in the same group

        ---------------------------------
        listToGroup: anything that need to be grouped
        listOfNormal: the guidance vector, with the same lengh as listToGroup

        return: 2-dimensional list with the same type as listToGroup
    """
    if len(listOfNormal) != len(listToGroup):
        raise Exception('items and normals should have same number.')
    listToGroup = np.array(listToGroup)
    normalGroup,uniqueNormal = [[len(listOfNormal)-1]],[listOfNormal[-1]]
    for i,nor in enumerate(listOfNormal[:-1]):
        matched = False
        for g,un in enumerate(uniqueNormal):
            if Vector.parallel(nor,un):
                normalGroup[g].append(i)
                matched = True
                break
        if not matched:
            normalGroup.append([i])
            uniqueNormal.append(nor)

    itemsGroup = [list(listToGroup[groupIdx]) for groupIdx in normalGroup]
    return itemsGroup

    normal_ = [Vector(normal).string for normal in listOfNormal]
    sortedGroup = {nor: [] for nor in np.unique(normal_)}
    for nor, item in zip(normal_, listToGroup):
        sortedGroup[nor].append(item)
    return list(sortedGroup.values())


def _groupRelateArray(sequences: list) -> list:
    """join array together if they have intersections"""
    sequenceSet = [set(s) for s in sequences]
    length = len(sequenceSet)
    for _ in range(length):
        s = sequenceSet.pop()
        flag = True
        for i in np.arange(len(sequenceSet) - 1, -1, -1):
            if set(s) & set(sequenceSet[i]):
                sequenceSet[i] = s | sequenceSet[i]
                flag = False
                break
        if flag:
            sequenceSet = [s] + sequenceSet
    return [list(s) for s in sequenceSet]


def _groupByCollinear(listToGroup: list, listOfNormal: list[pygeos.Geometry | np.ndarray],
                      listOfGeometry: list[pygeos.Geometry]) -> list[list]:
    """push linestring in a group if they are collinear. based on _groupByNormal function"""
    if len(listOfNormal) != len(listToGroup) or len(listOfNormal) != len(listOfGeometry):
        raise Exception('items and normals should have same number.')
    if len(listOfNormal)==0:
        return listToGroup
    groupIdx = _groupByNormal(list(np.arange(len(listToGroup))), listOfNormal)
    listToGroup = [np.array(listToGroup)[group] for group in groupIdx]
    listOfNormal = [np.array(listOfNormal)[group] for group in groupIdx]
    listOfGeometry = [np.array(listOfGeometry)[group] for group in groupIdx]
    groups = []
    for itemGroup, norGroup, geometryGroup in zip(listToGroup, listOfNormal, listOfGeometry):
        extremePoint = np.min(pygeos.get_coordinates(geometryGroup), axis=0)
        pointOnLines = [pygeos.get_coordinates(geo)[0] for geo in geometryGroup]
        distance = [Vector.dot(nor, poi - extremePoint) for nor, poi in zip(norGroup, pointOnLines)]
        thisGroups = {dist: [] for dist in np.unique(distance)}
        for item, dist in zip(itemGroup, distance):
            thisGroups[dist].append(item)
        for gp in list(thisGroups.values()):
            groups.append(gp)
    return groups


def partitionWall(walls: list[MoosasWall], model: MoosasContainer, bottom=None, top=None) -> list[MoosasWall]:
    """partition the walls by sorting their coordinates and making polygon using the top and bottom boundaries
    the glazing of all walls will be collected and try to attach to the new wall again.
    """
    coor = pygeos.points(pygeos.get_coordinates([w.force_2d() for w in walls]))

    coor = list(pygeos.get_coordinates(list(set(coor))))

    coor.sort(key=lambda x: (x[0], x[1]))
    top = np.max([wall.toplevel + wall.topoffset for wall in walls]) if top is None else top
    bottom = np.min([wall.level + wall.offset for wall in walls]) if bottom is None else bottom
    gls: list[MoosasGlazing] = []
    for wall in walls:
        gls = list(np.append(gls, np.array(wall.glazingElement)))

    # print(coor, bottom, top, gls)
    wallNew: list[MoosasWall] = MoosasWall.fromSeriesPoint(pygeos.points(coor), bottom, top, gls, model)
    return wallNew


def _fastOverlap(wall1: pygeos.Geometry, wall2: pygeos.Geometry) -> bool:
    """very fast calculate weather two walls are containBy
    according the sequence of their coordinates
    """
    coor = list(np.append(pygeos.get_coordinates([wall1, wall2]), [[0], [0], [1], [1]], axis=1))
    coor.sort(key=lambda x: (x[0], x[1]))
    if not coor[0][2] == coor[1][2]:
        if Vector(coor[1][:2] - coor[2][:2]).length() > geom.POINT_PRECISION:
            return True
    return False


def solve_duplicated_level(model: MoosasContainer) -> MoosasContainer:
    """remove duplicated levels,
     and put geometries on those levels onto the bottom level
     """
    del_level = []
    for i in range(1, len(model.levelList)):
        target = searchBy('level', model.levelList[i], model.faceList)
        # print(f'level {model.levelList[i]}, floors {len(target)}')
        # plot_object(np.array(model.faceList)[target])
        sum_area = np.sum([pygeos.area(model.faceList[item].force_2d()) for item in target])
        if sum_area < geom.LEVEL_MIN_AREA:
            for item in target:
                model.faceList[item].offset = \
                    model.faceList[item].level + model.faceList[item].offset - model.levelList[i - 1]
                model.faceList[item].level = model.levelList[i - 1]
            del_level.append(i)
    model.levelList = np.delete(model.levelList, del_level).tolist()
    return model


def solve_duplicated_wall(model: MoosasContainer) -> MoosasContainer:
    """
        Identify the duplicated walls that 2 points of them are placed nearby
        you must solve duplication before solving containment
        this func is based on _groupByCollinear. if _groupByCollinear do not perform well, serious error will occur here
    """
    """build up tue duplication check list"""
    duplicateCheckList: list[list[int]] = []
    duplicatedWall: list[int] = []
    edge2d = [w.force_2d() for w in model.wallList]
    for bld_level in model.levelList:

        wall_list = searchBy('level', bld_level, model.wallList)
        wall_group: list[list[int]] = _groupByCollinear(listToGroup=wall_list,
                                                        listOfNormal=[model.wallList[w].normal for w in
                                                                      wall_list],
                                                        listOfGeometry=[model.wallList[w].force_2d() for w in
                                                                        wall_list])
        for wall_list in wall_group:
            for i in range(len(wall_list)):
                duplicateCheckList.append(wall_list[i:])

    """check if the walls are duplicated, and dissolve that wall into the others"""
    for wl, task in enumerate(duplicateCheckList):
        print(f'\rCLEANSE: Duplicated checking: {wl}/{len(duplicateCheckList)}', end='')
        for i in range(1, len(task)):
            if equals(edge2d[task[0]], edge2d[task[i]]):
                model.wallList[task[i]].dissolve(model.wallList[task[0]])
                duplicatedWall.append(task[0])
                break

    print()
    model.wallList = np.delete(model.wallList, duplicatedWall)
    return model


def solve_overlapped_wall(model: MoosasContainer) -> MoosasContainer:
    """ Solve the overlapped of walls.

    Identify the big walls which overlaps with a small walls or other walls,
    and break the big walls according to the walls' intersections.

    To ensure the efficiency, this func do a lot of simplifications on geometries including:
    1. represent all walls in 2d.
    2. 'containBy' means the end points of two (or more) walls are not in sequences.
    3. all walls will be reconstructed using only 4 points to get simplified representations.
    4. the height of walls will be regarded as the same, but will be extended or trimmed to the top of the level.

    P.S.
    you must solve duplication before solving containment
    this func is based on _groupByCollinear. if _groupByCollinear do not perform well, serious error will occur here
    """
    """build the containment check list"""
    containCheckList: list[list[int]] = []
    mergeGroup: list[set[int]] = []
    for bld_level in model.levelList:
        wall_list = searchBy('level', bld_level, model.wallList)
        wall_group = _groupByCollinear(listToGroup=wall_list,
                                       listOfNormal=[model.wallList[w].normal for w in wall_list],
                                       listOfGeometry=[model.wallList[w].force_2d() for w in wall_list])
        for wall_list in wall_group:
            for i in range(len(wall_list)):
                containCheckList.append(wall_list[i:])

    """check containment and build the mergeGroup"""
    for i, task in enumerate(containCheckList):
        print(f'\rCLEANSE: Overlapped checking: {i+1}/{len(containCheckList)}', end='')
        solveWall = model.wallList[task[0]]
        for others in task[1:]:
            if _fastOverlap(solveWall.force_2d(), model.wallList[others].force_2d()):
                mergeGroup.append({task[0], others})
    # print('finish.')
    """merge the sets if a & b != None"""
    mergeGroup = _groupRelateArray(mergeGroup)

    """partition the walls into new walls"""
    wallNew = []
    for i,group in enumerate(mergeGroup):
        wallNew += partitionWall(np.array(model.wallList)[list(group)], model)
        print(f'\rCLEANSE: Overlapped checking merging:{i+1}/{len(mergeGroup)}', end='')

    """delete the old walls"""
    delList = [item for group in mergeGroup for item in list(group)]
    model.wallList = np.append(np.delete(model.wallList, delList), wallNew)

    print()
    return model


def solve_invalid_wall(model: MoosasContainer) -> MoosasContainer:
    """check if the walls are valid including:
    1.zone length or zero height wall
    2.invalid pygeos.Geometry
    3.then dissolve those walls to others valid walls,
    which have coincident edge with the invalid walls and lay below the them.
    """

    def _isValid(_wall: MoosasWall) -> int:
        # for face in np.array(wall.face).flatten():
        # if not pygeos.is_valid(face):
        #    print(face)
        #    return -1
        if pygeos.get_dimensions(wall.force_2d()) <= 0:
            return 1
        if Vector(wall.force_2d()).length() < geom.POINT_PRECISION:
            return 2
        if wall.area3d() < geom.POINT_PRECISION*geom.POINT_PRECISION:
            return 2
        if (wall.level + wall.offset) == (wall.toplevel + wall.topoffset):
            return -1
        return 0

    """build the check list for walls' validation"""
    del_face = []
    check_list = list(np.arange(len(model.wallList)))
    total = len(check_list)
    while len(check_list) > 0:
        i = check_list.pop()
        wall = model.wallList[i]
        print(f'\rCLEANSE: Invalid checking: {total - len(check_list)}/{total}', end='')
        if _isValid(wall) != 0:
            del_face.append(i)
            if _isValid(wall) > 0:
                searchLevel = model.levelList.index(wall.level) - 1
                searchLevel = [model.levelList[searchLevel] + wall.level]

                """find a wall to dissolve this invalid wall"""
                checkWall = [index for index in searchBy('level', searchLevel, model.wallList) if
                             not (index in del_face)]
                for j in checkWall:
                    if overlapEdge(wall.face, model.wallList[j].face):
                        if model.wallList[j].height <= wall.height:
                            model.wallList[j].dissolve(wall)
                            check_list.append(j)
                            break


    print(f"\t\tdel walls {len(del_face)}")
    model.wallList = list(np.delete(model.wallList, del_face))
    return model


def solve_invalid_face(model: MoosasContainer) -> MoosasContainer:
    """check if the faces are valid including:
    face.force2d() was valid 2d geometry.
    all faces would be triangulated before testing
    """
    delface = []
    for i, face in enumerate(model.faceList):
        if not pygeos.is_valid(face.force_2d()):
            print(f"***Warning: invalid horizontal face detected:{face.face}")
            delface.append(i)
    model.faceList = np.delete(model.faceList, delface)
    return model


def solve_redundant_line(model: MoosasContainer) -> MoosasContainer:

    total_a = len(model.wallList)
    for bld_level in model.levelList:
        total = len(model.wallList)
        face_list = np.array(model.wallList)[searchBy('level', bld_level, model.wallList)]
        _,redundant = _coPlannerCleanse(face_list)
        if len(redundant) >0:
            redundant = [list(model.wallList).index(w) for w in redundant]
            model.wallList = list(np.delete(model.wallList, redundant))
        print(f'\rCLEANSE: Merge walls: {total - len(model.wallList)} in Level: {bld_level}', end='')
    print(f"\t\ttotal merge wall: {total_a - len(model.wallList)}")
    return model

def _coPlannerCleanse(elements: np.ndarray[MoosasElement]) -> (np.ndarray[MoosasElement],np.ndarray[MoosasElement]):
    """Delete Coplanar Lines: Lines with and only two adjacent faces are coplanar lines.

    This function works within 3d spaces, and operates directly on the geometries of the walls.
    It provides a clean set of walls for glazing matching and close contour calculation,
    as well as significantly improves the performance for other cleanse functions.

    This function needs to ensure the cleanse performance.
    Therefore, it will not do any simplifications on the geometries,
    which means a very high calculation cost.

    In the future, a multi processes should be added to this func.

    The process of the func can be described as:
    1. Traverse the horizontal & vertical planes of the same floor and create a dict of all lines (initialized with set())
    2. Iterate over dict to get set() of length 2
    3. Check whether the walls A and B in the set have a common line corresponding to the set length of 2
    4. Iterate through all sets and sets with common elements
    5. Iterate through all sets after the cleanup and call the dissolve method
    ---------------------------------
    elements: MoosasElement or MoosasGeometry as input

    Return: merged elements,redundant elements (np.ndarray[MoosasElement],np.ndarray[MoosasElement])
    """
    faceNum = len(elements)
    currentFaceNum = 0
    redundant = []
    while currentFaceNum != faceNum:
        currentFaceNum = faceNum
        edgeDict = {}

        """Get the topology of all faces"""
        for faceIdx, moface in enumerate(elements):
            edges = moface.getEdgeStr()
            for edge_str in edges:
                if edge_str not in edgeDict.keys():
                    edgeDict[edge_str] = [faceIdx]
                else:
                    edgeDict[edge_str] += [faceIdx]

        """Find coPlane faces"""
        _dissolveFaces = []
        for faces in edgeDict.values():
            if len(faces) == 2:
                if Vector.parallel(Vector(elements[faces[0]].normal), Vector(elements[faces[1]].normal)):
                    coedges = set(elements[faces[0]].getEdgeStr()) & set(elements[faces[1]].getEdgeStr())
                    if len([edge_str for edge_str in list(coedges) if len(edgeDict[edge_str]) > 2]) == 0:
                        _dissolveFaces.append({faces[0],faces[1]})

        """Merge dissolve groups"""
        to_dissolveFaces = _groupRelateArray(_dissolveFaces)

        """Dissolve each group"""
        delfaces = set()
        for faces in to_dissolveFaces:
            faces = list(faces)
            parentFace = elements[faces[0]]
            childFaces = [elements[i] for i in faces[1:]]
            delfaces = delfaces | set(faces[1:])
            redundant += childFaces
            parentFace.dissolve(childFaces)

        elements = list(np.delete(elements, list(delfaces)))
        faceNum = len(elements)
    return elements,redundant

def solveIntersectionVertical(model: MoosasContainer) -> MoosasContainer:
    """Calculate the intersection of walls projection in 2d for each floor
    then break those walls into parts.

    this method cannot use to solve the intersection on vertical and horizontal faces,
    but only solve the intersection between vertical faces (walls).
    Besides, since we implement the function in 2d space, any 3d relations will be ignored.
    in this case, this function do not care about any walls cross multi-level.
    """
    delWalls, newWalls = [], []
    prs = 0

    for bld_level in model.levelList:
        wall_list = searchBy('level', bld_level, model.wallList)
        wallElement = np.array(model.wallList)[wall_list]
        wall2d = np.array([w.force_2d() for w in wallElement])

        for i, wall, w2d in zip(wall_list, wallElement, wall2d):
            prs += 1

            print(f"\rCLEANSE: solve horizontal intersection {prs}/{len(model.wallList)}", end='')
            parallel = [not(Vector.parallel(Vector(wall.normal), Vector(w.normal))) for w in wallElement]
            testSet2d = wall2d[parallel]
            for w2dOther in testSet2d:
                intersection = pygeos.intersection(w2d, w2dOther,grid_size=1.5*geom.POINT_PRECISION)
                # print(w2d, w2dOther,Vector.parallel(Vector(w2d), Vector(w2dOther)),intersection)
                if (not pygeos.is_empty(intersection)) and pygeos.get_dimensions(intersection)==0:
                    twins =pygeos.points(pygeos.get_coordinates(w2d))
                    if not (pygeos.dwithin(twins[0], intersection, geom.POINT_PRECISION) or pygeos.dwithin(twins[1], intersection,geom.POINT_PRECISION)):
                        brkResult = MoosasWall.break_(wall, intersection)
                        if brkResult is not None:
                            newWalls += brkResult
                            delWalls.append(i)
                # if pygeos.contains(w2d, poi):
                #     twins = pygeos.points(pygeos.get_coordinates(w2d))
                #     if not (pygeos.dwithin(twins[0], poi, geom.POINT_PRECISION) or pygeos.dwithin(twins[1], poi,
                #                                                                                   geom.POINT_PRECISION)):
                #         wall1, wall2 = MoosasWall.break_(wall, poi)
                #         newWalls += [wall1, wall2]
                #         delWalls.append(i)
    print(f'\tbreak walls:{len(delWalls)}',end='')

    model.wallList = list(np.delete(model.wallList, delWalls))
    model.wallList += newWalls
    print()
    return model


def solveIntersectionHorizontal(model: MoosasContainer) -> MoosasContainer:
    dividedCount = 0
    for bldLevelIndex in range(len(model.levelList)):
        faces = list(np.array(model.faceList)[searchBy('level', model.levelList[bldLevelIndex], model.faceList)])
        edges = []
        if bldLevelIndex > 0:
            edges += list(np.array(model.edgeList)[searchBy('level', model.levelList[bldLevelIndex-1], model.edgeList)])
        if bldLevelIndex < len(model.levelList) - 1:
            edges += list(np.array(model.edgeList)[searchBy('level', model.levelList[bldLevelIndex], model.edgeList)])

        # from ..visual.geometry import plot_object
        # plot_object(edges,faces,colors=['blue','black'])
        dividedFaces = []

        while len(faces) > 0:
            f = faces.pop()
            dividedFaces.append(f)
            try:
                for e in edges:
                    intersectArea = overlapArea(e.force_2d(), f.force_2d())
                    if intersectArea > geom.AREA_PRECISION:
                        if intersectArea < f.area - geom.AREA_PRECISION:
                            # it means the MoosasFace need to be split
                            splitF = splitFaces(f, e)
                            if splitF is not None:
                                if len(splitF[1])>0 and splitF[0] is not None:
                                    faces += [splitF[0]] + splitF[1]
                                    dividedFaces.pop()
                                    dividedCount += 1
                                    break
            except GeometryError:
                pass
            print(f'\rPACKING: containBy checking for horizontal Faces-Level{model.levelList[bldLevelIndex]} remain:{len(faces)}', end='')
    print(f'\tdivided horizontal faces: {dividedCount}')
    return model


def splitFaces(face: MoosasFace, edge: MoosasEdge) -> (MoosasFace, list[MoosasFace]):
    """split the face into the intersection with edge's boundary and the remained part
    if the face is not a planar face or the face is incline,
    it will not be changed since it is seldom connects to other spaces
    ***you should check if the face overlaps with the edge first by overlapArea method!!
    ***intersection will only create one face, but pygeos.difference can create multi faces!!
    """
    model: MoosasContainer = face.parent
    if not Vector.parallel(face.normal, [0, 0, 1]):
        return [face,[]]
    if face not in model.faceList:
        return [face,[]]

    f2d = makeValid(face.force_2d())[0]
    # print(pygeos.is_valid_reason(f2d), edge.force_2d())
    """split opaque part"""
    innerFace = pygeos.force_3d(pygeos.intersection(f2d, edge.force_2d(),grid_size=geom.POINT_PRECISION), z=face.elevation)
    outerFace = pygeos.force_3d(pygeos.difference(f2d, edge.force_2d(),grid_size=geom.POINT_PRECISION), z=face.elevation)

    innerFace = makeValid(innerFace)[0]
    outerFace = [makeValid(outf)[0] for outf in pygeos.get_parts(outerFace) if not pygeos.is_empty(outf)]
    # outerFace = [makeValid(f)[0] for ff in outerFace for f in ff]
    if pygeos.area(innerFace)>geom.AREA_PRECISION:
        innerFace = MoosasFace(model=model,
                               faceId=model.includeGeo(innerFace, Vector([0, 0, 1]).geometry, face.category))
    else:
        return None
    for i, outf in enumerate(outerFace):
        if pygeos.area(outerFace[i]) > geom.AREA_PRECISION:
            outerFace[i] = MoosasFace(model=model,
                                      faceId=model.includeGeo(outf, Vector([0, 0, 1]).geometry, face.category))
        else:
            outerFace[i] = None
    outerFace = [outf for outf in outerFace if outf is not None]
    if len(outerFace)==0:
        return None
    model.faceList = list(np.append(np.append(model.faceList, [innerFace]), outerFace))
    model.faceList.remove(face)

    """split aperture part"""
    innerGlazings, outerGlazings = [], []  # record for inner and outer skylights
    for gls in face.glazingElement:
        g2d = makeValid(gls.force_2d())[0]
        overArea = overlapArea(g2d, edge.force_2d())

        # aperture lay inside the edge
        if overArea > gls.area - geom.AREA_PRECISION:
            innerGlazings = np.append(innerGlazings, [gls])

        # aperture lay outside the edge
        elif overArea == 0:
            outerGlazings = np.append(outerGlazings, [gls])

        # aperture need to be split
        else:
            innerGls = pygeos.force_3d(pygeos.intersection(g2d, edge.force_2d(),grid_size=geom.POINT_PRECISION), z=face.elevation)
            outerGls = pygeos.force_3d(pygeos.difference(g2d, edge.force_2d(),grid_size=geom.POINT_PRECISION), z=face.elevation)
            outerGls = pygeos.get_parts(outerGls)

            innerGls = MoosasSkylight(model=model,
                                      faceId=model.includeGeo(makeValid(innerGls)[0], Vector([0, 0, 1]).geometry,
                                                              gls.category))
            for i, outf in enumerate(outerGls):
                outerGls[i] = MoosasSkylight(model=model,
                                             faceId=model.includeGeo(makeValid(outf)[0], Vector([0, 0, 1]).geometry,
                                                                     gls.category))

            model.skylightList = list(np.append(np.append(model.skylightList, [innerGls]), outerGls))
            model.skylightList.remove(gls)
            innerGlazings = np.append(innerGlazings, [innerGls])
            outerGlazings = np.append(outerGlazings, outerGls)
    """attach the inner and outer skylight to the MoosasFace"""
    for gls in innerGlazings:
        innerFace.add_glazing(gls)
    for gls in outerGlazings:
        for outf in outerFace:
            if pygeos.contains(outf.force_2d(), gls.force_2d()):
                outf.add_glazing(gls)
                break

    return innerFace, outerFace
