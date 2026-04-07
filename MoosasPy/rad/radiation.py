from __future__ import annotations

from ..IO import writeGeo
from ..geometry import MoosasGrid
from ..geometry.element import MoosasSpace, MoosasSkylight, MoosasGlazing, MoosasElement
from ..geometry.geos import Ray, Vector
from ..utils import np, os, Iterable
from ..utils import path, callCmd, generate_code
from ..utils.constant import rad
from ..weather import MoosasCumSky


def modelRadiation(model, reflection=1):
    """
    Calculate radiation for each space in the model using a fast single-call method via MoosasRad.exe.
    
    Parameters
    ----------
    model : object
        The building model containing spaces, geometry, and sky data. Must have `spaceList`, 
        `cumSky['summerCumSky']`, `cumSky['winterCumSky']`, and settings attributes.
    reflection : int, optional
        The number of reflections to consider in the radiation calculation. Default is 1.
    
    Returns
    -------
    object
        The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad'
        values representing the total solar radiation for summer and winter periods.
    """
    model.x = 1000
    """
         This method is faster than spaceRadiation since it only call MoosasRad.exe once.
         Radiation Calculation in MoosasRad is parallel.
    """
    """construct rays"""
    rays, windowArea, spaceIdx = [], [], []
    geo_path = writeRadGeo(model)
    for i, space in enumerate(model.spaceList):
        moFaces = space.getAllFaces(to_dict=False)
        for moGeometry in moFaces:
            if isinstance(moGeometry, MoosasSkylight) or isinstance(moGeometry, MoosasGlazing):
                rays.append(Ray(
                    origin=Vector(moGeometry.getWeightCenter()),
                    direction=Vector(moGeometry.normal)
                ))
                windowArea.append(moGeometry.area3d())
                spaceIdx.append(i)

    rays = np.array(rays)
    windowArea = np.array(windowArea)
    spaceIdx = np.array(spaceIdx)

    """radiation calculation"""
    summerRad = positionRadiation(
        positionRay=rays,
        sky=model.cumSky['summerCumSky'],
        geo_path=geo_path,
        reflection=reflection
    )
    winterRad = positionRadiation(
        positionRay=rays,
        sky=model.cumSky['winterCumSky'],
        geo_path=geo_path,
        reflection=reflection
    )

    """sum up space radiation"""
    for i, space in enumerate(model.spaceList):
        subList = [idx for idx in range(len(spaceIdx)) if spaceIdx[idx] == i]
        space.settings['zone_summerrad'] = np.sum(
            rad.DEFAULT_SHGC * windowArea[subList] * summerRad[subList])
        space.settings['zone_winterrad'] = np.sum(
            rad.DEFAULT_SHGC * windowArea[subList] * winterRad[subList])

    return model


def spaceRadiation(space: MoosasSpace, reflection=1) -> dict:
    """
    Calculate seasonal radiation for a space by aggregating aperture-level radiation contributions.
    
    Parameters
    ----------
    space : MoosasSpace
        The space object containing apertures (skylights or glazing) for which radiation is calculated.
    reflection : float, optional
        Reflection coefficient used in radiation calculation. Default is 1.
    
    Returns
    -------
    dict
        Updated settings dictionary of the space with 'zone_summerrad' and 'zone_winterrad' keys 
        representing total summer and winter radiation values weighted by window areas.
    """
    """
        This method packing up the ray of all apertures of the space and call MoosasRad.exe once.
        Radiation Calculation in MoosasRad is parallel.
    """
    settings = space.settings
    model = space.parent
    geo_path = writeRadGeo(model)
    if 'cumSky' not in model.__dir__():
        model.loadCumSky()
    moFaces = space.getAllFaces(to_dict=False)
    rays = []
    windowArea = []
    for moGeometry in moFaces:
        if isinstance(moGeometry, MoosasSkylight) or isinstance(moGeometry, MoosasGlazing):
            rays.append(Ray(
                origin=Vector(moGeometry.getWeightCenter()),
                direction=Vector(moGeometry.normal)
            ))
            windowArea.append(moGeometry.area3d())
    windowArea = np.array(windowArea)
    settings['zone_summerrad'] = np.sum(windowArea * positionRadiation(
        positionRay=rays,
        sky=model.cumSky['summerCumSky'],
        geo_path=geo_path,
        reflection=reflection
    ))

    settings['zone_winterrad'] = np.sum(windowArea * positionRadiation(
        positionRay=rays,
        sky=model.cumSky['winterCumSky'],
        geo_path=geo_path,
        reflection=reflection
    ))

    return settings


