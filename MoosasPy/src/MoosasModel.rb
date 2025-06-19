
#用于封装模拟所需要的所有数据：气象、材质、场地、几何数据
module MoosasConstant 
#    #WIN_U = 0.3
#    #WALL_U = 1.7
#    #WIN_SHGC = 0.4

    WIN_U = 2.4
    WALL_U = 0.5
    WIN_SHGC = 0.6
#
#
end

class MoosasModel
    Ver='0.6.3'
    attr_accessor :spaces, :settings, :weather ,:shading
    def initialize(ss,shd=nil)
        @spaces = ss
        @shading = []

        #一些设定数据
        @settings = {
            "year"=>2018,
            "sStartM" => 5,
            "sStartD" => 21,
            "sEndM" => 9,
            "sEndD" => 20,
            "wStartM" => 11,
            "wStartD" => 16,
            "wEndM" => 3,
            "wEndD" => 15,
            "workEnd" => 18,
            "workStart" => 9,
            "aoute" => 16.8,   #屋顶对流换热系数 
            "beta2" => 1.5,   #冬季周末修正系数
            "afat" => -1.83,   #周末修正系数计算所需常数
            "afas" => 2.16,    #周末修正系数计算所需常数
            #"AC_T" => 26.0,     #空调控制温度
            "AC_H" => 40.0,     #空调控制相对湿度,0.4 == 40%
            #"HT_T" => 22.0,     #冬季采暖控制温度
            #PPSM = 0.111     #每平米人数
            #"AVE_HM" => 13.653,     #人员散热
            #LIG_GAIN = 15.0     #灯光散热
            #AVE_EQ = 11.67     #设备散热
            #"ACR" => 0.7,     #渗透换气次数
            #"NITEV" => 1,      #夜间通风换气系数
            "AVE_FA" => 30,     #人均新风
            "AOUT" => 23.3,     #外表面对流换热系数
            "HTTHSFCO" => 0.75,     #内外区绝热强度系数
            "TERML_FORM" => 1,      #末端形式：定风量全空气、变风量全空气、风机盘管+新风、全水
            "LIG_CONTROL" => 2,     #照明控制方式：开关调节、连续调节
            "SYSTEM_SET" => 2,      #系统配对：夏季冷源+冬季热源+冬季冷源
            "VENAT_AC_NIGHT" => 0,     #空调季是否夜间通风
            "VENAT_HT_NIGHT" => 0,     #采暖季是否夜间通风
            "E" => 0.55     #表面辐射吸收率
        }

        load_weather_data()
        load_material_data()
        assign_material($rad_lib)
    end
    def %(id)
        @spaces.each{|sp| 
            if sp.id=id 
                return sp
            end
        }
        return nil
    end
    
    #加载气象数据
    @weather = nil
    def load_weather_data()
        @weather  = MoosasWeather.singleton
        #@weather = MoosasWeather.new
        @weather.init_summer_winter_day_number(@settings)
        #@weather.get_city_station_weather_data("54511")
    end

    def load_material_data()
        $rad_lib=[]
        begin
            File.open(MPath::DB+"rad_material_lib.csv","r") do |file|
                line = file.gets 
                while line = file.gets  
                    arr = line.chomp.split(',')
                    $rad_lib.push(MoosasMaterial.new(arr))
                end  
            end 
        rescue Exception => e
            MoosasUtils.rescue_log(e)
            p "加载材质数据失败"
        end
    end

    def assign_material(mat_lib)
        mofaces=self.get_all_face
        mofaces.each{|mf| mf.assign_material(mat_lib)}
    end

    def get(key)
        return @settings[key]
    end

    #获取建筑空间总面积
    def get_total_area()
        if @total_area == nil
            #计算建筑空间总面积
            @total_area = 0
            @spaces.each do |s|
                @total_area += s.area_m
            end
        end
        return @total_area
    end

    def backup
        @b_settings = @settings.clone
        @spaces.each do |s|
            s.backup
        end
    end

    def restore
        @settings = nil
        @settings = @b_settings
        @spaces.each do |s|
            s.restore
        end
    end

    def get_all_bounds
        bounds = []
        @spaces.each do |s|
            bounds += s.bounds
        end
        return bounds
    end

    def get_all_bounds_in_direction()
        all_bounds = self.get_all_bounds

        bounds_in_dir = [[],[],[],[]]  #南、西、北、东

        all_bounds.each do |b|
            dir_i = b.get_orientation()
            bounds_in_dir[dir_i].push b
        end
        return bounds_in_dir
    end

    def get_all_bounds_info_in_direction()
        bounds_info = []
        all_bs = self.get_all_bounds_in_direction()
        all_bs.each do |bs|
            bis = []
            bs.each do |b|
                bis.push [b.wwr,b.settings]
            end
            bounds_info.push bis
        end
        return bounds_info
    end

    def get_all_face
        faces = Hash.new()
        @spaces.each{|s|
            s.get_all_face.each{|mf|
            faces[mf.id]=mf
            }
        }
        @shading.each{|mf|
            faces[mf.id]=mf
        }
        return faces.values
    end

    def get_all_rad_material
        mofaces=self.get_all_face
        all_mat=Hash.new(0)
        mofaces.each{|mf| 
            if mf.material==nil
                mf.assign_material($rad_lib)
            end
            all_mat[mf.material]+=1
        }
        return all_mat
    end

    def pack_data(is_detail=false)
        spaces_data = []

        building_height = 0.0
        floor_height = 0.0
        @spaces.each do |s|
            spaces_data.push s.pack_data(is_detail)
            sh = s.floor[0].height * 0.0254 + s.height_m
            if building_height < sh
                building_height = sh
            end
            floor_height += s.height_m
        end

        floor_height /= @spaces.length
        model_data ={
            "spaces" => spaces_data,
            "area" => self.get_total_area(),
            "height" =>building_height,
            "floor_height" => floor_height
        }
        return model_data
    end
    def print_bounds_points
        p "bounds informaton:"
        @spaces.each do |s|
            s.print_bounds_points
        end
    end

    def change_space_parameters(params)
        space_id=params[0]
        attribute=params[1]
        space_data=params[2]
        @spaces.each do |s|
            if s.id==space_id
                s.settings[attribute]=space_data
                break
            end
        end
    end
