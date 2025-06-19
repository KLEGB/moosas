from ..utils import np, pygeos, GeometryError
from ..utils import path, parseFile, mixItemListToList
from ..utils.constant import geom
from ..geometry.element import MoosasGeometry
from ._obj import _readObj


def writeGeo(file_path, model=None, geoList=None, mask=None) -> str:
    """Get a *.geo file for the geometry library in the model

    .geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed......
    The .geo file format is: (cat: 0 is the opaque surface, 1 is the translucent surface, and 2 is the air wall)
    f,{polygon type cat},{polygon number idd}
    fn, {normal x}, {normal y}, {normal z}
    fv, {vertex 1x}, {vertex 1y}, {vertex 1z}
    ...
    fv,{vertex nx},{vertex ny},{vertex nz}
    fh,{aperture number},{vertex 1x},{vertex 1y},{vertex 1z}
    fh,{aperture number},{vertex nx},{vertex ny},{vertex nz}
    ;
    A face should end with ';'

    For example, there are two vertical faces with two openings with a positive x-axis normal vector:
    f,1,0
    fn,1.0,0.0,0.0
    fv,15.5,10.0,2.2
    fv,15.5,10.0,0.0
    fv,15.5,10.8,0.0
    fv,15.5,10.8,2.2
    fh,0,15.5,10.1,1.8
    fh,0,15.5,10.1,0.9
    fh,0,15.5,10.3,0.9
    fh,0,15.5,10.3,1.8
    fh,1,15.5,10.5,1.8
    fh,1,15.5,10.5,0.9
    fh,1,15.5,10.7,0.9
    fh,1,15.5,10.7,1.8
    ;
    f,1,0
    fn,1.0,0.0,0.0
    fv,12.5,10.0,2.2
    fv,12.5,10.0,0.0
    fv,12.5,10.8,0.0
    fv,12.5,10.8,2.2
    fh,0,12.5,10.1,1.8
    fh,0,12.5,10.1,0.9
    fh,0,12.5,10.3,0.9
    fh,0,12.5,10.3,1.8
    fh,1,12.5,10.5,1.8
    fh,1,12.5,10.5,0.9
    fh,1,12.5,10.7,0.9
    fh,1,12.5,10.7,1.8
    ;
    ...

    Args:
        file_path(str): output geo file path
        model(MoosasModel): model to export
        geoList(list(MoosasGeometry)): list of geometry objects to export
        mask(list[int]): mask for the geometry index in the geometry library. default is None

    Returns:
        geo file string

    Examples:
        >>>ids = [f.firstFaceId for f in model.spaceList[0].floor.face]
        >>>writeGeo('temp.geo',model,mask=ids)
    """
    path.checkBuildDir(file_path)
    if not geoList:
        geoList = []
    if mask and model:
        geoList += model.findFace(mask)
    elif model:
        geoIdSet = set([])
        for f in model.getAllFaces():
            geoIdSet = geoIdSet.union(mixItemListToList(f.faceId))
        geoIdSet = [model.geoId.index(faceId) for faceId in geoIdSet]
        geoList += list(np.array(model.geometryList)[list(geoIdSet)])
    geoStr = ''
    for geo in geoList:
        faceStr = 'f,' + str(geo.category) + ',' + str(geo.faceId) + '\n'
        faceStr += 'fn,'
        faceStr += ','.join([str(x) for x in pygeos.get_coordinates(geo.normal, include_z=True)[0]]) + '\n'
        rings = pygeos.get_rings(geo.face)
        for poi in pygeos.get_coordinates(rings[0], include_z=True)[:-1]:
            faceStr += 'fv,' + ','.join(poi.astype(str)) + '\n'
        if len(rings) > 1:
            for i in range(1, len(rings)):
                for poi in pygeos.get_coordinates(rings[i], include_z=True)[:-1]:
                    faceStr += f'fh,{i - 1},' + ','.join(poi.astype(str)) + '\n'
        geoStr += faceStr + ';\n'
    with open(file_path, 'w+') as f:
        f.write(geoStr)
    return geoStr