def faceRadiation(face: MoosasElement, gridSize=None, gridOffset=0.78, sky: MoosasCumSky = None, reflection=1,
                  geo_path=None) -> np.ndarray:
    """
    Calculate the sky visibility for each patch in the sky model, for a gridded face.
    the return result would be the average sky visibility, not for a position but the whole grid.

    Parameters
    ----------
    face : object
        The face to be calculated.
    sky : MoosasCumSky
        The position will be replaced if a sky is given,
        and the radiation value will be multiplied by the visibility.
    gridSize : float
        The calculation grid size in meters. (default 1.0)
    gridOffset : float
        The grid offset in meters. (default 0.2)
    reflection : float
        How many reflection in the ray test calculation. (default 0)
    geo_path : str
        The path of the geometric model.
    Returns
    -------
    np.ndarry
        A numpy array containing average sky patches visibility (len=145).
    """
    grid: MoosasGrid = MoosasGrid(face, gridSize, gridOffset)
    model = face.parent
    if sky is None:
        position = MoosasCumSky.defaultPosition()
    else:
        position = sky.position
    rays = []
    fixMatrix = []
    allCells = [c for row in grid.gridCell for c in row]
    for c in allCells:
        thisRays = [Ray(c.origin, pos,value=1.0) for pos in position]
        rays += thisRays
        fixMatrix.append(np.array([abs(Vector.dot(c.direction, r.direction)) for r in thisRays]))

    unHit = np.arange(len(rays))
    rays = np.array(rays)
    if geo_path is None:
        geo_path = writeRadGeo(model)

    while reflection >= 0 and len(rays[unHit]) > 0:
        newRays = rayTest(rays[unHit], geo_path=geo_path)
        if len(newRays) != len(unHit):
            raise Exception('Ray test error: input and output dont have the same len')
        unHitNext = []
        for i, thisRay in enumerate(newRays):
            if thisRay is not None:
                rays[unHit[i]] = thisRay
                rays[unHit[i]].value *= rad.CONTENT_REFLECTION
                unHitNext.append(unHit[i])
        unHit = unHitNext
        if len(rays[unHit]) == 0:
            break
        reflection -= 1

    rays = np.array([ra.value for ra in rays])
    rays = rays.reshape(len(allCells), int(len(rays) / len(allCells)))
    if sky is None:
        rays = [cell * fixMatrix[i] for i, cell in enumerate(rays)]
    else:
        rays = [cell * sky.value * fixMatrix[i] for i, cell in enumerate(rays)]
    return np.mean(rays, axis=0)


def positionRadiation(positionRay: Ray | Iterable[Ray], sky: MoosasCumSky,
                      model=None, reflection=1, geo_path=None) -> Iterable[float]:
    """
        Cumulative radiation for positions with factors.
        The position are defined as Ray class with origins and directions.
        list or ndarry or Ray can be given as positionRay.
        The return value is unit in kWh/m2
        Model or geoPath should be provided.

        Parameters
        -------------------------------------

        positionRay: Iterable[Ray] position(origin, factor) to test. Put as much as possible in one coll on this func.
        sky: MoosasCumSky cumulative sky model we use in this func.
        model: MoosasModel the reflectance test content.
        reflection: how many reflection will be calculated. default 1
        geoPath: optional *.geo file input for the test content.

        Returns
        -------
        Iterable[float]
            The return value is unit in kWh/m2
    """
    if isinstance(positionRay, Ray):
        positionRay = np.array([positionRay])
    elif isinstance(positionRay, list):
        positionRay = np.array(positionRay)
    elif not isinstance(positionRay, np.ndarray):
        raise Exception(f'Wrong type of positionRay, except {list} or {np.ndarray} or {Ray} got {type(positionRay)}')
    if len(positionRay) == 0:
        return np.array([])
    if geo_path is None:
        if model is None:
            raise Exception('Geo export error: empty model.')
        geo_path = writeRadGeo(model)

    rays = []
    for pointRay in positionRay:
        # project the direct sun radiation to the pointRay direction
        thisRays = [Ray(pointRay.origin, pos, value=val) for pos, val in
                    zip(sky.position, sky.value)]
        # Add ground reflection to the rays
        nagativeRays = [ra.reverse() for ra in thisRays]
        for ra in nagativeRays:
            ra.value *= rad.GROUND_REFLECTION
        thisRays += nagativeRays
        for r in thisRays:
            r.value *= max(Vector.dot(r.direction, pointRay.direction), 0)
        rays += thisRays
    # whether the ray hit anything
    unHit = np.arange(len(rays))
    rays = np.array(rays)
    while reflection >= 0 and len(rays[unHit]) > 0:
        newRays = rayTest(rays[unHit], geo_path=geo_path)
        if len(newRays) != len(unHit):
            raise Exception('Ray test error: input and output dont have the same len')
        unHitNext = []
        for i, thisRay in enumerate(newRays):
            if thisRay is not None:
                rays[unHit[i]] = thisRay
                rays[unHit[i]].value *= rad.CONTENT_REFLECTION
                unHitNext.append(unHit[i])
        unHit = unHitNext
        if len(rays[unHit]) == 0:
            break
        reflection -= 1

    rays = np.array([ra.value for ra in rays])
    rays = rays.reshape(len(positionRay), int(len(rays) / len(positionRay)))
    return np.sum(rays, axis=1)


