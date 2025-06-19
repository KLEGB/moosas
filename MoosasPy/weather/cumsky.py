from __future__ import annotations

import os
import numpy as np
from ..geometry.geos import Vector
from ..utils.tools import path
from ..utils.date import DateTime
from ..utils import Iterable


class MoosasCumSky(object):
    __slots__ = ['position', 'value']
    ANNUAL_HOY = 8760
    FIX_RADIATION = 1000
    SUMMER_START_HOY = 3624
    SUMMER_END_HOY = 5832
    WINTER_START_HOY = 8016
    WINTER_END_HOY = 1416

    def __init__(self, cumValue=None):
        self.value = cumValue
        self.position = []
        with open(os.path.join(path.libDir, r'weather\sun_position.csv')) as f:
            self.position = [Vector(np.array(line.split(',')).astype(float)) for line in f.read().split('\n')]

    @classmethod
    def fromPeriod(cls, cumValue, stDateTime: DateTime | int, edDateTime: DateTime | int):
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
    m_cumSky = []
    with open(os.path.join(path.dataBaseDir, f'cum_sky\\cumsky_{stationid}.csv')) as f:
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
