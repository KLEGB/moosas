"""
    Define DirectSun position from lat and lon
    The sun position object define consider leap your, timezone and solartime.
    This class have learnt from ladybug for direct sun calculation.
"""
from __future__ import annotations

from ..utils.date import DateTime
from ..geometry.geos import Vector
from ..utils.constant import dateSetting
import numpy as np


class SunPosition(Vector):
    """An object representing a single Sun. construct based on Vector

    Args:
        datetime: A DateTime that represents the datetime for this sun_vector
        altitude: Solar Altitude in degrees.
        azimuth: Solar Azimuth in degrees.
        is_daylight_saving: A Boolean indicating if the datetime is calculated
            for a daylight saving period
        north_angle: North angle of the sunpath in degrees. This is only used to
            adjust the sun_vector and does not affect the sun altitude or azimuth.

    Properties:
        * datetime
        * north_angle
        * hoy
        * altitude
        * azimuth
        * is_daylight_saving
        * data
    """

    __slots__ = ('datetime', 'is_daylight_saving', 'north_angle', 'data')
    PI = np.pi

    def __init__(self, datetime: DateTime, altitude, azimuth,
                 is_daylight_saving=False, north_angle=0, data=None):
        """Init sun."""
        self.datetime = datetime  # read-only

        assert -90 <= altitude <= 90, \
            'altitude({}) must be between {} and {}.' \
                .format(altitude, -self.PI, self.PI)

        assert -360 <= azimuth <= 360, \
            'azimuth({}) should be between {} and {}.' \
                .format(azimuth, -self.PI, self.PI)
        if north_angle != 0:
            azimuth -= north_angle
        sunVec = self.azimuthToVector(azimuth)
        sunVec.z = sunVec.length() * np.tan(np.radians(altitude))
        super(SunPosition, self).__init__(sunVec.unit())

        self.is_daylight_saving = is_daylight_saving
        self.north_angle = north_angle
        self.data = data  # place holder for metadata

    def __repr__(self):
        """Sun representation."""
        return "Sun at {} (x:{}, y:{}, z:{})".format(
            self.datetime,
            self.x,
            self.y,
            self.z
        )



