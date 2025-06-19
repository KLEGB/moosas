#全局变量，存储天空
$current_CIESky = nil
$current_CumSky = nil
class MoosasCIESky
    Ver='0.6.1'
    '''
    根据CIE标准的15种天空模型，用于生成*.rad文件的句柄
    Properties:
        * altitude                      太阳高度角
        * azimuth                       太阳水平方位角
        * direct_normal_irradiance      直射辐射强度，来自气象数据库，需要根据总辐射&漫射辐射推算（DeST气象文件不记录）#climate_based 模型需要，暂不实现
        * diffuse_horizontal_irradiance 漫射辐射强度，来自气象数据库 *全阴天模型下为平均水平辐射通量 #climate_based 模型需要，暂不实现
        * ground_reflectance            地面反射系数，默认0.2
        * is_point_in_time              是否为PIT天空，默认为True
        * is_climate_based              是否为基于气象数据建立的天空 #climate_based 模型需要，暂不实现
        * sky_type                      Radiance天空类型句柄,与输入选项对应
        * lat
        * lng
    '''
    attr_accessor :alt, :az, :dir, :diff, :g_ref, :point_in_time, :climate_based,:sky_type,:lat,:lng
    # 挑选的天空类型
    if $language == 'Chinese'
        SKY_TYPE={'晴朗天空，清澄大气'=>"+s",
                    '晴朗天空，浑浊大气'=>"-s",
                    '多云天空，太阳的周边亮'=>"+i",
                    '多云天空，看不见太阳'=>"-i",
                    '全阴天'=>"-c"
                }
    else
        SKY_TYPE={'clear sky'=>"+s",
                    'clear sky without sun'=>"-s",
                    'cloudy sky'=>"+i",
                    'cloudy sky without sun'=>"-i",
                    'uniform sky'=>"-c"
                }
    end
    DOM=[31,28,31,30,31,30,31,31,30,31,30,31]

    def initialize(skytype,uni_diff=15000)
        #更新经纬度数据
        # datetime格式（来自输入：mm-dd-hr:min）"01-20-14:00"
        # 转换为0=>month 1=>day 2=>hr
        sf = MoosasWeather.singleton.station_info
        @lat = sf["lat"]
        @lng = sf["lng"]
        @sky_type=skytype
        #gen_sun(lat=sf["lat"],lng=sf["lng"],datetime)
        # 太阳白光平均光视觉效能
        @diff=uni_diff/179 
    end

    def gen_sun(lat,lng,datetime)
        datetime=datetime.to_s.split('-')
        datetime[2]=datetime[2].split(':')[0]
        # 太阳日
        n=0 
        for m in 0..datetime[0].to_i-1
            n+=DOM[m]
        end
        n+=datetime[1].to_i
        # 太阳赤纬角
        # Spencer, J.W. (1971) Fourier series representation of the position of the sun. Search, 5, 172.
        t=2*Math::PI*(n-1)/365
        asol=0.006918-0.399912*Math.cos(t)+0.070257*Math.sin(t)-0.006758*Math.cos(2*t)+0.000907*Math.sin(2*t)-0.002697*Math.cos(3*t)+0.00148*Math.sin(3*t)
        # 简化公式：
        #asol=23.45*Math.sin(2*Math::PI*(284+n)/365)
        # 正午太阳高度角
        hm=90-lat+asol
        #太阳日照时长
        # Cooper, P.I. (1969) The adsorption of radiation in solar stills. Solar Energy, 3, 333-346.
        ts=2/15*Math.acos(-Math.tan(asol)*Math.tan(lat))
        # 正午太阳时间
        tc=12+(lng-120)/360*1440/60
    end
    def gen_sky_from_date(datetime)
        hour=datetime[2].to_i
        # 格林威治时间
        hour_standard=hour+(@lng.to_f/15).round(0)
        if hour_standard<0
            hour_standard=hour_standard+24
            datetime[1]-=1
        end
        if hour_standard>24
            hour_standard=hour_standard-24
            datetime[1]+=1
        end
        sky_str=["!gensky",datetime[0].to_s,datetime[1].to_s,hour.to_s,@sky_type,"-a",@lat,"-o",@lng,"-g","0.200"].join(" ")
        if @sky_type=="-c"
            sky_str=sky_str+" -B #{@diff.to_s}"
        end
        sky_str=[sky_str,
            "skyfunc glow sky_mat","0","0","4","    1 1 1 0",
            "sky_mat source sky","0","0","4","    0 0 1 180",
            "skyfunc glow ground_glow","0","0","4","    1 .8 .5 0",
            "ground_glow source ground","0","0","4","    0 0 -1 180"].join("\n")
        return sky_str
    end
    def gen_sky()
        sky_str=["!gensky","-ang",@alt.to_s,@az.to_s,@sky_type].join(" ")
        if @sky_type=="-c"
            sky_str=sky_str+" -B #{@diff.to_s}"
        end
        sky_str=[sky_str,
            "skyfunc glow sky_mat","0","0","4","    1 1 1 0",
            "sky_mat source sky","0","0","4","    0 0 1 180",
            "skyfunc glow ground_glow","0","0","4","    1 .8 .5 0",
            "ground_glow source ground","0","0","4","    0 0 -1 180"].join("\n")
        return sky_str
    end
