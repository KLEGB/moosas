import os

import numpy as np
from ..utils.tools import path, callCmd
weather_dic = os.path.join(path.dataBaseDir, 'weather')
temp_dic = path.tempDir
stationInfo = os.path.join(path.dataBaseDir, 'dest_station.csv')

class Location(object):
    __slots__ = ['stationId', 'city', 'state', 'latitude', 'longitude', 'altitude', 'pressure']

    def __init__(self, stationId, city, state, latitude, longitude, altitude, pressure):
        self.stationId = str(stationId)
        self.city = str(city)
        self.state = str(state)
        self.latitude = np.round(eval(latitude), 2)
        self.longitude = np.round(eval(longitude), 2)
        self.altitude = np.round(eval(altitude), 2)
        self.pressure = np.round(eval(pressure), 2)

    def __str__(self):
        return ','.join(np.array([self.stationId,
                                 self.city,
                                 self.state,
                                 self.latitude,
                                 self.longitude,
                                 self.altitude,
                                 self.pressure]).astype(str))

    @classmethod
    def fromString(cls,strArray:str):
        strArray = strArray.split(',')
        if len(strArray) < 5: return None
        return cls(*strArray)

    def __repr__(self):
        print(f"""
            Station:{self.stationId}
            city:{self.city}
            state:{self.state}
            lat:{self.latitude},lon:{self.longitude},alt:{self.altitude}
            Atmo_pressure:{self.pressure}
        """)

class MoosasWeather(object):
    __slots__ = ['weatherData', 'location', 'weatherFile','stationDict', 'params']

    def __init__(self, stationid: str):
        self.stationDict = self.loadStation()
        weatherPath = os.path.join(weather_dic, stationid + '.csv')
        self.location = self.stationDict[stationid]
        self.weatherFile = os.path.abspath(weatherPath)
        self.weatherData = self.loadWeatherData(weatherPath)
        self.params = object()

    @staticmethod
    def loadStation():
        stationDict = {}
        with open(stationInfo, 'r') as f:
            lines = f.read().split('\n')
            for line in lines:
                if len(line) > 0:
                    line = line.split(',')
                    if len(line) < 5: continue
                    stationDict[line[0]] = Location(*line)
        return stationDict

    @staticmethod
    def loadWeatherData(path):
        '''
            # 气象站编号
            # 无用，0
            # 小时数 int,0-8760
            # 空气温度 Dry Bulb Temperature
            # 空气含湿量 Humidity Ratio
            # 地面水平总辐射量 Global Horizontal Radiation
            # 地面水平散射辐射量 Diffuse Horizontal Radiation
            # 0.5m地面温度，按月平均拓展 Ground Temperature record in month
            # 天空有效温度 Effective Sky (Radiating) Temperature
            # 风速
            # 风向 C=0,NE=1,E=2....NW=15,N=16
            # 站点大气压 Atmospheric Station Pressure
            # ！未知数据,9999999
        '''
        with open(path, 'r') as f:
            data = np.array([line.strip('\n').split(',') for line in f.readlines()]).T
            return {
                'hoy': data[2],
                'temperature': data[3],
                'humidityRatio': data[4],
                'globalRad': data[5],
                'diffuseRad': data[6],
                'groundTemp': data[7],
                'skyTemp': data[8],
                'windVel': data[9],
                'windDir': data[10],
                'Pressure': data[11]
            }

