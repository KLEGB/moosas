from __future__ import annotations
from datetime import datetime

from .calculation import ray_test, write_radiation_geometry
from ...transform.geometry.geos import Vector, Ray
from ...utils.date import DateTime
from ...utils import np,Iterable
from ...model import MoosasModel


def calculate_position_sun_hours(position_ray: Ray | Iterable[Ray], sky,
                                 model: MoosasModel = None, geo_path=None,
                                 period_start: datetime | DateTime = DateTime(1, 1, 0),
                                 period_end: datetime | DateTime = DateTime(12, 31, 23),
                                 leap_year: bool = False)->Iterable[float]:
    """
    Direct sun hour calculation for given positions considering shadows and orientation.
    
    Parameters
    ----------
    positionRay : Ray or Iterable[Ray]
        Position(s) defined as Ray objects with origin and direction. Each Ray may include a weighting factor.
        Can be a single Ray or an iterable of Rays.
    sky : object
        Direct-sun sky object providing ``annual_sun(leap_year=...)``.
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
        sky: direct sun sky model used in this function.
        model: optional MoosasModel the reflectance test content.
        geoPath: optional *.geo file input for the test content.
        periodStart: datetime | DateTime optional start time in for analysis
        periodEnd: datetime | DateTime optional end time in for analysis
        leapYear: optional bool to analysis a leap year

        returns: Iterable[float]
        The return value is unit in hour/day
    """
    if sky is None:
        raise Exception('Sky not found')
    if geo_path is None:
        if model is None:
            raise Exception('Geo export error: empty model.')
        geo_path = write_radiation_geometry(model)

    if isinstance(position_ray, Ray):
        position_ray = [position_ray]

    if isinstance(period_start, datetime):
        period_start = DateTime(period_start)
    if isinstance(period_end, datetime):
        period_end = DateTime(period_end)

    sunPositions = sky.annual_sun(leap_year=leap_year)
    if int(period_start.hoy) < int(period_end.hoy):
        sunPositions = sunPositions[int(period_start.hoy):int(period_end.hoy)]
        totalDays = 0 - int(period_start.doy) + int(period_end.doy)
    else:
        sunPositions = sunPositions[int(period_start.hoy):] + sunPositions[:int(period_end.hoy)]
        totalDays = 365 - int(period_start.doy) + int(period_end.doy)
        if leap_year:
            totalDays += 1

    sunPositions = [sunvect for sunvect in sunPositions if sunvect.z >= 0]
    rayIdx, sunRay = [], []
    for position in position_ray:
        validSunRay = [Ray(position.origin, sunvect) for sunvect in sunPositions if
                       Vector.dot(sunvect, position.direction) > 0]

        rayIdx.append([len(sunRay), len(sunRay) + len(validSunRay)])
        sunRay += validSunRay

    refRay = np.array(ray_test(sunRay, geo_path= geo_path))
    if len(refRay) != len(sunRay):
        raise Exception(f'Error occurred in ray test: expect len of rays {len(sunRay)} but got {len(refRay)}')

    resultHour = []
    for rayArraySE in rayIdx:
        resultHour.append(len([ref for ref in refRay[rayArraySE[0]:rayArraySE[1]] if ref is not None]))

    return np.array(resultHour).astype(float) / totalDays
