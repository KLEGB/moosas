from __future__ import annotations

import os
import numpy as np
from ...transform.geometry.geos import Vector
from ...utils.tools import path
from ...utils.date import DateTime
from ...utils import Iterable


class MoosasCumSky(object):
    __slots__ = ['_position', 'value']
    ANNUAL_HOY = 8760
    FIX_RADIATION = 1000
    SUMMER_START_HOY = 3624
    SUMMER_END_HOY = 5832
    WINTER_START_HOY = 8016
    WINTER_END_HOY = 1416

    def __init__(self, cumValue=None,position=None):
        """
        Initialize the object with cumulative value and load sun position data.
        
        Parameters
        ----------
        cumValue : optional
            Initial cumulative value to assign to the instance. Default is None.
        
        Returns
        -------
        None
        """
        self.value = cumValue
        self._position = position

    @property
    def position(self):
        if self._position is None:
            with open(os.path.join(path.libDir, r'weather','sun_position.csv')) as f:
                self._position = [Vector(np.array(line.split(',')).astype(float)) for line in f.read().split('\n')]
        return self._position

    @staticmethod
    def defaultPosition():
        with open(os.path.join(path.libDir, r'weather', 'sun_position.csv')) as f:
            position = [Vector(np.array(line.split(',')).astype(float)) for line in f.read().split('\n')]
            return position

    @classmethod
    def fromPeriod(cls, cumValue, stDateTime: DateTime | int, edDateTime: DateTime | int):
        """
        Create an instance from a cumulative value array over a specified time period.
        
        Parameters
        ----------
        cumValue : numpy.ndarray
            Array of cumulative values, typically radiation data, with shape (n, m) where n is the number of samples.
        stDateTime : DateTime or int
            Start time of the period. If DateTime, converted to hour of year (hoy); if int, assumed to be hour of year.
        edDateTime : DateTime or int
            End time of the period. If DateTime, converted to hour of year (hoy); if int, assumed to be hour of year.
        
        Returns
        -------
        cls
            A new instance of the class initialized with the normalized cumulative value over the specified period.
        """
        if isinstance(stDateTime, DateTime):
            stDateTime = stDateTime.hoy
        if isinstance(edDateTime, DateTime):
            edDateTime = edDateTime.hoy
        if stDateTime < edDateTime:
            cumValue = np.sum(cumValue[:, stDateTime:edDateTime], axis=1) / MoosasCumSky.FIX_RADIATION
        else:
            cumValue = (np.sum(cumValue[:, stDateTime:], axis=1) + np.sum(cumValue[:, :edDateTime],
                                                                          axis=1)) / MoosasCumSky.FIX_RADIATION
        return cls(cumValue)


def loadCumSky(stationid: str,
               stDateTime: DateTime | int | Iterable[DateTime] | Iterable[int] = None,
               edDateTime: DateTime | int | Iterable[DateTime] | Iterable[int] = None) -> MoosasCumSky | list[
    MoosasCumSky]:
    """
    Load cumulative sky data for a given station over specified time periods.
    
    Parameters
    ----------
    stationid : str
        The identifier for the weather station whose cumulative sky data is to be loaded.
    stDateTime : DateTime or int or Iterable[DateTime] or Iterable[int], optional
        Start time(s) for the period(s) of interest. Can be a single DateTime/int or an iterable of DateTimes/ints.
        If int, it is interpreted as an hour index (0-8759). Default is None.
    edDateTime : DateTime or int or Iterable[DateTime] or Iterable[int], optional
        End time(s) for the period(s) of interest. Must match the type and length of stDateTime.
        If int, it is interpreted as an hour index (1-8760). Default is None.
    
    Returns
    -------
    MoosasCumSky or list[MoosasCumSky]
        A single MoosasCumSky object if one period is requested, otherwise a list of MoosasCumSky objects,
        each representing cumulative sky data for the corresponding time period.
    """
    m_cumSky = []
    with open(os.path.join(path.dataBaseDir, 'cum_sky', f'cumsky_{stationid}.csv')) as f:
        cumValue = np.array([line.split(',') for line in f.read().split('\n') if len(line) > 1]).astype(float)
        if stDateTime is not None and edDateTime is not None:
            if not isinstance(stDateTime, Iterable):
                stDateTime = [stDateTime]
                edDateTime = [edDateTime]
            for stTime, edTime in zip(stDateTime, edDateTime):
                m_cumSky.append(MoosasCumSky.fromPeriod(cumValue, stTime, edTime))
        else:
            m_cumSky.append(MoosasCumSky.fromPeriod(cumValue, 0, 8760))
    if len(m_cumSky) == 1:
        m_cumSky = m_cumSky[0]
    return m_cumSky