class MoosasDirectSky(object):
    """Calculate sun positions

    Args:
        latitude: A number between -90 and 90 for the latitude of the location
            in degrees. (Default: 0 for the equator)
        longitude: A number between -180 and 180 for the longitude of the location
            in degrees (Default: 0 for the prime meridian)
        timeZone: A number representing the time zone of the location for the
            sun path. Typically, this value is an integer, assuming that a
            standard time zone is used but this value can also be a decimal
            for the purposes of modeling location-specific solar time.
            The time zone should follow the epw convention and should be
            between -12 and +14, where 0 is at Greenwich, UK, positive values
            are to the East of Greenwich and negative values are to the West.
            If None, this value will be set to solar time using the Sunpath's
            longitude. (Default: None).
        northAngle: A number between -360 and 360 for the counterclockwise
            difference between the North and the positive Y-axis in degrees.
            90 is West and 270 is East (Default: 0).
        daylight_saving_period: An analysis period for daylight saving time.
            If None, no daylight saving time will be used. (Default: None)

    Properties:
        * latitude
        * longitude
        * time_zone
        * north_angle
        * daylight_saving_period
        * is_leap_year
    """

    __slots__ = ('longitude', 'latitude', 'northAngle', 'timeZone',
                 'daylightSavingPeriod')
    PI = np.pi

    def __init__(self, latitude: float, longitude: float,
                 timeZone: int = None, northAngle: float = 0,
                 daylightSavingStDay: DateTime | int = None, daylightSavingEdDay: DateTime | int = None):
        """Init sunpath.
        """
        self.latitude = float(latitude)
        if self.latitude == self.PI / 2:  # prevent np domain errors
            self.latitude = self.latitude - 1e-9
        if self.latitude == -self.PI / 2:  # prevent np domain errors
            self.latitude = self.latitude + 1e-9
        self.longitude = float(longitude)
        self.timeZone = longitude / 15 if timeZone is None else timeZone
        self.northAngle = int(northAngle)
        if isinstance(daylightSavingStDay, int):
            daylightSavingStDay = DateTime.from_hoy(daylightSavingStDay)
        if isinstance(daylightSavingEdDay, int):
            daylightSavingEdDay = DateTime.from_hoy(daylightSavingEdDay)
        self.daylightSavingPeriod = (daylightSavingStDay, daylightSavingEdDay)

    def isDaylightSavingHour(self, datetime: DateTime) -> bool:
        """Check if a datetime is within the daylight saving time."""
        if not self.daylightSavingPeriod[0] or not self.daylightSavingPeriod[1]:
            return False
        else:
            return self.daylightSavingPeriod[0].moy <= datetime.moy < self.daylightSavingPeriod[1].moy

    def sunAtDateTime(self, datetime: DateTime) -> SunPosition:
        """Get Sun for a specific datetime.

        This code is originally written by Trygve Wastvedt (Trygve.Wastvedt@gmail.com)
        based on (NOAA) and modified by Chris Mackey and Mostapha Roudsari.

        Args:
            datetime: Ladybug datetime.

        Returns:
            A sun object for the input datetime.
        """

        # compute solar geometry
        sol_dec, eq_of_time = self.calculateSolarGeometry(datetime)

        # get the correct mintue of the day for which solar position is to be computed
        try:
            hour = datetime.float_hour
        except AttributeError:  # native Python datetime; try to compute manually
            hour = datetime.hour + datetime.minute / 60.0
        is_daylight_saving = self.isDaylightSavingHour(datetime)
        hour = hour - 1 if is_daylight_saving else hour  # spring forward!
        sol_time = self.calculateSolarTime(hour, eq_of_time) * 60

        # degrees for the angle between solar noon and the current time.
        hour_angle = sol_time / 4 + 180 if sol_time < 0 else sol_time / 4 - 180

        # radians for the zenith and degrees for altitude
        zenith = np.arccos(np.sin(self.latitude) * np.sin(sol_dec) +
                         np.cos(self.latitude) * np.cos(sol_dec) *
                         np.cos(np.radians(hour_angle)))
        altitude = 90 - np.degrees(zenith)

        # approx atmospheric refraction used to correct the altitude
        if altitude > 85:
            atmos_refraction = 0
        elif altitude > 5:
            atmos_refraction = 58.1 / np.tan(np.radians(altitude)) - \
                               0.07 / (np.tan(np.radians(altitude))) ** 3 + \
                               0.000086 / (np.tan(np.radians(altitude))) ** 5
        elif altitude > -0.575:
            atmos_refraction = 1735 + altitude * \
                               (-518.2 + altitude * (103.4 + altitude * (-12.79 + altitude * 0.711)))
        else:
            atmos_refraction = -20.772 / np.tan(np.radians(altitude))

        atmos_refraction /= 3600
        altitude += atmos_refraction

        # azimuth in degrees
        az_init = ((np.sin(self.latitude) * np.cos(zenith)) - np.sin(sol_dec)) / \
                  (np.cos(self.latitude) * np.sin(zenith))
        try:
            if hour_angle > 0:
                azimuth = (np.degrees(np.arccos(az_init)) + 180) % 360
            else:
                azimuth = (540 - np.degrees(np.arccos(az_init))) % 360
        except ValueError:  # perfect solar noon yields np domain error
            azimuth = 180

        # create the sun for this hour
        return SunPosition(datetime, altitude, azimuth, is_daylight_saving,
                           self.northAngle)

    def annualSun(self, leapYear=False) -> list[SunPosition]:
        hoyList = list(np.arange(8760)) if not leapYear else list(np.arange(8761))
        datetimeList = [DateTime.from_hoy(hoy) for hoy in hoyList]
        sunList = [self.sunAtDateTime(dateTime) for dateTime in datetimeList]
        return sunList

    def calculateSolarGeometry(self, datetime: DateTime):
        def _days_from_010119(year, month, day):
            """Calculate the number of days from 01-01-1900 to the provided date.

            Args:
                year: Integer. The year in the date
                month: Integer. The month in the date
                day: Integer. The day in the date

            Returns:
                The number of days since 01-01-1900 to the provided date
            """

            def is_leap_year(year):
                """Determine whether a year is a leap year over the past centuries."""
                return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

            years = range(1900, year)  # list of years from 1900
            # Number of days in a year are 366 if it is a leap year
            days_in_year = []
            for item in years:
                if is_leap_year(item):
                    days_in_year.append(366)
                else:
                    days_in_year.append(365)
            # Making the total of all the days in preceding years
            days_in_preceding_years = 0
            for days in days_in_year:
                days_in_preceding_years += days

            # get the total of all the days in preceding months in the same year
            month_array = dateSetting.MONTH_DAY_LEAP if is_leap_year(year) \
                else dateSetting.MONTH_DAY
            days_in_preceding_months = 0
            for i in range(month - 1):
                days_in_preceding_months += month_array[i]

            return days_in_preceding_years + days_in_preceding_months + day + 1

        """Calculate parameters related to solar geometry for an hour of the year.

        Attributes:
            datetime: A Ladybug datetime

        Returns:
            A tuple with two values

            - sol_dec: Solar declination in radians. Declination is analogous to
                latitude on Earth's surface, and measures an angular displacement
                north or south from the projection of Earth's equator on the
                celestial sphere to the location of a celestial body.

            - eq_of_time: Equation of time in minutes. This is an astronomical
                term accounting for changes in the time of solar noon for a given
                location over the course of a year. Earth's elliptical orbit and
                Kepler's law of equal areas in equal times are the culprits
                behind this phenomenon.
        """
        year, month, day, hour, minute = \
            datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute

        julian_day = _days_from_010119(year, month, day) + 2415018.5 + \
                     round((minute + hour * 60) / 1440.0, 2) - (float(self.timeZone) / 24)

        julian_century = (julian_day - 2451545) / 36525

        # degrees
        geom_mean_long_sun = (280.46646 + julian_century *
                              (36000.76983 + julian_century * 0.0003032)
                              ) % 360
        # degrees
        geom_mean_anom_sun = 357.52911 + julian_century * \
                             (35999.05029 - 0.0001537 * julian_century)

        eccent_orbit = 0.016708634 - julian_century * \
                       (0.000042037 + 0.0000001267 * julian_century)

        sun_eq_of_ctr = np.sin(
            np.radians(geom_mean_anom_sun)) * \
                        (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century)
                         ) + \
                        np.sin(np.radians(2 * geom_mean_anom_sun)) * \
                        (0.019993 - 0.000101 * julian_century) + \
                        np.sin(np.radians(3 * geom_mean_anom_sun)) * \
                        0.000289

        # degrees
        sun_true_long = geom_mean_long_sun + sun_eq_of_ctr

        # degrees
        sun_app_long = sun_true_long - 0.00569 - 0.00478 * \
                       np.sin(np.radians(125.04 - 1934.136 * julian_century))

        # degrees
        mean_obliq_ecliptic = 23 + \
                              (26 + ((21.448 - julian_century * (46.815 + julian_century *
                                                                 (0.00059 - julian_century *
                                                                  0.001813)))) / 60) / 60

        # degrees
        oblique_corr = mean_obliq_ecliptic + 0.00256 * \
                       np.cos(np.radians(125.04 - 1934.136 * julian_century))

        # RADIANS
        sol_dec = np.arcsin(np.sin(np.radians(oblique_corr)) *
                          np.sin(np.radians(sun_app_long)))

        var_y = np.tan(np.radians(oblique_corr / 2)) * \
                np.tan(np.radians(oblique_corr / 2))

        # minutes
        eq_of_time = 4 \
                     * np.degrees(
            var_y * np.sin(2 * np.radians(geom_mean_long_sun)) -
            2 * eccent_orbit * np.sin(np.radians(geom_mean_anom_sun)) +
            4 * eccent_orbit * var_y *
            np.sin(np.radians(geom_mean_anom_sun)) *
            np.cos(2 * np.radians(geom_mean_long_sun)) -
            0.5 * (var_y ** 2) *
            np.sin(4 * np.radians(geom_mean_long_sun)) -
            1.25 * (eccent_orbit ** 2) *
            np.sin(2 * np.radians(geom_mean_anom_sun))
        )

        return sol_dec, eq_of_time

    def calculateSolarTime(self, hour: float, eq_of_time: float):
        """Calculate Solar time for an hour."""

        return ((hour * 60 + eq_of_time + 4 * np.degrees(self.longitude) -
                 60 * self.timeZone) % 1440) / 60

    def __repr__(self):
        """Sunpath representation."""
        return "Sunpath (lat:{}, lon:{}, time zone:{})".format(
            self.latitude, self.longitude, self.timeZone)