def rayTest(rays: Iterable[Ray], model=None, geo_path: str = None,
            ray_path: str = None) -> list[Ray | None]:
    """
        call MoosasRad.exe to test the ray face intersection and reflection.
        if the ray hit a face: result ray will be the reflection ray of the input ray.
        if the ray doesnt hit a face: result==None.
        Model or geoPath should be provided.

        -------------------------------------

        rays: Iterable[Ray] ray to test. Put as much as possible rays in one coll on this func.
        model: MoosasModel the reflectance test content.
        geoPath: optional *.geo file input for the test content.
        ray_path: option temp path for the ray file.

        returns: Iterable[Ray | None]
        if the intersection is valid, the reflection of the ray will be return.
        If not, None will be add.
    """
    # export geometry file or use exist file directly
    prj = 'ray_' + generate_code(4)
    if geo_path is None:
        if model is None:
            raise Exception('empty model')
        geo_path = writeRadGeo(model)
    if ray_path is None:
        ray_path = os.path.abspath(os.path.join(path.tempDir, prj + '.i'))
    result_path = os.path.abspath(os.path.join(path.tempDir, prj + '.o'))

    # export ray file
    lines = ''
    for ra in rays:
        if not isinstance(ra, Ray):
            raise Exception(f'expect{Vector},got{type(ra)}')
        lines += ra.dump() + '\n'

    path.checkBuildDir(ray_path, result_path)
    with open(ray_path, 'w') as f:
        f.write(lines)

    # call MoosasRad.exe
    command = [
        os.path.join(path.libDir, r'rad\MoosasRad.exe'),
        '-g', geo_path,
        '-o', result_path,
        ray_path
    ]
    callCmd(command)

    # read the result ray from the file
    result = []
    with open(result_path, 'r') as f:
        result = f.read().split('\n')
    reflectionRay = []
    for res in result:
        if len(res) > 6:
            res = np.array(res.split(',')).astype(float)
            res = Ray(Vector(res[:3]), Vector(res[3:]))
            if Vector.equal(res.origin, Vector(np.array([-1, -1, -1]))):
                res = None
            reflectionRay.append(res)
    return reflectionRay


def writeRadGeo(model):
    """
    Write a geometry file for the given model towards MoosasRayTest.exe.
    
    Parameters
    ----------
    model : object
        The geometric model to be written to the .geo file. The exact type depends on the expected input of `writeGeo`, typically representing a 3D scene or geometry structure.
    
    Returns
    -------
    str
        The absolute file path to the generated .geo file.
    """
    prj = 'ray_' + generate_code(4)
    geo_path = os.path.abspath(os.path.join(path.tempDir, prj + '.geo'))
    writeGeo(geo_path, model)
    # with open(geoPath,'a') as f:
    #    f.write(
    #        '''
    #        Face1 99999
    #        Normal
    #        0 0 1
    #        Vertices
    #        -99999.0 -99999.0 0.0
    #        -99999.0 99999.0 0.0
    #        99999.0 99999.0 0.0
    #        99999.0 -99999.0 0.0
    #
    #        '''
    #    )
    return geo_path
