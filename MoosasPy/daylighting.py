from .rad import _meshToRadObject, _materialLib, _getSky
from .models import MoosasModel
from .geometry import MoosasElement, MoosasGrid, Vector, MoosasSpace,Projection
from .utils import np, pygeos, path, callCmd, os,mixItemListToList
from datetime import datetime


def simModel(model: MoosasModel, date: datetime, skyType, lat=39.93, lon=116.28, diff=15000,
             radPath=rf"{path.libDir}\rad\model.rad", gridPath=rf"{path.libDir}\rad\grid.input"):
    """
        Simulate a model by embedded RADIANCE module.
        gensky.exe is implemented with the params input.

        Parameters
        ----------
        model : MoosasModel
            the model for simulation
        date : datetime
            the date to generate the sky
        skyType : str
            the skyType hint for radiance, -c means the cloudy sky
        lat : float
            latitude of the location
        lon : float
            longitude of the location
        diff : float , optional
            diffuse illuminance for the cloudy sky (Default : 15000)
        radPath : str , optional
            redirect the rad output file.
        gridPath : str , optional
            redirect the grid output file

        Returns
        -------
        dict
            the daylighting simulation result on the floor:
            [{df:daylight factor, satisfied: satification}...{}]

    """
    floor = []
    if os.path.exists(gridPath):
        os.remove(gridPath)
    for spc in model.spaceList:
        faces = spc.getAllFaces(to_dict=True)
        for moface in faces["MoosasFloor"]:
            floor = np.append(floor, moface)
    modelToRad(model, date, skyType, lat, lon, diff, radPath)
    floorDict = [{"Uid": fl.Uid, "element": fl, "gridLength": len(writeGrid(fl, normal=[0, 0, 1], gridPath=gridPath))}
                 for fl in floor]
    callCmd(rf"{path.libDir}\rad\run_moosas.bat", cwd=rf"{path.libDir}\rad")
    with open(rf"{path.libDir}\rad\ill_moosas.output", "r") as f:
        for i in range(len(floorDict)):
            res = []
            for _ in range(floorDict[i]["gridLength"]):
                res.append(float(f.readline()))
            floorDict[i]["df"] = np.mean(res) / diff
            floorDict[i]["satisfied"] = np.sum([i > 300.0 for i in res]) / len(res)

        return floorDict


def _generateRadGeo(roof, floor, others):
    geoStr = ''
    ids = 0
    for moFace in floor:
        geoStr += _meshToRadObject(triOpaque(moFace), "default_floor", ids)
        ids += 1
    for moFace in roof:
        geoStr += _meshToRadObject(triOpaque(moFace), "default_roof", ids)
        ids += 1
    for moFace in others:
        if moFace.category == 0:
            geoStr += _meshToRadObject(triOpaque(moFace), "default_wall", ids)
        if moFace.category == 1:
            geoStr += _meshToRadObject(moFace.representation(), "glazing_", ids)
        ids += 1
    return geoStr


def modelToRad(model: MoosasModel, date: datetime, skyType, lat, lon, diff=10000,
               radPath=rf"{path.libDir}\rad\model.rad"):
    roof, floor, others = [], [], []
    for spc in model.spaceList:
        faces = spc.getAllFaces(to_dict=True)
        ceils, ground = [], []
        for moface in faces["MoosasCeiling"]:
            ceils = np.append(ceils, moface)
        for moface in faces["MoosasFloor"]:
            ground = np.append(ground, moface)
        roof = np.append(roof, ceils)
        floor = np.append(floor, ground)
    roof = list(set(roof).difference(set(floor)))
    floor = list(floor)
    others = list(model.wallList)+list(model.glazingList)+list(model.skylightList)
    # roof = [model.geoId.index(item) for item in roof]
    # floor = [model.geoId.index(item) for item in floor]
    # others = [model.geoId.index(item) for item in others]
    # roof = np.array(model.geometryList)[roof]
    # floor = np.array(model.geometryList)[floor]
    # others = np.array(model.geometryList)[others]

    geoStr = _generateRadGeo(roof, floor, others)
    radStr = _getSky(date, skyType, lat, lon, diff) + _materialLib() + geoStr
    with open(radPath, 'w+') as f:
        f.write(radStr)
    return radStr

def triOpaque(moFace:MoosasElement)->list[pygeos.Geometry]:
    proj = Projection(origin=np.mean(pygeos.get_coordinates(moFace.face, include_z=True), axis=0), unitZ=moFace.normal)
    baseFace = mixItemListToList(moFace.face)
    baseBrep,holes=[],[]
    for face in baseFace:
        baseBrep.append(pygeos.get_exterior_ring(face))
        if len(pygeos.get_rings(face))>1:
            holes+=list(pygeos.get_rings(face))[1:]
    for gls in moFace.glazingElement:
        holes.append(gls.representation())
    baseBrep = [proj.toUV(face) for face in baseBrep]
    baseBrep = pygeos.union_all(baseBrep)
    holes = [proj.toUV(face) for face in holes]
    for h in holes:
        baseBrep = pygeos.difference(baseBrep,h)
    baseBrep = pygeos.delaunay_triangles(baseBrep)
    baseBrep = [proj.toWorld(tri) for tri in pygeos.get_parts(baseBrep)]
    return baseBrep
def spaceToRad(space: MoosasSpace, date: datetime, skyType, lat, lon, diff=10000,
               radPath=rf"{path.libDir}\rad\model.rad"):
    roof, floor, others = [], [], []
    faces = space.getAllFaces(to_dict=True)
    for moface in faces["MoosasCeiling"]:
        roof = np.append(roof, moface)
    for moface in faces["MoosasFloor"]:
        floor = np.append(floor, moface)
    for moface in faces["MoosasWall"]:
        others = np.append(others, moface)
    for moface in faces["MoosasGlazing"]:
        others = np.append(others, moface)
    for moface in faces["MoosasSkylight"]:
        others = np.append(others, moface)

    geoStr = _generateRadGeo(roof, floor, others)

    radStr = _getSky(date, skyType, lat, lon, diff) + _materialLib() + geoStr
    with open(radPath, 'w+') as f:
        f.write(radStr)
    return radStr


def writeGrid(element: MoosasElement, gridPath=rf"{path.libDir}\rad\grid.input", normal=None, append=True):
    if append:
        mode = 'a+'
    else:
        mode = 'w+'
    gridStr = []
    grid = MoosasGrid(element)
    for pts in grid.gridPoints:
        pts = pygeos.get_coordinates(pts, include_z=True).astype(str)[0]
        nor = grid.normal.astype(str) if normal is None else Vector(normal).array.astype(str)

        gridStr += [" ".join(pts) + " " + " ".join(nor)]

    with open(gridPath, mode) as f:
        f.write('\n'.join(gridStr) + "\n")

    return gridStr
