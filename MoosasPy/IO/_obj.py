from ..utils import np, pygeos, ET, json,GeometryError
from ..utils import to_dictionary, path, parseFile, mixItemListToList
from ..utils.constant import geom
from ..geometry.element import MoosasGeometry

def _readObj(file_path) -> list[MoosasGeometry]:
    obj_file, mtl_file = [], []
    material_lab = {}
    """
    *.obj file structure: The null line separates a block
        The first block is the file header
        The second block is the MTL file name
        The third block starts with the body of the text, corresponding to the following line markup:
        g mesh name
        v vertices
        vt vertices material coordinates
        vn vertices normal vectors
        f face, each representing a vertices: v/vt/vn number
        Each block defines a face, which can be merged directly without blank lines

    *.mtl file structure: The null line separates a block
        The first block is the file header
        The format of subsequent blocks is as follows
        newmtl material_name
        Ka 0.000000 0.000000 0.000000
        Kd 0.800000 0.921569 0.956863
        Ks 0.330000 0.330000 0.330000
        d 0.500000
        map_Kd test/material_map.jpg
    """
    with open(file_path) as f:
        line = f.readline()
        block = []
        while line:
            block.append(line)
            if not line.strip('\n'):
                obj_file.append(block)
                block = []
            line = f.readline()

    mtl_path = file_path.split('\\')[0:-1] + [obj_file[1][0].strip('\n').split(' ')[1]]
    mtl_path = ('\\').join(mtl_path)

    with open(mtl_path) as f:
        line = f.readline()
        block = []
        while line:
            block.append(line)
            if not line.strip('\n'):
                mtl_file.append(block)
                block = []
            line = f.readline()
    # print (mtl_file)
    for block in mtl_file[1:]:
        material_name = block[0].strip('\n').split(' ')[1]
        mat = {block[i].strip('\n').split(' ')[0]: block[i].strip('\n').split(' ')[1:] for i in range(1, len(block)) if
               block[i].strip('\n')}
        material_lab[material_name] = mat

    obj_file = [line for block in obj_file[3:] for line in block]
    v, vn, obj_faces = [], [], []
    # vt=[] #暂不需要读取材质坐标
    material_this = ''

    for line in obj_file:
        line = line.strip('\n').split(' ')
        if line[0] == 'usemtl': material_this = line[1]
        if line[0] == 'v': v.append(np.array(line[1:4]).astype(float))
        # if line[0] == 'vt' : vt.append(line[1:])
        if line[0] == 'vn': vn.append(np.array(line[1:4]).astype(float))
        if line[0] == 'f':
            f = {
                'material': material_this,
                'vertices': [],
                # 'vertices_texture': [],
                'normal': []
            }
            for node in line[1:]:
                if node == '': continue
                node = node.split('/')
                v_ver = int(node[0]) - 1
                if v_ver < 0: v_ver += 1
                f['vertices'].append(v[v_ver])
                f['normal'].append(vn[int(node[2]) - 1])

            f['normal'] = np.array([np.round(np.mean(nor_d), 3) for nor_d in np.array(f['normal']).T]).astype(float)
            obj_faces.append(f)
    # print('obj face number:',len(obj_faces))
    cat, idd, normal, faces = [], [], [], []
    for i in range(len(obj_faces)):
        idd.append(i)
        normal.append(pygeos.points(obj_faces[i]['normal']))
        pts = obj_faces[i]['vertices']
        pts.append(pts[0])
        faces.append(pygeos.polygons(pts))
        cat.append(0)
        if 'd' in material_lab[obj_faces[i]['material']].keys():
            if float(material_lab[obj_faces[i]['material']]['d'][0]) < 1.0:
                cat.pop()
                cat.append(1)
    faces = _roundPolygons(faces,geom.POINT_PRECISION)
    return [MoosasGeometry(f, i, n, c) for f, i, n, c in zip(faces, idd, normal, cat)]

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
    coordinates,coorLengthIndex = [],[0]
    for p in polygons:
        coor = pygeos.get_coordinates(p, include_z=True)
        coordinates+= list(coor)
        coorLengthIndex += [coorLengthIndex[-1]+len(coor)]
    coordinates = np.array(coordinates)
    for dim in range(3):
        xIndex = np.argsort(coordinates[:,dim].flatten())
        xReindex = np.argsort(xIndex)
        coordinates = coordinates[xIndex]
        for i in range(1,len(xIndex)-1):
            if np.abs(coordinates[i][dim] - coordinates[i+1][dim])<precision:
                coordinates[i + 1][dim] = coordinates[i][dim]
        coordinates = coordinates[xReindex]
    coordinates = geom.round(coordinates, precision)
    coordinates = [coordinates[idxS:idxE] for idxS,idxE in zip(coorLengthIndex[:-1],coorLengthIndex[1:])]
    return np.array([pygeos.polygons(coors) for coors in coordinates])