def objToGeo(file_path, geo_path):
    """Transform an *.obj file to *.geo file.

    Args:
        file_path(str): *.obj file path
        geo_path(str): *.geo file path

    Returns:
        None
    """
    from ..models import MoosasModel
    path.checkBuildDir(geo_path)
    model = MoosasModel()
    model.geometryList = _readObj(file_path)
    model.geoId = [geo.faceId for geo in model.geometryList]
    writeGeo(geo_path, model)


def geoLegacyToGeo(file_path, geo_path=None):
    """Transform a legacy *.geo file to new *.geo file.

        Args:
            file_path(str): legacy *.geo file path
            geo_path(str): *.geo file path. if None we will overwrite the original file.

        Returns:
            None
        """
    from ..models import MoosasModel
    path.checkBuildDir(geo_path)
    if geo_path is None:
        geo_path = file_path
    model = MoosasModel()
    model.geometryList = _readGeoLegacy(file_path)
    model.geoId = [geo.faceId for geo in model.geometryList]
    writeGeo(geo_path, model)


def _readGeo(file_path) -> list[MoosasGeometry]:
    """
    .geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed......
    The .geo file format is: (cat: 0 is the opaque surface, 1 is the translucent surface, and 2 is the air wall)
    f,{polygon type cat},{polygon number idd}
    fn, {normal x}, {normal y}, {normal z}
    fv, {vertex 1x}, {vertex 1y}, {vertex 1z}
    ...
    fv,{vertex nx},{vertex ny},{vertex nz}
    fh,{aperture number},{vertex 1x},{vertex 1y},{vertex 1z}
    fh,{aperture number},{vertex nx},{vertex ny},{vertex nz}
    ;
    A face should end with ';'

    For example, there are two vertical faces with two openings with a positive x-axis normal vector:
    f,1,0
    fn,1.0,0.0,0.0
    fv,15.5,10.0,2.2
    fv,15.5,10.0,0.0
    fv,15.5,10.8,0.0
    fv,15.5,10.8,2.2
    fh,0,15.5,10.1,1.8
    fh,0,15.5,10.1,0.9
    fh,0,15.5,10.3,0.9
    fh,0,15.5,10.3,1.8
    fh,1,15.5,10.5,1.8
    fh,1,15.5,10.5,0.9
    fh,1,15.5,10.7,0.9
    fh,1,15.5,10.7,1.8
    ;
    f,-1,0
    fn,1.0,0.0,0.0
    fv,12.5,10.0,2.2
    fv,12.5,10.0,0.0
    fv,12.5,10.8,0.0
    fv,12.5,10.8,2.2
    fh,0,12.5,10.1,1.8
    fh,0,12.5,10.1,0.9
    fh,0,12.5,10.3,0.9
    fh,0,12.5,10.3,1.8
    fh,1,12.5,10.5,1.8
    fh,1,12.5,10.5,0.9
    fh,1,12.5,10.7,0.9
    fh,1,12.5,10.7,1.8
    ;
    ...


    """
    blocks = parseFile(file_path)
    cat, idd, normal, faces, holes = [], [], [], [], []
    for blk in blocks:
        coordinates, holeCoordinates = [], {}
        for li in blk:
            if li[0] == "f":
                cat.append(int(float(li[1])))
                idd.append(li[2])
                continue
            if li[0] == "fn":
                try:
                    normal.append(pygeos.points(np.array(li[1:]).astype(float)))
                except:
                    print('******Warning: FileError, empty face normal.')
                    normal.append(None)
                continue
            if li[0] == "fv":
                coor = np.array(li[1:]).astype(float)
                coordinates.append(coor)
                continue
            if li[0] == "fh":
                if li[1] not in holeCoordinates:
                    holeCoordinates[li[1]] = []
                coor = np.array(li[2:]).astype(float)
                coor = geom.round(coor, geom.POINT_PRECISION)
                holeCoordinates[li[1]].append(list(coor))
                continue
        if len(coordinates) > 2:
            faces.append(pygeos.polygons(coordinates + [coordinates[0]]))
            holes.append([pygeos.polygons(holeCoordinates[coors] + [holeCoordinates[coors][0]]) for coors in
                          holeCoordinates.keys()])

    faces = _roundPolygons(faces, geom.POINT_PRECISION)
    geos: list[MoosasGeometry] = []
    for f, i, n, c, h in zip(faces, idd, normal, cat, holes):
        try:
            geos.append(MoosasGeometry(f, i, n, c, h, errors='raise'))
        except GeometryError as gE:
            print(f"******Waring: FileError: ignore face {i}: {gE.reason}")
    # for aperture,nor in zip (holes,normal):
    #    for aper in aperture:
    #        geos.append(Geometry(aper,str(len(geos)),nor,2))
    # plot_object(faces)
    return geos


