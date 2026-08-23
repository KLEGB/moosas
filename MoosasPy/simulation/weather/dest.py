import os

import numpy as np
from ...utils.tools import path, callCmd
weather_dic = os.path.join(path.dataBaseDir, 'weather')
temp_dic = path.tempDir
stationInfo = os.path.join(path.dataBaseDir, 'dest_station.csv')

class Location(object):
    __slots__ = ['stationId', 'city', 'state', 'latitude', 'longitude', 'altitude', 'pressure']

    def __init__(self, stationId, city, state, latitude, longitude, altitude, pressure):
        """
        Initialize a station object with geographic and atmospheric data.
        
        Parameters
        ----------
        stationId : str
            Unique identifier for the station, converted to string.
        city : str
            Name of the city where the station is located, converted to string.
        state : str
            Name of the state where the station is located, converted to string.
        latitude : float or str
            Latitude of the station in degrees, evaluated and rounded to 2 decimal places.
        longitude : float or str
            Longitude of the station in degrees, evaluated and rounded to 2 decimal places.
        altitude : float or str
            Altitude of the station in meters, evaluated and rounded to 2 decimal places.
        pressure : float or str
            Atmospheric pressure at the station in hPa, evaluated and rounded to 2 decimal places.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        self.stationId = str(stationId)
        self.city = str(city)
        self.state = str(state)
        self.latitude = np.round(eval(latitude), 2)
        self.longitude = np.round(eval(longitude), 2)
        self.altitude = np.round(eval(altitude), 2)
        self.pressure = np.round(eval(pressure), 2)

    def __str__(self):
        """
        String representation of the object.
        
        Returns a comma-separated string of the object's attributes, including stationId, city, state, 
        latitude, longitude, altitude, and pressure.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the attributes to be converted to a string.
        
        Returns
        -------
        str
            A comma-separated string representation of the object's attributes.
        """
        return ','.join(np.array([self.stationId,
                                 self.city,
                                 self.state,
                                 self.latitude,
                                 self.longitude,
                                 self.altitude,
                                 self.pressure]).astype(str))

    @classmethod
    def fromString(cls,strArray:str):
        """
        Create an instance of the class from a comma-separated string.
        
        Parameters
        ----------
        cls : type
            The class upon which this method is called.
        strArray : str
            A comma-separated string containing at least five values to be used as arguments for initializing the class instance.
        
        Returns
        -------
        object or None
            An instance of the class initialized with the split string values if there are at least five elements; otherwise, None.
        """
        strArray = strArray.split(',')
        if len(strArray) < 5: return None
        return cls(*strArray)

    def __repr__(self):
        """
        String representation of the station's information.
        
        Returns
        -------
        None
            This function prints the station information to stdout and does not return any value.
        """
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
        """
        Initialize the weather station object with a given station ID.
        
        Parameters
        ----------
        stationid : str
            The ID of the weather station to load data for. Used to locate the corresponding CSV file and retrieve station location.
        
        Returns
        -------
        None
        """
        self.stationDict = self.loadStation()
        weatherPath = os.path.join(weather_dic, stationid + '.csv')
        self.location = self.stationDict[stationid]
        self.weatherFile = os.path.abspath(weatherPath)
        self.weatherData = self.loadWeatherData(weatherPath)
        self.params = object()

    @staticmethod
    def loadStation():
        """
        Load station information from a file into a dictionary.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        dict of {str: Location}
            A dictionary mapping station IDs (strings) to Location objects containing station details.
        """
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
        """
        Load weather data from a CSV file into a dictionary of arrays.
        
        Parameters
        ----------
        path : str
            Path to the input CSV file containing weather data. The file is expected
            to have comma-separated values with specific columns corresponding to
            different meteorological variables.
        
        Returns
        -------
        dict
            A dictionary containing the following keys and corresponding data arrays:
            - 'hoy' (array-like): Hour of the year (int, 0-8760).
            - 'temperature' (array-like): Dry bulb temperature (°C).
            - 'humidityRatio' (array-like): Humidity ratio (g/kg or kg/kg).
            - 'globalRad' (array-like): Global horizontal radiation (W/m²).
            - 'diffuseRad' (array-like): Diffuse horizontal radiation (W/m²).
            - 'groundTemp' (array-like): Ground temperature at 0.5m depth, monthly averaged (°C).
            - 'skyTemp' (array-like): Effective sky (radiating) temperature (°C).
            - 'windVel' (array-like): Wind speed (m/s).
            - 'windDir' (array-like): Wind direction (coded as 0=Calm, 1=NE, ..., 16=N).
            - 'Pressure' (array-like): Atmospheric station pressure (Pa).
        """
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