end
#描述未被结构化的面
class MoosasGeometry
    attr_accessor :face,:transformation,:id
    def initialize(f,t,i)
        @face=f
        @transformation=t
        @id=i
    end
end
#描述（可能）用于计算的材质
class MoosasMaterial
    attr_accessor :name,:category, :rad_mat ,:bes_mat 
    '''
    category 为按照名称匹配MAT_REF中的一种
    rad_mat<dict> 为采光模拟材质，根据RADIANCE标准定义：
         type=> plastic(不透明材质，包括金属),trans(半透明材质，例如透光大理石、磨砂玻璃，颜色由反射光决定),glass(光滑玻璃材质，颜色由透射光决定)
         R=>    红反(plastic/trans)/红透(glass)
         G=>    绿反(plastic/trans)/绿透(glass)
         B=>    蓝反(plastic/trans)/蓝透(glass)
         spec=> 高光
         rough=>粗糙度
    材质库存储于db/rad_material_lib.csv
    category,subname(用于搜索,无法匹配则识别为空),rad_type,R,G,B,spec,rough

    bes_mat<dict> 为能耗计算材质
    材质库存储于db/erengy_material_lib.csv
    MoosasFace中记载的mat根据MAT_REF索引至本类实例，请根据需要更新
    '''
    MAT_REF={
            "plaster"=>"plaster",
            "paint"=>"praint",
            "praint"=>"praint",
            "glazing"=>"glazing",
            "glass"=>"glazing",
            "translucent"=>"glazing",
            "fencing"=>"glazing",
            "wood"=>"cladding",
            "timber"=>"cladding",
            "brick"=>"brick",
            "cladding"=>"cladding",
            "stone"=>"stone",
            "marble"=>"stone",
            "concrete"=>"concrete",
            "aluminium"=>"aluminium",
            "steel"=>"steel",
            "metal"=>"metal",
            "default"=>"default"
    }

    def initialize(params)
        @name=params[1]
        @category=params[0]
        @rad_mat={
            "type"=>params[2],
            "R"=>params[3].to_s,
            "G"=>params[4].to_s,
            "B"=>params[5].to_s,
            "spec"=>params[6].to_s,
            "rough"=>params[7].to_s
        }
        @bes_mat=nil #还未实装
    end
    def self.search_material(name_str,mat_lib)
        # 转义为标准category,忽略大小写
        category=nil
        idx=nil
        name_str=name_str.split(" ").join("_")
        MoosasMaterial::MAT_REF.keys.each{|cat| 
            if name_str.scan(/#{cat.to_s}/i).length >0
                category=MoosasMaterial::MAT_REF[cat] 
            end
            }
        if category!=nil
            # 识别二级词,忽略大小写
            for i in 0..mat_lib.length-1
                if mat_lib[i].category==category
                    if mat_lib[i].name=="-"
                        idx=i 
                    else
                        if name_str.scan(/#{mat_lib[i].name.to_s}/i).length >0
                            idx=i
                        end
                    end
                end
            end     
        end
        return idx
    end

end

#描述每一个最小空间
class MoosasSpace
    attr_accessor :floor,:height, :bounds,:ceils, :is_outer, :id, :area_m, :height_m, :settings, :neighbor, :internal_wall

    def initialize(f,h,c,b)
        @multifloor = f
        @floor=f
        @height = h
        @ceils = c
        @bounds = b
        @id = nil
        @neighbor={}
        @area_m = @floor.map{|fl| fl.area_m}.sum()
        @height_m = @height * MoosasConstant::INCH_METER_MULTIPLIER
        @internal_wall=[]
        #一些设定数据s
        @settings = {
            "zone_name"=> "Space",

            "zone_summerrad"=> nil, #夏季辐射得热，单位kwh
            "zone_winterrad"=> nil, #冬季辐射得热，单位kwh

            "zone_standard"=>nil
        }
        self.apply_settings(
                MoosasStandard.search_template([
                    MoosasStandard::STANDARDNAME[$ui_settings["selectBuildingType"]],
                    MoosasStandard::STANDARDNAME[$ui_settings["selectStandard"]]
                    ])[0]
            )
        #根据空间参数计算id
        @id='s_'+@area_m.round().to_s+@height_m.round().to_s+@bounds.length.to_s
        @id += @bounds.map{|edge| (edge.wwr*10).round()}.sort.join("")
        @id += self.get_weight_center().map{ |v| v.round().to_s  }.join("")
        @settings["zone_name"]= "Space"+id.to_s[2,4]
        
    end

    def %(id)
        self.get_all_face.each{|face| 
            if face.id=id 
                return face
            end
        }
        return nil
    end

    def calculate_zone_radation(model)

        @settings["zone_summerrad"] = 0.0
        @settings["zone_winterrad"] = 0.0
        #MoosasRender.hide_all_face
        #self.get_all_face().each{|mf| mf.face.hidden = false}
        #MoosasRender.hide_glazing
        model = self.get_all_face.map{ |f| f.face  }

        @bounds.each{ |b| 
            b.calculate_radiation(model) 
            @settings["zone_summerrad"] += b.settings["summer_rad"] 
            @settings["zone_winterrad"] += b.settings["winter_rad"] 
        }
        @settings["zone_summerrad"]=@settings["zone_summerrad"].round(2)
        @settings["zone_winterrad"]=@settings["zone_winterrad"].round(2)
        #MoosasRender.show_all_face
    end

    def apply_settings(setting_key)
        setting_dict = $template[setting_key]
        if @settings["zone_standard"] == nil
            @settings["zone_standard"]=setting_key
        end
        setting_dict.keys.each{ |key| 
            if @settings[key] == nil
                @settings[key] = setting_dict[key]
            elsif @settings[key] == $template[@settings["zone_standard"]][key]
                @settings[key] = setting_dict[key]
            end
        }
        @settings["zone_standard"]=setting_key
    end

    def visualize_orientation(entities)
        for w in @bounds
            entities=w.visualize_factor(entities)
        end
        return entities
    end

    def get_weight_center()
        floor_wca = @floor.map{|fl| fl.get_weight_center()}
        floor_wc=[0,0,0]
        floor_wca.each{|wca| 
            floor_wc[0]+=wca[0]
            floor_wc[1]+=wca[1]
            floor_wc[2]+=wca[2]
        }
        floor_wc=floor_wc.map{|target| target/floor_wca.length}
        return floor_wc
    end

    def construct_space_volume(entities)
        begin
            pts = @floor[0].face.outer_loop.vertices.map {|v|
                        pt = v.position
                        [pt.x,pt.y,pt.z+10000]
                }
        _face=entities.add_face(pts)
            if _face.normal[2]<0
                _face.reverse!
            end
            _face.pushpull(@height)
            return entities
        rescue
            return entities
        end
    end

    def get_quick_location()
        loc=[0,0,0]
        @floor.each{|fc| 
            fc.face.outer_loop.vertices.each {|v|
                        pt = v.position
                        loc[0]+=pt.x
                        loc[1]+=pt.y
                        loc[2]+=pt.z
                }
            }
        loc=loc.map{|k|k/@floor.map{|fc| fc.face.outer_loop.vertices.length}.sum()}
        return loc
    end

    def assign_type_directly(groundHeight)
        if @floor==nil or @ceils==nil or @bounds==nil
            p "_floorNil" if @floor==nil
            p "_ceilNil" if @ceils==nil
            p "_boundNil" if @bounds==nil
            return nil
        end
        @floor.each{|fl|
            fl.type = MoosasConstant::ENTITY_FLOOR
            fl.type = MoosasConstant::ENTITY_GROUND_FLOOR if fl.height<=groundHeight+1.0
            fl.glazings.each{|fl_g|
                fl_g.type = MoosasConstant::ENTITY_SKY_GLAZING
                fl_g.type = MoosasConstant::ENTITY_IGNORE if fl_g.face.material.alpha < 0.2 #空气墙
                fl_g.shading.each{|fl_g_shading| fl_g_shading.type = MoosasConstant::ENTITY_SHADING}
            }
        }

        @ceils.each{|ci|
            ci.type = MoosasConstant::ENTITY_ROOF if ci.type == nil
            ci.glazings.each{|fl_g|
                fl_g.type = MoosasConstant::ENTITY_SKY_GLAZING
                fl_g.type = MoosasConstant::ENTITY_IGNORE if fl_g.face.material.alpha < 0.2 #空气墙
                fl_g.shading.each{|fl_g_shading| fl_g_shading.type = MoosasConstant::ENTITY_SHADING}
            }
        }

        @bounds.each do |b|
            if b.is_internal_edge==true
                b.walls.each do |w|
                    w.type = MoosasConstant::ENTITY_INTERNAL_WALL
                end
                b.glazings.each do |g|
                    g.type = MoosasConstant::ENTITY_INTERNAL_GLAZING
                    g.type = MoosasConstant::ENTITY_IGNORE if g.face.material.alpha < 0.2 #空气墙
                    g.shading.each{|fl_g_shading| fl_g_shading.type = MoosasConstant::ENTITY_SHADING}
                end

            else
                b.walls.each do |w|
                    w.type = MoosasConstant::ENTITY_WALL
                end
                b.glazings.each do |g|
                    g.type = MoosasConstant::ENTITY_GLAZING
                    g.type = MoosasConstant::ENTITY_IGNORE if g.face.material.alpha < 0.2 #空气墙
                    g.shading.each{|fl_g_shading| fl_g_shading.type = MoosasConstant::ENTITY_SHADING}
                end
            end
        end

        @internal_wall.each do |inw|
            inw.type = MoosasConstant::ENTITY_INTERNAL_WALL
        end
    end

    def get_all_face()
        # return as MoosasFaces
        faces = []
        @floor.each do |f|   
            faces.push(f)
        end
        @ceils.each do |c|
            faces.push(c)
        end
        @bounds.each do |b|
            b.walls.each do |w|
                faces.push(w)
            end
        end
        @internal_wall.each{|mf|
            faces.push(mf)}
        faces=faces.map{|f| [f,f.glazings]}.flatten
        faces=faces.map{|f| [f,f.shading]}.flatten
        return faces.flatten
    end

    def backup
        @b_settings = @settings.clone
        @floor.each do |f| 
            f.backup
        end
        @ceils.each do |c|
            c.backup
        end
        @bounds.each do |b|
            b.backup
        end
        return nil
    end

    def restore
        @settings = nil
        @settings = @b_settings
        @floor.each do |f| 
            f.restore
        end
        @ceils.each do |c|
            c.restore
        end
        @bounds.each do |b|
            b.restore
        end
        return nil
    end

    def pack_data(is_detail)
        s_info={
            "id"=>@id,
        }
        @settings.keys.each{|key| s_info[key]=@settings[key]}
        #p s_info

        s_data = []
        self.get_all_face.each{ |f| s_data.push f.pack_data(is_detail) }
        
        s_data=[s_info,s_data]
        return s_data
    end

    #def get(key)
    #    return @settings[key]
    #end

    #def infer_type
    #    @is_outer = false
    #    #只要有一条边在外面，就认为是外区
    #    @bounds.each do |b|
    #        if not b.is_internal_edge
    #            @is_outer = true
    #            break
    #        end
    #    end
    #    #@is_top = false
    #    #@is_ground = false
    #end

    #def assign_vertical_face_normal()
    #    floor_wc=self.get_weight_center()
    #    @bounds.each do |b|
    #        b.walls.each do |w|
    #            pt = w.transformation * w.face.vertices[0].position
    #            if normal_need_reverse(floor_wc,pt,w.normal)
    #                w.normal = [0-w.normal.x, 0-w.normal.y, 0-w.normal.z]
    #            end
    #        end
    #        b.glazings.each do |g|
    #            pt = g.transformation * g.face.vertices[0].position
    #            if normal_need_reverse(floor_wc,pt,g.normal)
    #                g.normal = [0-g.normal.x, 0-g.normal.y, 0-g.normal.z]
    #            end
    #        end
    #    end
    #end

    #def normal_need_reverse(wc,pt,normal)
    #    deltaX = wc.x - pt.x
    #    deltaY = wc.y - pt.y
    #    val = normal.x * deltaX + normal.y * deltaY
    #    if val > 0
    #        return true #[0-normal.x, 0-normal.y, 0-normal.z]
    #    else
    #        return false
    #    end 
    #end

    #def print_info
    #    p "floor area = #{@area_m}"
    #    p "floor type = #{@floor[0].type}"
    #    #p "floor height = #{@floor.height * MoosasConstant::INCH_METER_MULTIPLIER}"
    #    p "story height = #{@height_m}"
    #    
    #    p "bounds number = #{@bounds.length}"
    #    bi = 0
    #    @bounds.each do |b|
    #        bi += 1
    #        p "     #{bi}: length=#{b.get_length_in_m()},  wwr=#{b.wwr}, normal=#{b.normal},ids=#{b.get_vface_ids}"
    #        #p " settings=#{b.settings}"
    #    end
    #    p "ceils number = #{@ceils.length}"
    #    ci = 0
    #    @ceils.each do |c|
    #        ci += 1
    #        p "     #{ci}: area=#{c.area_m}, type=#{c.type}"
    #        #p "     settings=#{c.settings}"
    #    end
    #end

    #def print_bounds_points
    #    b_data = []
    #    @bounds.each do |b|
    #        b_data.push b.get_edge_point_in_meter
    #    end
    #    p b_data
    #end
end

#描述每个空间的边
class MoosasEdge
    attr_accessor  :edge, :walls, :glazings, :wwr, :is_internal_edge, :area_m, :cp, :normal,:settings

    def initialize(e,height,require_infer=true)
        @edge = e
        @walls = []
        @glazings = []
        @is_internal_edge = false

        if require_infer
            @area_m = get_length() * height * MoosasConstant::INCH_METER_MULTIPLIER_SQR
            set_edge_center_point(height)
            #set_edge_normal()
        else

        end
        #一些设定数据
        @settings = {
            "opaque" => [0,MoosasConstant::WALL_U],                #不透光结构热工参数，[材质的id，U值]
            "glazing" => [0,MoosasConstant::WIN_U,MoosasConstant::WIN_SHGC,0.6],         #透光结构热工参数，[材质的id，U值，SHGC值,可见光透过率T值]
            "summer_rad"=>0.0,          #冬季立面太阳辐射得热，总热量
            "winter_rad"=>0.0           #夏季立面太阳辐射得热，总热量
        }
    end

    def calculate_radiation(model)
        @settings['summer_rad'] = 0.0
        @settings['winter_rad'] = 0.0
        summer_cum_sky=$current_CumSky.get_cum_sky(normal,$current_CumSky.summer_CumSky)
        winter_cum_sky=$current_CumSky.get_cum_sky(normal,$current_CumSky.winter_CumSky)
        #connected_faces = @walls.map{|w| w.face.all_connected}.flatten
        #model = []
        #MMR.traverse_faces(connected_faces) do |e,path|
        #    model.push(e)
        #end
        #connected_faces.each{ |f| f.hidden = false } 
        @glazings.each{|g|
            #g.face.hidden = true
            position = Geom::Point3d.new(g.get_weight_center())
            @settings['summer_rad'] += MoosasRadiance.calculate_position_radiance(position,model,summer_cum_sky) * g.area_m
            @settings['winter_rad'] += MoosasRadiance.calculate_position_radiance(position,model,winter_cum_sky) * g.area_m
            #g.face.hidden = false
        }
        #total_area = @glazings.map{|g| g.area_m}.sum
        #@settings['summer_rad'] /= total_area
        #@settings['winter_rad'] /= total_area
        #MoosasRender.show_all_face
    end

    def visualize_factor(entities)
        origin = Geom::Point3d.new(@walls[0].get_weight_center)
        vec = Geom::Vector3d.new(@normal)
        vec.length=20
        entities.add_face([
            origin,
            origin+vec+vec+vec+Geom::Vector3d.new([0,0,5]),
            origin+vec+vec+vec+vec,
            origin+vec+vec+vec+Geom::Vector3d.new([0,0,-5]),
        ])
        return entities
    end
    def set_len(length)
        @len=length
    end
    
    def assign_value_directly(wwr,normal,len_m,height_m)
        @area_m = len_m * height_m
        @wwr = wwr
        @normal = normal
        @len_m = len_m
    end

    #根据墙体的面推断这条边的类型，只要存在一个面是内部面的类型，就推断为内部边
    def infer_type
        @walls.each do |w|
            if w.type == MoosasConstant::ENTITY_INTERNAL_WALL
                @is_internal_edge = true
                return
            end
        end
        @glazings.each do |g|
            if g.type == MoosasConstant::ENTITY_INTERNAL_GLAZING
                @is_internal_edge = true
                return
            end
        end
    end

    #获取这个边所代表的面的中点
    def set_edge_center_point(floor_height)
        cx = (@edge[0].x + @edge[1].x)/2
        cy = (@edge[0].y + @edge[1].y)/2
        cz = (@edge[0].z + @edge[1].z + floor_height )/2
        @cp  = [cx,cy,cz]
    end

    #获取代表正面的法向量
    def set_edge_normal()
        len = get_length()
        dx = (@edge[1].x - @edge[0].x) / len   #进行归一化处理
        dy = (@edge[1].y - @edge[0].y) / len
        @normal = [0-dy,dx,0]
    end

    def reverse_normal()
        @normal = [0-@normal[0],0-@normal[1],@normal[2]]
    end

    def get_length
        if @len != nil
            return @len
        end
        @len = ( (@edge[0].x - @edge[1].x) ** 2 + (@edge[0].y - @edge[1].y) ** 2 ) ** 0.5
        return @len
    end

    def get_length_in_m
        if @len_m != nil
            return @len_m
        end
        @len_m = get_length() * MoosasConstant::INCH_METER_MULTIPLIER
        return @len_m
    end

    def get_vface_ids
        ids = []
        @walls.each do |w|
            ids.push(w.face.entityID)
        end
        @glazings.each do |g|
            ids.push(g.face.entityID)
        end
        ids
    end

    def backup
        @b_wwr = @wwr
        @b_settings = {
            "opaque" => @settings["opaque"].clone,                
            "glazing" => @settings["glazing"].clone        
        }
        @walls.each do |w|
            w.backup
        end
        @glazings.each do |g|
            g.backup
        end
    end

    def restore
        @wwr = @b_wwr
        @settings = nil
        @settings = @b_settings
        @walls.each do |w|
            w.restore
        end
        @glazings.each do |g|
            g.restore
        end
    end

    #根据法向量，计算墙体朝向
    PI_1_4 = 0.7071067811865476  # pi/4
    PI_3_4 = -0.7071067811865476  # pi/4*3
    def get_orientation
        if @ori == nil
            normal_len = (@normal[0] ** 2 + @normal[1]**2) ** 0.5
            if normal_len == 0
                normal_len = 1.0
            end
            cosx = @normal[0] / normal_len
            if cosx >= PI_1_4
                @ori = MoosasConstant::ORIENTATION_EAST
            elsif cosx <= PI_3_4
                @ori = MoosasConstant::ORIENTATION_WEST
            else
                if @normal[1] > 0
                     @ori = MoosasConstant::ORIENTATION_NORTH
                else
                     @ori = MoosasConstant::ORIENTATION_SOUTH
                end 
            end
        end
        return @ori 
    end

    def get_edge_point_in_meter
        p1 = [edge[0].x.to_m,edge[0].y.to_m,edge[0].z.to_m]
        p2 = [edge[1].x.to_m,edge[1].y.to_m,edge[1].z.to_m]   
        return [p1,p2]
    end
end

#描述每个面
class MoosasFace
    attr_accessor :face, :glazings, :shading, :height, :transformation, :area, :wc, :type,:id, :normal, :area_m, :settings,:material


    def initialize(face, transformation, area,nor=nil,id=0)
        @face = face
        @transformation = transformation
        @area = area
        @normal = nor
        calculate_height() if face != nil
        @wc = nil
        @type = nil
        @material=nil
        @glazings=[]
        @shading=[]
        @id = id
        @area_m = area * MoosasConstant::INCH_METER_MULTIPLIER_SQR
        @settings = {"u"=>MoosasConstant::WALL_U}
    end

    def assign_material(mat_lib)
        mat_num=nil
        name_str=nil
        if @face.material!=nil
            #使用原名进行匹配
            name_str=@face.material.name
            mat_num=MoosasMaterial.search_material(name_str,mat_lib)
            if mat_num==nil
            #使用显示名进行匹配
                name_str=@face.material.display_name
                mat_num=MoosasMaterial.search_material(name_str,mat_lib)
            end
        end

        #若材质匹配失败，按默认以及类型处理
        if mat_num==nil
            case @type
            when MoosasConstant::ENTITY_FLOOR
                name_str="default_floor"
            when MoosasConstant::ENTITY_GROUND_FLOOR
                name_str="default_floor"
            when MoosasConstant::ENTITY_WALL
                name_str="default_wall"
            when MoosasConstant::ENTITY_INTERNAL_WALL
                name_str="default_wall"
            when MoosasConstant::ENTITY_PARTY_WALL
                name_str="default_wall"
            when MoosasConstant::ENTITY_SHADING
                name_str="default_wall"
            when MoosasConstant::ENTITY_GLAZING
                name_str="default_window"
            when MoosasConstant::ENTITY_INTERNAL_GLAZING
                name_str="default_window"
            when MoosasConstant::ENTITY_SKY_GLAZING
                name_str="default_window"
            when MoosasConstant::ENTITY_ROOF
                name_str="default_roof"
            else
                name_str="default_wall"
            end
            mat_num=MoosasMaterial.search_material(name_str,mat_lib)
        end
        @material=mat_num
    end

    def calculate_height
        @height = 0
        @face.vertices.each do |v|
            tp = transformation * v.position
            @height += tp.z
        end
        @height /= @face.vertices.length
    end

    def get_transformation_vs
        if @vs != nil
            return @vs
        end
        @vs = []
        @face.vertices.each do |v|
            tv = @transformation * v.position
            @vs.push [tv.x,tv.y]
        end
        return @vs
    end

    def get_transformation_vs_3d
        @vs_3d = []
        @face.vertices.each do |v|
            tv = @transformation * v.position
            @vs_3d.push [tv.x * 0.0254,tv.y * 0.0254,tv.z * 0.0254]
        end
        return @vs_3d
    end
    def centroid
        cx = 0
        cy = 0
        cz = 0
        fvs = @face.vertices
        fvs.each do |fv|
            tfv =  * fv.position.transform(@transformation)
            cx += tfv.x
            cy += tfv.y
            cz += tfv.z
        end
        cx /= fvs.length
        cy /= fvs.length
        cz /= fvs.length
        @wc = [cx,cy,cz]
        return Geom::Point3d.new(@wc)
    end

    def get_weight_center  #对水平面使用
        if @wc != nil
            return @wc
        end
        cx = 0
        cy = 0
        cz = 0
        if @face.outer_loop.convex?
            fvs = @face.vertices
            fvs.each do |fv|
                tfv = fv.position.transform(@transformation)
                
                cx += tfv[0]
                cy += tfv[1]
                cz += tfv[2]
            end
            cx /= fvs.length
            cy /= fvs.length
            cz /= fvs.length
        else
            mesh = @face.mesh
            polygons = mesh.polygons
            area = 0
            polygons.each do |pol|
                p1 = mesh.point_at(pol[0]).transform(@transformation)
                p2 = mesh.point_at(pol[1]).transform(@transformation)
                p3 = mesh.point_at(pol[2]).transform(@transformation)

                a = get_triangle_area(p1,p2,p3)
                area += a

                cx += a*(p1.x + p2.x + p3.x)
                cy += a*(p1.y + p2.y + p3.y)
                cz += a*(p1.z + p2.z + p3.z)
            end
            area = area * 3
            cx /= area
            cy /= area
            cz /= area
        end
        @wc = []
        [cx,cy,cz].each{ |v| 
                    if v.is_a?(Complex)  
                        @wc.push v.real
                    else
                        @wc.push v
                    end
                    }
        return @wc
    end

    def get_height_info
        hs = [] 
        @face.vertices.each do |fv|
            tfv = @transformation * fv.position
            hs.push tfv.z
        end
        return [hs.min,@height,hs.max]
    end

    def get_triangle_area(p1,p2,p3)
        a = p1.distance(p2)
        b = p2.distance(p3)
        c = p3.distance(p1)
        t = (a+b+c)/2
        s = (t * (t-a)*(t-b)*(t-c))**0.5
        return s
    end

    def get_transformation_mesh_polygons
        mesh = @face.mesh
        polygons = mesh.polygons
        pols = []
        polygons.each do |pol|
            p1 = @transformation * mesh.point_at(pol[0])
            p2 = @transformation * mesh.point_at(pol[1])
            p3 = @transformation * mesh.point_at(pol[2])
            pols.push([[p1.x,p1.y],[p2.x,p2.y],[p3.x,p3.y]])
        end
        return pols
    end

    def get_edges
        es = []
        @face.edges.each do |e|
            sp = @transformation * e.start.position 
            ep = @transformation * e.end.position 
            es.push([sp,ep])
        end
        return es
    end

    @be = nil
    def get_bottom_edge
        if @be != nil
            return @be
        end
        es = get_edges
        minHeight = Float::MAX
        es.each do |e|
            if e[0].z + e[1].z < minHeight
                minHeight = e[0].z + e[1].z
                @be = e
            end
        end
        return @be
    end

    def is_glazing
        if @face.material && @face.material.alpha < MoosasConstant::MATERIAL_ALPHA_THRESHOLD
            @settings["u"] = MoosasConstant::WIN_U
            @settings["s"] = MoosasConstant::WIN_SHGC
            return true
        else
            return false
        end
    end

    def backup
        @b_settings = @settings.clone
    end

    def restore
        @settings = nil
        @settings = @b_settings
    end

    def pack_data(is_detail)
        if is_detail == true
            f_data = [@id,@type,@area_m,@normal,self.get_transformation_vs_3d()]
        else
            f_data = [@id,@type,@area_m]
        end
    end
end