def _roundPolygons(polygons: np.ndarray[pygeos.Geometry], precision: float) -> np.ndarray:
    """
    round the coordinates of polygons according to precision.
    graping the next near coordinates (x,y,z) to the past if their distance is less than precision.

        Args:
            polygons(np.ndarray[pygeos.Geometry]): polygons in np.ndarray format
            precision(float): round precision, usually would be geom.POINT_PRECISION

        Returns:
            np.ndarray rounded polygons
    """
    coordinates, coorLengthIndex = [], [0]
    for p in polygons:
        coor = pygeos.get_coordinates(p, include_z=True)
        coordinates += list(coor)
        coorLengthIndex += [coorLengthIndex[-1] + len(coor)]
    coordinates = np.array(coordinates)
    for dim in range(3):
        xIndex = np.argsort(coordinates[:, dim].flatten())
        xReindex = np.argsort(xIndex)
        coordinates = coordinates[xIndex]
        for i in range(1, len(xIndex) - 1):
            if np.abs(coordinates[i][dim] - coordinates[i + 1][dim]) < precision:
                coordinates[i + 1][dim] = coordinates[i][dim]
        coordinates = coordinates[xReindex]
    coordinates = geom.round(coordinates, precision)
    coordinates = [coordinates[idxS:idxE] for idxS, idxE in zip(coorLengthIndex[:-1], coorLengthIndex[1:])]
    return np.array([pygeos.polygons(coors) for coors in coordinates])


def _readGeoLegacy(file_path) -> list[MoosasGeometry]:
    '''
    .geo为moosasPy专用文件格式，为增加IO速度使用极简的文件结构……
    .geo文件格式为：(cat: 0为不透光面，1为透光面)
    Face{面类型cat} {面编号idd}
    Normal
    {法向量x} {法向量y} {法向量z}
    Vertices
    {顶点1x} {顶点1y} {顶点1z}
    ...
    {顶点nx} {顶点ny} {顶点nz}

    例如：
    Face1 0
    Normal
    1.0 1.2031856992204363e-15 -6.09788937479567e-16
    Vertices
    15.500000000000002 10.000000000000004 2.2
    15.500000000000002 10.000000000000004 0.0
    15.499999999999998 10.800000000000004 0.0
    15.500000000000002 10.800000000000004 2.2
    '''
    cat, idd, normal, faces = [], [], [], []
    with open(file_path, "r", encoding='utf-8') as f:
        read = f.readline()
        while read != '':
            if read[0:4] == "Face":
                cat.append(int(read[4]))
                idd.append(read[6:len(read) - 1])
                read = f.readline()
                continue
            if read[0:4] == "Norm":
                normal_t = str(f.readline().strip('\n')).split(" ")
                normal_t = np.array(normal_t).astype(float)
                normal.append(pygeos.points(normal_t))
                read = f.readline()
                continue
            if read[0:4] == "Vert":
                read = f.readline()
                pts_t = []
                while read[0:4] != "Face" and read != '':
                    pts_t.append(np.array(str(read.strip('\n')).split(" ")).astype(float))
                    read = f.readline()
                # if len(pts_t)>5:
                # pts_t=find_outerloop(pts_t)
                # else:
                # pts_t.append(pts_t[0])
                pts_t.append(pts_t[0])

                # faces.append(pygeos.linestrings(pts_t))
                faces.append(pygeos.polygons(pts_t))
                continue
            read = f.readline()
    faces = _roundPolygons(faces, geom.POINT_PRECISION)
    return [MoosasGeometry(f, i, n, c) for f, i, n, c in zip(faces, idd, normal, cat)]
