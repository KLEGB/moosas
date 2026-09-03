from .radiance import _meshToRadObject, _materialLib, _getSky
from ...model import MoosasModel
from ...transform.geometry.element import MoosasElement, MoosasSpace
from ...transform.geometry.geos import Projection, Vector
from ...transform.geometry.grid import MoosasGrid
from ...utils import np, shapely, path, os,mixItemListToList
from datetime import datetime
import warnings


def simModel(
    model: MoosasModel,
    date: datetime,
    skyType,
    location,
    diff=15000,
    radPath=None,
    gridPath=None,
    *,
    work_dir=None,
    timeout_seconds: float = 300.0,
    engine=None,
):
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
        location : Location
            Geographic metadata read from an EPW file.
        diff : float , optional
            diffuse illuminance for the cloudy sky (Default : 15000)
        work_dir : str or pathlib.Path, optional
            Parent directory for the per-run temporary work directory.
        timeout_seconds : float, optional
            Maximum runtime for each Radiance executable.

        Returns
        -------
        dict
            the daylighting simulation result on the floor:
            [{df:daylight factor, satisfied: satification}...{}]

    """
    if radPath is not None or gridPath is not None:
        warnings.warn(
            "radPath and gridPath are ignored. RadianceRunner uses an isolated temporary work directory.",
            DeprecationWarning,
            stacklevel=2,
        )

    from .runner import RadianceRunner, RadianceSky

    result = RadianceRunner(
        model=model,
        sky=RadianceSky(date, skyType, location, diff),
        work_dir=work_dir,
        timeout_seconds=timeout_seconds,
        engine=engine,
    ).run()
    return result.as_legacy()


def _generateRadGeo(roof, floor, others):
    """
    Generate a Radiance geometry string from roof, floor, and other building elements.
    
    Parameters
    ----------
    roof : list of MeshFace
        List of mesh faces representing the roof elements.
    floor : list of MeshFace
        List of mesh faces representing the floor elements.
    others : list of MeshFace
        List of mesh faces representing other elements (e.g., walls, glazing).
        The category attribute of each face determines its treatment:
        category 0 for walls, category 1 for glazing.
    
    Returns
    -------
    str
        A string containing the Radiance-formatted geometry representation.
    """
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
    """
    Convert a MoosasModel to a Radiance input file (.rad) string and write it to disk.
    
    Parameters
    ----------
    model : MoosasModel
        The building model containing spaces, walls, glazing, and other geometry.
    date : datetime
        The date and time for which the sky conditions are generated.
    skyType : object
        Specifies the type of sky (e.g., sunny, cloudy) for Radiance sky generation.
    lat : float or int
        Latitude of the site in degrees, used for solar position calculation.
    lon : float or int
        Longitude of the site in degrees, used for solar position calculation.
    diff : int, optional
        Diffuse solar irradiance value (in W/m虏). Default is 10000.
    radPath : str, optional
        File path where the generated .rad file will be saved. Default is a path within `path.libDir`.
    
    Returns
    -------
    str
        The complete Radiance input string containing sky, materials, and geometry definitions.
    """
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

def triOpaque(moFace:MoosasElement)->list[shapely.Geometry]:
    """
    Compute triangulated opaque geometry from a MoosasElement face.
    
    Parameters
    ----------
    moFace : MoosasElement
        The input MoosasElement containing the face and glazing elements. The face is used to generate base geometry,
        and its normal is used for projection. Glazing elements are treated as holes in the base face.
    
    Returns
    -------
    list[shapely.Geometry]
        A list of shapely Geometry objects representing the triangulated opaque regions in world coordinates,
        with glazing areas subtracted as holes and projected back from UV to 3D space.
    """
    proj = Projection(origin=np.mean(shapely.get_coordinates(moFace.face, include_z=True), axis=0), unitZ=moFace.normal)
    baseFace = mixItemListToList(moFace.face)
    baseBrep,holes=[],[]
    for face in baseFace:
        baseBrep.append(shapely.get_exterior_ring(face))
        if len(shapely.get_rings(face))>1:
            holes+=list(shapely.get_rings(face))[1:]
    for gls in moFace.glazingElement:
        holes.append(gls.representation())
    baseBrep = [proj.toUV(face) for face in baseBrep]
    baseBrep = shapely.union_all(baseBrep)
    holes = [proj.toUV(face) for face in holes]
    for h in holes:
        baseBrep = shapely.difference(baseBrep,h)
    baseBrep = shapely.delaunay_triangles(baseBrep)
    baseBrep = [proj.toWorld(tri) for tri in shapely.get_parts(baseBrep)]
    return baseBrep
def spaceToRad(space: MoosasSpace, date: datetime, skyType, lat, lon, diff=10000,
               radPath=rf"{path.libDir}\rad\model.rad"):
    """
    Generate a Radiance input file string and write it to disk based on the provided space geometry and environmental conditions.
    
    Parameters
    ----------
    space : MoosasSpace
        The space object containing the 3D geometry, from which faces are extracted.
    date : datetime
        The date and time for which the sky conditions are computed.
    skyType : object
        Specifies the type of sky model to use (e.g., sunny, cloudy); passed to `_getSky`.
    lat : float or int
        Latitude of the location, used in sky calculation.
    lon : float or int
        Longitude of the location, used in sky calculation.
    diff : int, optional
        Diffuse solar radiation value (in Wh/m虏), default is 10000.
    radPath : str, optional
        File path where the Radiance script will be saved. Defaults to a path in `path.libDir`.
    
    Returns
    -------
    str
        The complete Radiance input string, including sky, materials, and geometry definitions.
    """
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
    """
    Write grid points and their normal vectors to a file.
    
    Parameters
    ----------
    element : MoosasElement
        The element used to generate the grid.
    gridPath : str, optional
        Path to the output file where grid data will be written. Default is constructed using `path.libDir`.
    normal : array-like or Vector, optional
        Normal vector to be written with each point; if None, uses the grid's default normal. Default is None.
    append : bool, optional
        If True, appends to the file; otherwise, overwrites it. Default is True.
    
    Returns
    -------
    list of str
        List of formatted strings representing grid points and normals written to the file.
    """
    if append:
        mode = 'a+'
    else:
        mode = 'w+'
    gridStr = []
    grid = MoosasGrid(element)
    for pts in grid.gridPoints:
        pts = shapely.get_coordinates(pts, include_z=True).astype(str)[0]
        nor = grid.normal.astype(str) if normal is None else Vector(normal).array.astype(str)

        gridStr += [" ".join(pts) + " " + " ".join(nor)]

    with open(gridPath, mode) as f:
        f.write('\n'.join(gridStr) + "\n")

    return gridStr
