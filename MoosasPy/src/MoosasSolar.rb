
class MoosasSolar
    Ver='0.6.1'

    class << self
        attr_reader :declination
    end

    GSC = 1367.0  # W/m*m

    def self.reset()
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

