from __future__ import annotations

from ..models import MoosasModel, MoosasCumSky, MoosasElement
from ..rad import faceRadiation,writeRadGeo
from ..utils import np, os, path


def roofAnnualGeneration(model: MoosasModel,usefulArea=0.7,efficiency=0.17, stationid="545110",
                         gridSize=1.0, gridOffset=0.2, reflection=0) -> np.ndarray:
    """
    Calculate the hourly total roof radiation gain for a given model and station ID.

    Parameters
    ----------
    model : object
        The geometric model to be written to the .geo file. The exact type depends on the expected input of `writeGeo`, typically representing a 3D scene or geometry structure.
    usefulArea: float
        Valid area for the BAPV installation. (default 0.7)
    efficiency: float
        Efficiency for the PV panel. (default 0.17)
    stationid : string
        The station ID. Should be appeared in the /db/cumsky folder.
    gridSize : float
        The calculation grid size in meters. (default 1.0)
    gridOffset : float
        The grid offset in meters. (default 0.2)
    reflection : float
        How many reflection in the ray test calculation. (default 0)
    Returns
    -------
        analysis_results with an array containing the hourly result (len=8760).
    """
    mElements = model.getAllFaces(True)
    roofFaces = []
    for mElement in mElements['MoosasFace']:
        if mElement.isOuter:
            if list(model.levelList).index(mElement.level) != 0:
                roofFaces.append(mElement)
    geo_path = writeRadGeo(model)
    return usefulArea * efficiency * faceAnnualRad(roofFaces,stationid,gridSize,gridOffset,reflection,geo_path)

def facadeAnnualGeneration(model: MoosasModel, usefulArea=0.4,efficiency=0.17,stationid="545110",
                           gridSize=None, gridOffset=0.2,reflection=0) -> np.ndarray:
    """
    Calculate the hourly total facade radiation gain for a given model and station ID.

    Parameters
    ----------
    model : object
        The geometric model to be written to the .geo file. The exact type depends on the expected input of `writeGeo`, typically representing a 3D scene or geometry structure.
    usefulArea: float
        Valid area for the BAPV installation. (default 0.4)
    efficiency: float
        Efficiency for the PV panel. (default 0.17)
    stationid : string
        The station ID. Should be appeared in the /db/cumsky folder.
    gridSize : float
        The calculation grid size in meters. (default 1.0)
    gridOffset : float
        The grid offset in meters. (default 0.2)
    reflection : float
        How many reflection in the ray test calculation. (default 0)
    Returns
    -------
    np.ndarry
        A numpy array containing the hourly result (len=8760).
    """
    mElements = model.getAllFaces(True)
    roofFaces = []
    for mElement in mElements['MoosasWall']:
        if mElement.isOuter:
            if list(model.levelList).index(mElement.level) != 0:
                roofFaces.append(mElement)
    geo_path = writeRadGeo(model)
    return usefulArea * efficiency * faceAnnualRad(roofFaces,stationid,gridSize,gridOffset,reflection,geo_path)

def faceAnnualRad(faces: MoosasElement | list[MoosasElement], stationid="545110", gridSize=None, gridOffset=0.2,
                  reflection=0, geo_path=None) -> np.ndarray:
    """
    Calculate the hourly total radiation gain for face(s), and stationid.

    Parameters
    ----------
    faces : object
        The face(s) to be calculated.
    stationid : string
        The station ID. Should be appeared in the /db/cumsky folder.
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
        A numpy array containing the hourly result (len=8760).
    """
    # matrix in kWh/m2
    if isinstance(faces, MoosasElement):
        faces = [faces]
    avgSkyValid = []

    for face in faces:
        avgSkyValid.append(faceRadiation(face, gridSize, gridOffset, None, reflection, geo_path))

    with open(os.path.join(path.dataBaseDir, 'cum_sky', f'cumsky_{stationid}.csv')) as f:
        cumValue = np.array([line.split(',') for line in f.read().split('\n') if len(line) > 1]).astype(float)
        generationSeries = []
        for face,avgRad in zip(faces,avgSkyValid):
            area = face.area
            generationSeries.append([area * np.sum(avgRad * cumValue[:, i]) / MoosasCumSky.FIX_RADIATION for i in range(8760)])

        return np.sum(generationSeries,axis=0)