end
class MoosasCumSky
    Ver='0.6.4'
    DeltaAlt=12.0  #纬度便利常量
    SkyAziIncrement = [12,12,15,15,20,30,60]

    ANGLE_TO_PI = Math::PI / 180.0

    #Perez all weather sky model coefficients
    M_PerezClearnessBin= [1.065,1.23,1.5,1.95,2.8,4.5,6.2,999999]
    M_a1 = [1.3525,-1.2219,-1.1000,-0.5484,-0.6000,-1.0156,-1.0000,-1.0500]
    M_a2 = [-0.2576,-0.7730,-0.2515,-0.6654,-0.3566,-0.3670,0.0211,0.0289]
    M_a3 = [-0.2690,1.4148,0.8952,-0.2672,-2.5000,1.0078,0.5025,0.4260]
    M_a4 = [-1.4366,1.1016,0.0156,0.7117,2.3250,1.4051,-0.5119,0.3590]
    M_b1 = [-0.7670,-0.2054,0.2782,0.7234,0.2937,0.2875,-0.3000,-0.3250]
    M_b2 = [0.0007,0.0367,-0.1812,-0.6219,0.0496,-0.5328,0.1922,0.1156]
    M_b3 = [1.2734,-3.9128,-4.5000,-5.6812,-5.6812,-3.8500,0.7023,0.7781]
    M_b4 = [-0.1233,0.9156,1.1766,2.6297,1.8415,3.3750,-1.6317,0.0025]
    M_c1 = [2.8000,6.9750,24.7219,33.3389,21.0000,14.0000,19.0000,31.0625]
    M_c2 = [0.6004,0.1774,-13.0812,-18.3000,-4.7656,-0.9999,-5.0000,-14.5000]
    M_c3 = [1.2375,6.4477,-37.7000,-62.2500,-21.5906,-7.1406,1.2438,-46.1148]
    M_c4 = [1.0000,-0.1239,34.8438,52.0781,7.2492,7.5469,-1.9094,55.3750]
    M_d1 = [1.8734,-1.5798,-5.0000,-3.5000,-3.5000,-3.4000,-4.0000,-7.2312]
    M_d2 = [0.6297,-0.5081,1.5218,0.0016,-0.1554,-0.1078,0.0250,0.4050]
    M_d3 = [0.9738,-1.7812,3.9229,1.1477,1.4062,-1.0750,0.3844,13.3500]
    M_d4 = [0.2809,0.1080,-2.6204,0.1062,0.3988,1.5702,0.2656,0.6234]
    M_e1 = [0.0356,0.2624,-0.0156,0.4659,0.0032,-0.0672,1.0468,1.5000]
    M_e2 = [-0.1246,0.0672,0.1597,-0.3296,0.0766,0.4016,-0.3788,-0.6426]
    M_e3 = [-0.5718,-0.2190,0.4199,-0.0876,-0.0656,0.3017,-2.4517,1.8564]
    M_e4 = [0.9938,-0.4285,-0.5562,-0.0329,-0.1294,-0.4844,1.4656,0.5636]

    W = 2.0
    
    #Perez global luminous efficacy coefficients
    M_GlobLumEffya = [96.63,107.54,98.73,92.72,86.73,88.34,78.63,99.65]
    M_GlobLumEffyb = [-0.47,0.79,0.7,0.56,0.98,1.39,1.47,1.86]
    M_GlobLumEffyc = [11.5,1.79,4.4,8.36,7.1,6.06,4.93,-4.46]
    M_GlobLumEffyd = [-9.16,-1.19,-6.95,-8.31,-10.94,-7.6,-11.37,-3.15]

    #Perez diffuse luminous efficacy coefficients
    M_DiffLumEffya = [97.24,107.22,104.97,102.39,100.71,106.42,141.88,152.23]
    M_DiffLumEffyb = [-0.46,1.15,2.96,5.59,5.94,3.83,1.90,0.35]
    M_DiffLumEffyc = [12.0,0.59,-5.53,-13.95,-22.75,-36.15,-53.24,-45.27]
    M_DiffLumEffyd = [-8.91,-3.95,-8.77,-13.9,-23.74,-28.83,-14.03,-7.98]

    #Perez direct luminous efficacy coefficients
    M_BeamLumEffya = [57.2,98.99,109.83,110.34,106.36,107.19,105.75,101.18]
    M_BeamLumEffyb = [-4.55,-3.46,-4.90,-5.84,-3.97,-1.25,0.77,1.58]
    M_BeamLumEffyc = [-2.98,-1.21,-1.71,-1.99,-1.75,-1.51,-1.26,-1.10]
    M_BeamLumEffyd = [117.12,12.38,-8.81,-4.56,-6.16,-26.73,-34.44,-8.29]



    attr_accessor :m_CumSky, :summer_CumSky , :winter_CumSky , :m_ptx , :m_pty , :m_ptz
    @doIlluminance = true #if true, output luminance instead of radiance

    def get_cum_sky(normal,cum_sky_value=@m_CumSky)
        cum_sky=[]
        for i in 0..144 do
            sky_vector=Geom::Vector3d.new([@m_ptx[i].round(2),@m_pty[i].round(2),@m_ptz[i].round(2)])
            if normal.dot(sky_vector)>0
                cum_sky.push([sky_vector,(cum_sky_value[i]*normal.dot(sky_vector)).round(2)])
            end
        end
        return cum_sky
    end

    def initialize(sid)
        #加载天空模型数据
        begin
            @m_CumSky = []
            @summer_CumSky=[]
            @winter_CumSky=[]
            @m_ptx = []
            @m_pty = []
            @m_ptz = []

            # 加载太阳位置数据，共145面片
            File.open(MPath::DB+"sun_position.csv","r") do |file|
                while line = file.gets  
                    arr = line.split(',')
                    @m_ptx.push(arr[0].to_f)
                    @m_pty.push(arr[1].to_f)
                    @m_ptz.push(arr[2].to_f)
                end  
            end

            # 加载累积辐照度数据，计算全年/冬季/夏季
            File.open(MPath::SKY+"cumsky_#{sid}.csv","r") do |file|
                while line = file.gets  
                    arr = line.split(',').map { |e| e.to_f }
                    @m_CumSky.push(arr.sum()/1000)
                    @summer_CumSky.push(arr[3624,5832].sum()/1000)
                    @winter_CumSky.push((arr[0,1416].sum()+arr[8016,8759].sum())/1000)
                end  
            end
        rescue Exception => e
            MoosasUtils.rescue_log(e)
            p "**Error: failed to load cumsky model"
        end
        #result = self.pack_sky_patch_result
        #MoosasWebDialog.send("update_sky_model",result)
    end

    
    #def self.exoprt_all_city_sky_model()
    #     stations = MoosasWeather.get_all_stations_id
    #     counter = 1
    #     totalTime = 0
    #     stations.each do |sid|
    #         begin
    #             t1 = Time.now
    #             MoosasWeather.get_city_station_weather_data(sid.to_s)
    #             self.generate_cum_sky_model
    #             self.export_cum_sky_to_file
    #             t2 = Time.now
    #             p "处理第#{counter}个站点#{sid}, 用时#{t2-t1}s"
    #             totalTime += t2 - t1
    #             counter += 1
                
    #         rescue Exception => e
    #             p "导出天空模型#{sid}失败！"
    #         end
    #     end
    #     p "处理完成，总用时#{totalTime}s"
    # end

    # def self.export_cum_sky_to_file()
    #     begin
    #         path = File.dirname(__FILE__)+"/../cumsky/cumsky_#{MoosasWeather.get_station_id()}.csv"
    #         File.open(path, 'w') do |f|             #Ctrl+C 结束执行
    #             for i in 0..144 do 
    #                 f.puts [i,@m_ptPatchAlt[i],@m_ptPatchAz[i], @m_CumSky[i]].join(",")
    #             end
    #         end
    #     rescue Exception => e
    #         MoosasUtils.rescue_log(e)
    #         p "写天空模型#{MoosasWeather.get_station_id()}失败"
    #     end
    # end

    # def self.generate_cum_sky_model
    #     self.generate_sky_patch
    #     self.calculate_sky
    #     result = self.pack_sky_patch_result
    #     MoosasWebDialog.send("update_sky_model",result)
    # end

    # def self.pack_sky_patch_result()
    #     max = 0 - Float::INFINITY
    #     min = Float::INFINITY
        
    #     colours = [Sketchup::Color.new("Red"), Sketchup::Color.new("Yellow"), Sketchup::Color.new("Blue") ]
    #     numCols = 3

    #     for i in 0..144 do 
    #         spr = @m_CumSky[i]
    #         max = spr if spr > max
    #         min = spr if spr < min
    #     end

    #     @m_CumSky.each do |spr|
    #         if spr > 100000.0
    #             next
    #         end
    #         max = spr if spr > max
    #         min = spr if spr < min
    #     end

    #     #p "min=#{min}, max=#{max}"


    #     result = []
    #     @m_CumSky.each do |spr|

    #         band = spr / 5000.0

    #         if band <= 1.0
    #             weight = (spr - min) / (5000.0 - min)
    #             weight = 0.1 + weight * 0.9
    #         elsif band <= 3.0
    #             weight = (spr - 5000.0) / 10000.0
    #             weight = 0.9 + weight * 0.05
    #         elsif band <= 5.0
    #             weight = (spr - 15000.0) / 10000.0
    #             weight = 0.95 + weight * 0.05
    #         else
    #             weight = 1.0
    #         end

    #         colour = Sketchup::Color.new(colours[2]).blend(Sketchup::Color.new(colours[0]),weight)
                    
                    
                    


    #         # if spr > 5000
    #         #     weight = (spr - 5000) / (max - 5000.0)
    #         #     weight = 1.0 if weight > 1.0
    #         #     weight = 0.0 if weight < 0.0
    #         #     weight = weight * 0.9 + 0.1
    #         #     colour = Sketchup::Color.new(colours[1]).blend(Sketchup::Color.new(colours[0]),weight)
    #         # else
    #         #     weight = (spr - min) / (5000.0 - min)
    #         #     weight = 1.0 if weight > 1.0
    #         #     weight = 0.0 if weight < 0.0
    #         #     weight = weight * 0.9 + 0.1
    #         #     colour = Sketchup::Color.new(colours[2]).blend(Sketchup::Color.new(colours[1]),weight)
    #         # end

    #         # if spr >= ave
    #         #     weight = (spr - ave) / (max - ave)
    #         #     weight = 1.0 if weight > 1.0
    #         #     colour = Sketchup::Color.new(colours[2]).blend(Sketchup::Color.new(colours[1]),weight)
    #         # else
    #         #     weight = (spr - min) / (ave - min)
    #         #     weight = 1.0 if weight > 1.0
    #         #     colour = Sketchup::Color.new(colours[1]).blend(Sketchup::Color.new(colours[0]),weight)
    #         # end 
            
    #         result.push([spr,"#"+colour.to_i().to_s(16)])
    #     end

    #     #p result

    #     return result
    # end


    # #生成天空面片
    # def self.generate_sky_patch()
    #     @m_ptPatchAlt = []
    #     @m_ptPatchAz = []
    #     @m_ptPatchDeltaAlt = []
    #     @m_ptPatchDeltaAz = []
    #     @m_ptPatchLuminance = []
    #     @m_ptPatchSolidAngle = []

    #     alt = DeltaAlt / 2 
    #     pointer = 0
    #     iAlt = 0
    #     iPatch = 0
    #     #生成每个面片的参数
    #     while alt <= 84 do
    #         deltaAz = SkyAziIncrement[iAlt]
    #         az = 0
    #         while az <= 360 - deltaAz do
    #             @m_ptPatchAlt.push(alt * ANGLE_TO_PI)
    #             @m_ptPatchAz.push(az * ANGLE_TO_PI)
    #             @m_ptPatchDeltaAlt.push(DeltaAlt * ANGLE_TO_PI)
    #             @m_ptPatchDeltaAz.push(deltaAz * ANGLE_TO_PI)
    #             @m_ptPatchSolidAngle.push(2*Math::PI*(Math.sin( @m_ptPatchAlt[iPatch] + @m_ptPatchDeltaAlt[iPatch]/2)-Math.sin(@m_ptPatchAlt[iPatch]-@m_ptPatchDeltaAlt[iPatch]/2.0))/(2 * Math::PI /  (@m_ptPatchDeltaAz[iPatch])))
    #             az += deltaAz
    #             iPatch += 1
    #         end
    #         alt += DeltaAlt
    #         iAlt += 1
    #     end
    #     #最顶端中心的面片
    #     @m_ptPatchAlt.push(Math::PI / 2)
    #     @m_ptPatchAz.push(0)
    #     @m_ptPatchDeltaAlt.push(6 * Math::PI / 180)
    #     @m_ptPatchDeltaAz.push(2 * Math::PI)
    #     @m_ptPatchSolidAngle.push(2*Math::PI*(Math.sin(@m_ptPatchAlt[144])-Math.sin(@m_ptPatchAlt[144]-@m_ptPatchDeltaAlt[144]))/(2*Math::PI/(@m_ptPatchDeltaAz[144])))
    # end

    # def self.calculate_sky()

    #     lat = MoosasWeather.station_info["lat"] * Math::PI / 180
    #     ele = MoosasWeather.station_info["ele"]

    #     ptLv = [0] * 145
    #     m_ptRadiance = [[0] * 145] * 8760
    #     sunUpHourCount = 0

    #     MoosasSolar.reset

    #     day = 1
    #     while day <= 365 do 
    #         MoosasSolar.update_day_sun_info(day, lat, ele)
    #         hour = 0.5
    #         while hour < 24 do 
    #             eIllum=0
    #             cosMinSunDist=-999
    #             h_in_year= (day-1)*24+ hour
                
    #             sun = MoosasSolar.calculate_radianc_in_time(lat, day, hour)
    #             if self.set_sky_conditions(sun["e0"],sun["idh"],sun["ibh"],sun["alt"],sun["az"])
    #                 cosSunDist = -1

    #                 for i in 0..144 do
    #                     # first calculate relative luminance and scaling factor
    #                     patchAltitude=@m_ptPatchAlt[i]
    #                     patchAzimuth=@m_ptPatchAz[i]
    #                     ptLv[i]=self.get_relative_luminance(sun, patchAltitude,patchAzimuth)
    #                     eIllum += ptLv[i] * @m_ptPatchSolidAngle[i]*Math.sin(patchAltitude)
    #                     #work out distance of sun from this patch
    #                     cosSunDist = Math.cos(sun["alt"])*Math.cos(self.abs(sun["az"]-patchAzimuth))*Math.cos(patchAltitude) + Math.sin(sun["alt"])*Math.sin(patchAltitude)
    #                     if cosSunDist > cosMinSunDist
    #                         cosMinSunDist=cosSunDist
    #                         sunPatch=i
    #                     end
    #                 end

    #                 ibh = sun["ibh"]
    #                 idh = sun["idh"]

    #                 if sun["alt"] > 0
    #                     ibn = ibh / Math.sin(sun["alt"])
    #                 else
    #                     ibn = 0
    #                 end

    #                 if ibn > 1367.0
    #                     idh = idh + ibh
    #                     ibn = 0
    #                 end

    #                 if @doIlluminance 
    #                     normFac= idh*self.get_diffuse_LumEffy(sun["alt"],0.0)
    #                 else
    #                     normFac = idh
    #                 end

    #                 if eIllum > 0
    #                     sunUpHourCount += 1
    #                 end

    #                 for i in 0..144 do
    #                     if eIllum > 0 and @doIlluminance
    #                         m_ptRadiance[h_in_year][i]=ptLv[i]*normFac/eIllum
    #                     else
    #                         m_ptRadiance[h_in_year][i]=0
    #                     end 
    #                 end

    #                 #计算太阳直射
    #                 if @doIlluminance
    #                     normFac=ibn*self.get_beam_LumEffy(sun["alt"],0.0)
    #                 else
    #                     normFac=ibn
    #                 end

    #                 #add on direct radiation to patch with sun in
    #                 if sun["alt"] > 0 and ibn > 0
    #                     m_ptRadiance[h_in_year][sunPatch] += normFac/(@m_ptPatchSolidAngle[sunPatch])
    #                 end
    #             end
    #             hour += 1
    #         end
    #         day += 1
    #     end

    #     #汇总结果
    #     @m_CumSky = [0]*145
    #     for i in 0..144 do
    #         for h in 0..8759 do
    #             @m_CumSky[i] += m_ptRadiance[h][i]/sunUpHourCount
                
    #         end
    #     end

    #     for i in 0..144 do 
    #         if @m_CumSky[i] > 100000.0
    #             @m_CumSky[i] = @m_CumSky[i+1] if i == 0
    #             @m_CumSky[i] = @m_CumSky[i-1] if i == 144
    #             @m_CumSky[i] = (@m_CumSky[i+1] + @m_CumSky[i-1])/2
    #         end
    #     end

    #     return @m_CumSky
    # end

    # def self.set_sky_conditions(e0,idh,ibh,sun_alt,sun_az)
    #     return false if idh <= 0

    #     s_zenith = Math::PI / 2 - sun_alt

    #     #calculate clearness
    #     if sun_alt > 0
    #         ibn = ibh / Math.sin(sun_alt)
    #     elsif sun_alt <= 0 and ibh > 0
    #         idh = idh + ibh
    #         ibn = 0 
    #     else
    #         ibn = 0
    #     end
    #     perezClearness = ((idh+ibn)/idh + 1.041* self.pow(s_zenith,3))/(1+1.041*self.pow(s_zenith,3))

    #     #air optical mass
    #     if sun_alt >= (10.0 * Math::PI / 180.0)
    #         airMass=1/Math.sin(sun_alt)
    #     else
    #         airMass=1/(Math.sin(sun_alt) + 0.50572*self.pow(180*sun_alt/Math::PI+6.07995,-1.6364))
    #     end

    #     #fix in case a very negative solar altitude is input
    #     if (sun_alt * 180.0 / Math::PI + 6.07995) >= 0
    #         perezBrightness = airMass * idh / e0
    #     else
    #         if idh <= 10
    #             return false
    #         end
    #         perezBrightness = 0
    #     end

    #     # Temporary bit!!!
    #     if perezBrightness < 0.2 and (perezClearness > 1.065 and perezClearness < 2.8)
    #         perezBrightness = 0.2
    #     end

    #     #Now determine the model coefficients
    #     if perezClearness < 1.0
    #         return false
    #     end

    #     #find which 'clearness bin' to use (note intClearness is set to one lower than the 
    #     #tradiational bin numbers (i.e. for clearness bin 1, intClearness=0)
    #     i = 7
    #     while i >= 0 do
    #         if perezClearness < M_PerezClearnessBin[i]
    #             intClearness=i
    #         end
    #         i -= 1
    #     end

    #     @m_a = M_a1[intClearness] + M_a2[intClearness]*s_zenith + perezBrightness*(M_a3[intClearness] + M_a4[intClearness]*s_zenith)
    #     @m_b = M_b1[intClearness] + M_b2[intClearness]*s_zenith + perezBrightness*(M_b3[intClearness] + M_b4[intClearness]*s_zenith)
    #     @m_e = M_e1[intClearness] + M_e2[intClearness]*s_zenith + perezBrightness*(M_e3[intClearness] + M_e4[intClearness]*s_zenith)
    #     if intClearness > 0
    #         @m_c = M_c1[intClearness] + M_c2[intClearness]*s_zenith + perezBrightness*(M_c3[intClearness] + M_c4[intClearness]*s_zenith)
    #         @m_d = M_d1[intClearness] + M_d2[intClearness]*s_zenith + perezBrightness*(M_d3[intClearness] + M_d4[intClearness]*s_zenith)
    #     else
    #         #different equations for c & d in clearness bin no. 1
    #         @m_c=Math.exp(self.pow(perezBrightness*(M_c1[intClearness] + M_c2[intClearness]*s_zenith),M_c3[intClearness])) - 1
    #         @m_d=0-Math.exp(perezBrightness*(M_d1[intClearness] + M_d2[intClearness]*s_zenith)) + M_d3[intClearness] +  M_d4[intClearness]*perezBrightness
    #     end

    #     @m_coefficientsset=true
    #     @m_PerezClearness=perezClearness
    #     @m_IntPerezClearness=intClearness
    #     @m_PerezBrightness=perezBrightness

    #     return true
    # end

    # def self.get_relative_luminance(sun, alt,az)
    #     return -1 if not @m_coefficientsset
    #     cosSkySunAngle= Math.sin(alt)*Math.sin(sun["alt"]) + Math.cos(sun["alt"])*Math.cos(alt)*Math.cos(self.abs(az-sun["az"]))
    #     lv=(1 + @m_a*Math.exp(@m_b/Math.sin(alt))) * (1 + @m_c*Math.exp(@m_d*Math.acos(cosSkySunAngle)) + @m_e*cosSkySunAngle*cosSkySunAngle)
    #     lv = 0 if lv < 0
    #     return lv
    # end

    # def self.get_diffuse_LumEffy(solarAlt, td)
    #     return M_DiffLumEffya[@m_IntPerezClearness] + M_DiffLumEffyb[@m_IntPerezClearness]*W + M_DiffLumEffyc[@m_IntPerezClearness]*Math.sin(solarAlt) + M_DiffLumEffyd[@m_IntPerezClearness]*Math.log(@m_PerezBrightness)
    # end

    # def self.get_beam_LumEffy(solarAlt, td)
    #     bBeamLumEffy= M_BeamLumEffya[@m_IntPerezClearness] + M_BeamLumEffyb[@m_IntPerezClearness]*W + M_BeamLumEffyc[@m_IntPerezClearness]*Math.exp(5.73*(Math::PI/2-solarAlt)-5) + M_BeamLumEffyd[@m_IntPerezClearness]*@m_PerezBrightness
    #     if bBeamLumEffy > 0
    #         return bBeamLumEffy
    #     else
    #         return 0
    #     end
    # end

    # def self.pow(a,b)
    #     return a ** b
    # end

    # def self.abs(x)
    #     return x >= 0? x : 0-x
    # end
end