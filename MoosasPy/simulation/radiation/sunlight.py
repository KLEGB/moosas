from __future__ import annotations
from datetime import datetime

from .radiation import rayTest, writeRadGeo
from ..weather.directsky import MoosasDirectSky
from ...transformation.geometry.geos import Vector, Ray
from ...utils.date import DateTime
from ...utils import np,Iterable
from ..weather.dest import Location
from ...models import MoosasModel


def positionSunHour(positionRay: Ray | Iterable[Ray], location: Location = None, sky: MoosasDirectSky = None,
                    model: MoosasModel = None, geo_path=None,
                    periodStart: datetime | DateTime = DateTime(1, 1, 0),
                    periodEnd: datetime | DateTime = DateTime(12, 31, 23),
                    leapYear: bool = False)->Iterable[float]:
    """
    Direct sun hour calculation for given positions considering shadows and orientation.
    
    Parameters
    ----------
    positionRay : Ray or Iterable[Ray]
        Position(s) defined as Ray objects with origin and direction. Each Ray may include a weighting factor.
        Can be a single Ray or an iterable of Rays.
    location : Location, optional
        Location object containing latitude and longitude. Used to create the MoosasDirectSky if sky is not provided.
        If both location and sky are None, an exception is raised.
    sky : MoosasDirectSky, optional
        Predefined direct sun sky model. If not provided, a new MoosasDirectSky is created from the location.
    model : MoosasModel, optional
        Model containing geometry for reflectance and shadow testing. Required if geo_path is not provided.
    geo_path : str, optional
        Path to a *.geo file representing the scene geometry for ray tracing. If not provided, generated from model.
    periodStart : datetime or DateTime, default=DateTime(1, 1, 0)
        Start time of the analysis period. Defaults to beginning of the year.
    periodEnd : datetime or DateTime, default=DateTime(12, 31, 23)
        End time of the analysis period. Defaults to end of the year.
    leapYear : bool, default=False
        Whether to consider a leap year in the sky matrix generation and day count.
    
    Returns
    -------
    Iterable[float]
        Average daily sun hours for each position, in units of hours per day.
        The result accounts for shading, orientation, and valid sun exposure during the specified period.
    """
    """
        Direct sun hour for positions with factors.
        The position are defined as Ray class with origins and directions.
        list or ndarry or Ray can be given as positionRay.
        The return value is unit in average hour/day
        Model or geoPath should be provided.

        -------------------------------------

        positionRay: Iterable[Ray] position(origin, factor) to test. Put as much as possible in one coll on this func.
        location: Location the location object define in weather, which is used to create MoosasDirectSky
        sky: optional MoosasDirectSky direct sun sky model we use in this func.
        model: optional MoosasModel the reflectance test content.
        geoPath: optional *.geo file input for the test content.
        periodStart: datetime | DateTime optional start time in for analysis
        periodEnd: datetime | DateTime optional end time in for analysis
        leapYear: optional bool to analysis a leap year

        returns: Iterable[float]
        The return value is unit in hour/day
    """
    if location is not None:
        sky = MoosasDirectSky(location.latitude, location.longitude)
    if sky is None:
        raise Exception('Sky not found')
    if geo_path is None:
        if model is None:
            raise Exception('Geo export error: empty model.')
        geo_path = writeRadGeo(model)

    if isinstance(positionRay, Ray):
        positionRay = [positionRay]

    if isinstance(periodStart, datetime):
        periodStart = DateTime(periodStart)
    if isinstance(periodEnd, datetime):
        periodEnd = DateTime(periodEnd)

    sunPositions = sky.annualSun(leapYear=leapYear)
    if int(periodStart.hoy) < int(periodEnd.hoy):
        sunPositions = sunPositions[int(periodStart.hoy):int(periodEnd.hoy)]
        totalDays = 0 - int(periodStart.doy) + int(periodEnd.doy)
    else:
        sunPositions = sunPositions[int(periodStart.hoy):] + sunPositions[:int(periodEnd.hoy)]
        totalDays = 365 - int(periodStart.doy) + int(periodEnd.doy)
        if leapYear:
            totalDays += 1

    sunPositions = [sunvect for sunvect in sunPositions if sunvect.z >= 0]
    rayIdx, sunRay = [], []
    for position in positionRay:
        validSunRay = [Ray(position.origin, sunvect) for sunvect in sunPositions if
                       Vector.dot(sunvect, position.direction) > 0]

        rayIdx.append([len(sunRay), len(sunRay) + len(validSunRay)])
        sunRay += validSunRay

    refRay = np.array(rayTest(sunRay, geo_path= geo_path))
    if len(refRay) != len(sunRay):
        raise Exception(f'Error occurred in ray test: expect len of rays {len(sunRay)} but got {len(refRay)}')

    resultHour = []
    for rayArraySE in rayIdx:
        resultHour.append(len([ref for ref in refRay[rayArraySE[0]:rayArraySE[1]] if ref is not None]))

    return np.array(resultHour).astype(float) / totalDays
