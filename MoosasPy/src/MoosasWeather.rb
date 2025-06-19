
#encoding: utf-8
require 'open-uri'

'''
    处理气象数据的函数
'''
class MoosasWeather
    Ver='0.6.4'
    class << self
        attr_accessor :singleton, :station_id #单例，全局变量
        attr_reader :stations
    end
    attr_accessor :station_info, :station_id, :weather_data, :climate_zone

    @stations = Hash.new
    @station_id = "545110"   #当前选中的气象站id
    @station_info = nil #当前选中的气象站信息
    @weather_data = nil #当前的气象数据
    @climate_zone = "climate_zone3"

    def self.load_data()
        MoosasWeather.load_weather_stations_data
        MoosasWeather.station_id = "545110"  #默认采用北京的数据
        MoosasWeather.load_singleton
        #MoosasWebDialog.send("update_weather_chart",{"weather"  => MoosasWeather.singleton.to_json_string()})
        $current_CumSky = MoosasCumSky.new(MoosasWeather.station_id)
        
    end

    def self.reset_weather_data_to_ui()
        #将数据传到前端进行显示
        MoosasWebDialog.send("load_weather_stations_data",{"stations"  => @stations, "station_id" => @station_id})  
        MoosasWeather.load_singleton      
        MoosasWebDialog.send("update_weather_chart",{"weather"  => MoosasWeather.singleton.to_json_string()})
    end

    def self.update_weather_station(sid)
        MoosasWeather.station_id = sid
        MoosasWeather.load_singleton
        MoosasWebDialog.send("update_weather_chart",{"weather"  => MoosasWeather.singleton.to_json_string()})
        $current_CumSky = MoosasCumSky.new(MoosasWeather.station_id)
        #p MoosasWeather.singleton.to_json_string()
    end

    def self.load_weather_stations_data()
        #加载气象数据数据站点参数
        begin
            File.open(MPath::DB+"dest_station.csv","r") do |file|
                while line = file.gets  
                    arr = line.split(',')
                    @stations[arr[0]]= {
                        "sid"=>arr[0].to_i,
                        "city"=>arr[1],
                        "province"=>arr[2],
                        "lat"=>arr[3].to_f,
                        "lng"=>arr[4].to_f,
                        "ele"=>arr[5].to_f,
                        "airP"=>arr[6].to_f
                    }
                end  
            end
            
        rescue Exception => e
            MoosasUtils.rescue_log(e)
            p "加载气象数据失败"
        end
    end

    def self.update_weather_stations_data(city,write=true)
        #更新气象数据数据站点参数，先加载再更新
        @stations[city[0]]={"sid"=>city[0].to_i,
                        "city"=>city[1],
                        "province"=>city[2],
                        "lat"=>city[3].to_f,
                        "lng"=>city[4].to_f,
                        "ele"=>city[5].to_f,
                        "airP"=>city[6].to_f}
        if write
            begin
                File.open(MPath::DB+"dest_station.csv","w+") do |file|
                    @stations.values.each{ |city_str| file.write(city_str.values.join(',')+"\n") }
                end
            rescue Exception => e
                MoosasUtils.rescue_log(e)
                p "写入气象数据失败"
            end
        end
    end

    def self.load_singleton()
        MoosasWeather.singleton = MoosasWeather.new
        if MoosasWeather.station_id == nil
            MoosasWeather.station_id = "545110"
        end
        MoosasWeather.singleton.get_city_station_weather_data(MoosasWeather.station_id)
        $weather = MoosasWeather.singleton
    end

    #返回气象数据
    def self.get_weather_stations()
        ret = Hash.new
        @stations.each do |k,v|
            if ret[v["province"]] == nil
                ret[v["province"]] = []
            end     
            ret[v["province"]].push(v)
        end
        return ret
    end

    def self.get_all_stations_id()
        ids =  []
        @stations.each do |k,v|
            ids.push(v["sid"])
        end
        return ids 
    end

    def initialize()
    end

    def self.include_epw_file()
        chosen_file = UI.openpanel("Open Epw File", "c:/", "Epw Files|*.epw;*.csv;||")
        if chosen_file != nil
            city_name = UI.inputbox(["城市名称"],["城市名称"], "请输入城市名称")[0]
            location = self.execute_MoosasWeather(chosen_file,city_name)
            self.load_weather_stations_data
            return location
        end
    end
    def self.execute_MoosasWeather(epw_file,cityname,pwd=MPath::PYTHON)
        Dir.chdir pwd
        code = ["from MoosasPy.weather import includeEpw"]
        code += ["from MoosasPy.utils import path"]
        code += ["import time"]
        code += ["sid=includeEpw(r\"#{epw_file}\",\"#{cityname}\")"]
        code += ["with open(path.tempDir+'\\sid.txt','w+') as f:"]
        code += ["    f.write(str(sid))"]
        code += ["time.sleep(0.1)"]
        begin
            MoosasUtils.exec_python("includeEpw.pyw",code,true)
            File.open(MPath::TEMP+"sid.txt","r") do |file|
                sid=file.gets
                return sid
            end
        rescue => e
            MoosasUtils.rescue_log(e)
            return nil
        ensure
            Dir.chdir File.dirname(__FILE__)
        end
    end

    def get_climate_zone(temperture)
        '''
        《民用建筑设计统一标准》GB 50352 《建筑气候区划标准》GB 50178规定建筑气候区划;
        《民用建筑热工设计规范》GB 50176规定建筑热工设计分区;
        MOOSAS采用GB 50176规定的建筑热工设计分区,主要体现在气象基本要素对建筑物及围护结构的保温隔热设计的影响。
        建筑热工设计分区用累年最冷月（即1月）和最热月（即7月）平均温度作为分区主要指标，
        累计日平均温度≤5度和≥25度的天数作为辅助指标。

        '''
        doy = [31,28,31,30,31,30,31,31,30,31,30,31]
        (1..11).to_a.each{ |mon| doy[mon] = doy[mon] + doy[mon-1]  }
        temperture = temperture.each_slice(24).to_a.map{ |day| day.sum / day.length } #日平均温度
        tmin_m = temperture[0,doy[0]].sum / temperture[0,doy[0]].length #最冷月平均温度——1月
        tmax_m = temperture[doy[5],doy[6]].sum / temperture[doy[5],doy[6]].length #最热月平均温度——7月
        d_5 = temperture.map{ |day| 1 if day<5 }.count(1) # 累计日平均温度≤5度
        d_25 = temperture.map{ |day| 1 if day>25 }.count(1) # 累计日平均温度≥25度

        #优先主要指标
        if tmin_m<=-10 
            return "climate_zone1"
        elsif tmin_m<=0 
            return "climate_zone2"
        elsif tmin_m<=10 and tmax_m>25 and tmax_m<=30 
            return "climate_zone3"
        elsif tmin_m>10 and tmax_m>25 and tmax_m<=29 
            return "climate_zone4"
        elsif tmin_m>0 and tmin_m<=13 and tmax_m>18 and tmax_m<=25 
            return "climate_zone5"
        end

        #其次次要指标
        if d_5>=145 
            return "climate_zone1"
        elsif d_5>=90 
            return "climate_zone2"
        elsif d_25>=40 and d_25 <110 
            return "climate_zone3"
        elsif d_25 <200 
            return "climate_zone4"
        else 
            return "climate_zone5"
        end
    end

    #根据气象站的id加载气象数据
    def get_city_station_weather_data(sid)
        #if @station_id == sid
        #    return @weather_data
        #end

        @station_id = sid
        @station_info = MoosasWeather.stations[sid]
        @weather_data = []
        begin
            File.open(MPath::WEATHER+"#{sid}.csv","r") do |file|
                while line = file.gets  
                    arr = line.split(',')
                    @weather_data.push(
                        {
                            "t"=>arr[3].to_f,
                            "d"=>arr[4].to_f,
                            "gt"=>arr[7].to_f,
                            "p"=>arr[11].to_f,
                            "rt"=>arr[5].to_f,
                            "ws"=>arr[9].to_f,
                            "wd"=>arr[10].to_f
                        })  #温度、含湿量、地表温度、气压强度、水平总辐射、风速、风向
                end  
            end

            #在模型中存储城市数据
            #MoosasMeta.set_city(pn+","+sid)
        rescue Exception => e
            MoosasUtils.rescue_log(e)
            p "加载气象站点的数据失败"
        end
        @climate_zone = self.get_climate_zone(@weather_data.map{ |day| day["t"] })
        return @weather_data
    end

    def get_weather_in_days()
        days = []
        dN = @weather_data.length / 24 #获取天数
        for d in 0..dN-1 do
            days.push(@weather_data[24*d..24*d+23])
        end
        return days
    end

    ''' 
        计算夜间室外平均温度
    '''
    def calculate_ave_out_tem_night(day,workStart, workEnd)
        arr = day[0..workStart-2] + day[workEnd-1..23]
        ave = 0
        arr.each do |a|
            ave += a["t"]
        end
        return ave / arr.length
    end


    #初始化冬夏季时间
    def init_summer_winter_day_number(settings)
        t = Time.new(settings["year"], settings["sStartM"], settings["sStartD"])
        @sStartN = t.yday
        t = Time.new(settings["year"], settings["sEndM"], settings["sEndD"])
        @sEndN = t.yday
        t = Time.new(settings["year"], settings["wStartM"], settings["wStartD"])
        @wStartN = t.yday
        t = Time.new(settings["year"], settings["wEndM"], settings["wEndD"])
        @wEndN = t.yday
    end

    #计算当前日处于什么季节
    def calculate_day_type(d)
        #夏季
        if d >= @sStartN and d <= @sEndN
            return 1
        end
        #冬季
        if d >= @wStartN or d <= @wEndN
            return 2
        end
        return 0
    end

    '''
    def self.get_year_enthalpy()
        ens = []
        #myFile = File.new("C:/Users/dell/Desktop/en.csv","w");  
    
        @weather_data.each do |w|
            #ens.push(MoosasThermalLoad.calculate_enthalpy_using_absolute_humandity(w["t"],w["d"]))
            e = MoosasThermalLoad.calculate_enthalpy_using_absolute_humandity(w["t"],w["d"])
            ens.push(e)
            #myFile.puts(e)
            #p e
        end
        #myFile.close
        ens
    end
    '''

    def get_station_id
        return @station_id
    end

    def to_array()
        jsa = []
        @weather_data.each do |wd|
            a = [wd["t"]]#,wd["d"],wd["gt"],wd["p"],wd["rt"],wd["ws"],wd["wd"]]
            jsa.push(a)
        end
        return jsa
    end

    def to_json_string()
        jsa = []
        @weather_data.each do |wd|
            a = "{\"t\":#{wd["t"]},\"d\":#{wd["d"]},\"gt\":#{wd["gt"]},\"p\":#{wd["p"]},\"rt\":#{wd["rt"]},\"ws\":#{wd["ws"]},\"wd\":#{wd["wd"]}}"
            jsa.push(a)
        end
        js = "[" + jsa.join(",")+ "]"
    end

end