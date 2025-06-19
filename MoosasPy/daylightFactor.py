"""space daylight factor calculation"""""

from .geometry.element import MoosasSpace
from .geometry.grid import MoosasGrid
from .utils import np, generate_code
from .IO import writeGeo
def spaceDaylightFactor_quick(space:MoosasSpace,light_transmittance = 0.6)->float:
    """
        a very simple model to predict the daylight factor of a space

        Parameters
        ----------
        space : MoosasSpace
            the space
        light_transmittance : float
            the light transmittance of the glazing

        Returns
        -------
        float
            the daylight factor
    """
    window_area = np.sum([w.area*w.wwr for w in space.edge.wall if w.isOuter])
    df = 45 * window_area * light_transmittance / space.area / 0.76
    df = 100 if df >100 else df
    return df

def spaceDaylightFactor(space:MoosasSpace,light_transmittance = 0.6)->float:
    """
        grid based method to calculate the daylight factor of a space

        Parameters
        ----------
        space : MoosasSpace
            the space
        light_transmittance : float
            the light transmittance of the glazing

        Returns
        -------
        float
            the daylight factor
    """
    grids = [MoosasGrid(space.parent,f.firstFaceId,gird_size=np.sqrt(space.area)/3) for f in space.floor.face]
    spaceFaces = space.getAllFaces(to_dict=True)
    aperture = spaceFaces['MoosasGlazing'] + spaceFaces['MoosasSkylight']
    geoFile = generate_code(4)+'.geo'
    writeGeo(geoFile,space.parent,[a.firstFaceId for a in aperture])





