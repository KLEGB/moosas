
class MoosasSolar
    Ver='0.6.1'

    class << self
        attr_reader :declination
    end

    GSC = 1367.0  # W/m*m

    def self.reset()
    # Function:
    # Resets all class variables to their initial zero values. This method is typically used to clear previously calculated solar position and daylight-related data.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
        @declination = 0
        @dayLength = 0
        @sunrise =  0
        @sunset = 0
        @gon=0
        @a0=0
        @a1=0
        @k=0
    end


    '''**
     * 根据天数更新一些信息
     * @param n
     *'''
    def self.update_day_sun_info(n, lat, ele)
    # Function
    # --------
    # Updates the solar information for a given day, including day length, sunrise and sunset times,
    # solar constant correction (extraterrestrial irradiance), and atmospheric transmittance coefficients,
    # based on day of year, latitude, and elevation.
    # 
    # Parameters
    # ----------
    # n : Integer
    # The day of the year (1-365 or 1-366 for leap years), used to calculate solar declination
    # and day angle for extraterrestrial radiation adjustments.
    # lat : Float
    # The latitude of the location in degrees (positive for northern hemisphere,
    # negative for southern hemisphere), used to compute day length and solar angles.
    # ele : Float
    # The elevation above sea level in meters. Internally converted to kilometers;
    # used to adjust atmospheric transmittance coefficients (a0, a1, k).
    # 
    # Returns
    # -------
    # None
    # This method updates several instance variables but does not return a value:
    # - @declination: Solar declination in degrees.
    # - @dayLength: Length of the daylight period in hours.
    # - @sunrise: Estimated hour of sunrise (rounded up to nearest hour).
    # - @sunset: Estimated hour of sunset (rounded down to nearest hour).
    # - @gon: Extraterrestrial irradiance (corrected for Earth-Sun distance).
    # - @a0, @a1, @k: Atmospheric transmittance coefficients dependent on elevation.

        @declination = 23.45 * Math.sin(2 * Math::PI * (284 + n) / 365)
        @dayLength = 2.0 / 15 * Math.acos(0 - Math.tan(lat)*Math.tan(@declination * Math::PI / 180)) * 180 / Math::PI
        @sunrise =  (12 - @dayLength /2).ceil
        @sunset =  (12 + @dayLength /2).floor
        ele = ele/1000   #千米制
        #需要补充完善这个地方的判断
        if ele >= 2.5
            ele = 2.49
        end
        day_angle=2 * Math::PI * n / 365

        @gon = GSC * (1.00011+0.034221*Math.cos(day_angle)+0.00128*Math.sin(day_angle)+0.000719*Math.cos(2*day_angle)+0.000077*Math.sin(2*day_angle))

        @a0 = 0.97 * (0.4237 - 0.00821 * Math.sqrt(6 - ele))
        @a1 = 0.99 * (0.5055 + 0.00595 * Math.sqrt(6.5 - ele))
        @k = 1.02 * (0.2711 + 0.01858 * Math.sqrt(2.5 - ele))
    end


    '''**
     * 根据经纬度、第n天第h时、海拔，计算太阳入射方向和入射强度
     * @param lat
     * @param lng
     * @param n
     * @param h
     * @return
     *'''
    def self.calculate_qsolar_in_time(lat, n, h)
    # Function
    # --------
    # Calculate the solar radiation intensity (direct and diffuse) for a given hour of the day.
    # 
    # This method computes the x, y, z components of the solar vector and the global solar irradiance 'g'
    # based on latitude, day of year, and hour of day. If the hour is outside sunrise/sunset times,
    # all values are set to zero. Otherwise, solar geometry (hour angle, solar altitude, and azimuth)
    # is calculated, followed by correction factors and total solar irradiance.
    # 
    # Parameters
    # ----------
    # lat : Float
    # Latitude of the location in radians.
    # n : Integer
    # Day of the year (1 <= n <= 365 or 366), used to determine solar declination (@declination should be precomputed).
    # h : Float
    # Hour of the day (in 24-hour format, e.g., 9.5 for 9:30 AM). Must be between 0 and 24.
    # 
    # Returns
    # -------
    # sun : Hash
    # A hash containing the following keys:
    # - "x" : Float, x-component of solar direction vector (east-west, positive west).
    # - "y" : Float, y-component of solar direction vector (north-south, positive south).
    # - "z" : Float, z-component (vertical component, sine of solar altitude).
    # - "g" : Float, estimated global solar irradiance (combination of direct and diffuse radiation),
    # calculated using empirical coefficients @a0, @a1, @k, and @gon.
    # Values are set to 0 if the time is before sunrise or after sunset.
        sun = {}   #x, y, z, G
        if h < @sunrise or h > @sunset   #如果超过日出日落时间的范围，就不用计算
            sun["x"]=sun["y"]=sun["z"]=sun["g"] = 0 
        else
            hourangle = 15 * (12 - h)
            #计算太阳高度角hs,太阳方位角r
            hs = Math.asin(Math.cos(lat) * Math.cos(@declination * Math::PI / 180) * Math.cos(hourangle * Math::PI / 180) + Math.sin(lat) * Math.sin(@declination * Math::PI / 180))
            if h == 12
                r = 0
            else
                r = Math.acos((Math.sin(hs) * Math.sin(lat) - Math.sin(@declination * Math::PI / 180))/(Math.cos(hs) * Math.cos(lat)))
            end
            sun["x"] = Math.cos(hs) * Math.sin(r)
            if hourangle< 12
                sun["x"] = 0 - sun["x"]
            end
            sun["y"] = 0 - Math.cos(hs) * Math.cos(r)
            if lat < 0 and h == 12
                sun["y"] = 0 - sun["y"]
            end
            sun["z"] = Math.sin(hs)
            
            #计算修正系数
            thelta = 90 - hs
            cb = @a0 + @a1 * Math.exp(0 - @k / Math.cos(thelta * Math::PI / 180))
            cd = 0.271 - 0.294 * cb
            sun["g"] = @gon * (cb + cd) / 2.0
            #sun["ibh"] =  @gon * cb / 5
            #sun["idh"] = @gon * cd / 5
        end 
        return sun
    end

    '''
        计算每个小时的太阳直射和散射的强度值
    '''
    def self.calculate_radianc_in_time(lat, n, h)
    # Function
    # --------
    # Calculates solar radiation parameters at a given time based on latitude, day of year, and hour of day.
    # This method computes solar altitude, azimuth, and various radiation components (direct horizontal, diffuse horizontal, extraterrestrial radiation) depending on whether the specified hour is within sunrise and sunset times.
    # 
    # Parameters
    # ----------
    # lat : Float
    # Latitude of the location in radians.
    # n : Integer
    # Day of the year (1 <= n <= 365 or 366 for leap years).
    # h : Float
    # Hour of the day (in 24-hour format, e.g., 12.5 for 12:30 PM). Must be between 0 and 24.
    # 
    # Returns
    # -------
    # Hash
    # A dictionary containing the following keys:
    # - "alt" (Float): Solar altitude angle in radians.
    # - "az" (Float): Solar azimuth angle in radians.
    # - "ibh" (Float): Beam horizontal irradiance.
    # - "idh" (Float): Diffuse horizontal irradiance.
    # - "e0" (Float): Extraterrestrial radiation.
    # If the hour `h` is outside sunrise/sunset times, all values are set to 0.
        sun = {}   #x, y, z, G
        if h < @sunrise or h > @sunset   #如果超过日出日落时间的范围，就不用计算
            sun["alt"]=sun["az"]=sun["idh"]=sun["ibh"] =sun["e0"]= 0 
        else
            hourangle = 15 * (12 - h)
            #计算太阳高度角hs,太阳方位角r
            hs = Math.asin(Math.cos(lat) * Math.cos(@declination * Math::PI / 180) * Math.cos(hourangle * Math::PI / 180) + Math.sin(lat) * Math.sin(@declination * Math::PI / 180))
            if h == 12
                r = 0
            else
                r = Math.acos((Math.sin(hs) * Math.sin(lat) - Math.sin(@declination * Math::PI / 180))/(Math.cos(hs) * Math.cos(lat)))
            end
            sun["alt"] = hs #* Math::PI / 180.0
            sun["az"] = r #* Math::PI / 180.0
            
            #计算修正系数
            thelta = 90 - hs
            cb = @a0 + @a1 * Math.exp(0 - @k / Math.cos(thelta * Math::PI / 180))
            cd = 0.271 - 0.294 * cb
            sun["ibh"] = @gon * cb / 2
            sun["idh"] = @gon * cd / 2 
            sun["e0"] = @gon / 2
        end 
        return sun
    end

    '''**
     * 根据太阳入射方向、平面法向量、太阳入射强度，计算平面的太阳辐射强度
     * @param nx
     * @param ny
     * @param nz
     * @param sun (x,y,z,G)
     * @return
     *'''
    def self.calculate_qsolar_on_face(nx,ny,nz,sun)
    # Function:
    # Calculates the solar radiation incident on a surface face based on surface normal and sun direction.
    # 
    # Parameters:
    # nx : Float
    # The x-component of the unit normal vector of the surface face.
    # ny : Float
    # The y-component of the unit normal vector of the surface face.
    # nz : Float
    # The z-component of the unit normal vector of the surface face.
    # sun : Hash
    # A hash containing solar vector components and irradiance:
    # - "x": x-component of the solar direction vector.
    # - "y": y-component of the solar direction vector.
    # - "z": z-component of the solar direction vector.
    # - "g": global solar irradiance (W/m²).
    # 
    # Returns:
    # Float
    # The effective solar radiation (in W/m²) incident on the surface face.
    # Returns 0 if the sun is below the horizon (sun["g"] == 0) or if the angle between the sun and the surface normal is greater than 90 degrees (cos < 0).
    # Otherwise, returns the projected irradiance using the cosine of the incidence angle multiplied by half the global irradiance.
        if sun["g"] == 0
            return 0
        end
        cos = (nx*sun["x"] + ny*sun["y"] + nz * sun["z"]) / (Math.sqrt(nx*nx + ny*ny + nz*nz)*Math.sqrt(sun["x"]*sun["x"] + sun["y"]*sun["y"]+sun["z"]*sun["z"]))
        if cos < 0
            return 0
        else
            return cos * sun["g"] / 2.0
        end
    end

end

