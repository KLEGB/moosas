#封装标准用到的数据
class MoosasStandard
    Ver='0.6.3'
    
    '''
        "zone_wallU"=>            #外墙U值
        "zone_winU"=>             #外窗U值
        "zone_win_SHGC"=>         #外窗SHGC值
        "zone_c_temp"=>           #空调控制温度
        "zone_h_temp"=>           #采暖控制温度
        "zone_collingEER"=>       #空调能效比
        "zone_HeatingEER"=>       #空调能效比
        "zone_work_start"=>       #系统开启时间
        "zone_work_end"=>         #系统关闭时间
        "zone_ppsm"=>             #每平米人数
        "zone_pfav"=>             #人均新风量
        "zone_popheat"=>          #人员散热
        "zone_equipment"=>        #设备散热
        "zone_lighting"=>         #灯光散热
        "zone_inflitration"=>     #渗风换气次数
        "zone_nightACH"=>         #夜间换气次数
    '''
    if $language == 'Chinese'
        STANDARDNAME={
            "居住建筑"=>"RESIDENTIAL",
            "办公建筑"=>'OFFICE',
            "酒店建筑"=>'HOTEL',
            "学校建筑"=>'SCHOOL',
            "商场建筑"=>'COMMERCIAL',
            "剧院建筑"=>'OPERA',
            "医院建筑"=>'HOSIPITAL',
            "近零能耗建筑技术标准 GB/T 51350-2019"=>"GB/T51350-2019"
        }
    else
        STANDARDNAME={
            "Residence"=>"RESIDENTIAL",
            "Office"=>'OFFICE',
            "Hotel"=>'HOTEL',
            "School"=>'SCHOOL',
            "Commercial"=>'COMMERCIAL',
            "Opera"=>'OPERA',
            "Hosipital"=>'HOSIPITAL',
            "GB/T 51350-2019"=>"GB/T51350-2019"
        }
    end

    def self.load_building_template()
        $template = {}
        begin
            File.open(File.dirname(__FILE__)+"/../db/building_template.csv","r") do |file|  
                # 读取标题行，不带'zone_'的为temple的标签，否则为temple的值
                title = file.gets.strip().split(',')
                _key_tab,_value_tab=[],[]
                for i in 0..title.length-1
                    if title[i][0,5]!='zone_'
                        _key_tab.push(i)
                    else
                        _value_tab.push(i)
                    end
                end
                _name = _value_tab.map{ |num| title[num] }

                # 读取内容，根据_key_tab,_value_tab区分标签和值
                while line = file.gets  
                    arr = line.split(',')
                    _key = _key_tab.map{ |num| arr[num] }.join('_')
                    _value = _value_tab.map{ |num| arr[num] }
                    _template={}
                    for i in 0.._value.length-1
                        _template[_name[i]]=_value[i]
                    end
                    $template[_key]=_template
                end  
            end
            return $template
        rescue Exception => e
            MoosasUtils.rescue_log(e)
            p "加载建筑样板数据失败"
        end
    end

    def self.search_template(str_list)
        namelist = $template.keys.map{ |k| k }
        str_list.each{ |hint| 
            if namelist.length == 0
                return nil
            end
            namelist = namelist.map{|templatename| templatename if templatename.include?(hint)}
            namelist.compact!
        }
        #return namelist.map{|templatename| $template[templatename]}
        return namelist
    end
end