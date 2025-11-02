
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
    # Function:
    # Initializes the object with given spaces and optional shading data, sets up default simulation settings,
    # and loads necessary weather and material data for thermal and energy performance calculations.
    # 
    # Parameters:
    # ss : Array or Hash
    # A collection of space objects or definitions to be used in the simulation.
    # shd : Array or nil, optional
    # An optional list of shading elements. If not provided, defaults to an empty array.
    # 
    # Returns:
    # None
    # This constructor does not return a value. It initializes instance variables and loads external data.
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
    # """
    # Function
    # --------
    # load_weather_data
    # Initializes and loads weather data using the MoosasWeather singleton instance,
    # setting up summer/winter day numbers based on current settings.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value.
    # """
        @weather  = MoosasWeather.singleton
        #@weather = MoosasWeather.new
        @weather.init_summer_winter_day_number(@settings)
        #@weather.get_city_station_weather_data("54511")
    end

    def load_material_data()
    # """
    # Function
    # --------
    # load_material_data
    # Loads material data from a CSV file and initializes an array of MoosasMaterial objects.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value. It populates the global variable `$rad_lib` with instances of `MoosasMaterial`
    # created from the data in the CSV file. In case of failure, it logs the error and prints an error message.
    # """
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
    # """
    # Function
    # --------
    # Assigns materials from a material library to all faces in the object.
    # 
    # Parameters
    # ----------
    # mat_lib : object
    # A material library containing material definitions to be assigned.
    # The exact type depends on the expected format by `Face#assign_material`.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It performs material assignment as a side effect.
    # """
        mofaces=self.get_all_face
        mofaces.each{|mf| mf.assign_material(mat_lib)}
    end

    def get(key)
    # """
    # Function
    # --------
    # Retrieve the value associated with the specified key from the settings hash.
    # 
    # Parameters
    # ----------
    # key : object
    # The key whose associated value is to be retrieved from the internal settings hash.
    # 
    # Returns
    # -------
    # object
    # The value associated with the given key in the settings hash. Returns `nil` if the key is not present.
    # """
        return @settings[key]
    end

    #获取建筑空间总面积
    def get_total_area()
    # """
    # Function
    # ----------
    # get_total_area
    # Calculates and returns the total area of all spaces in the building. The value is cached
    # in the instance variable @total_area to avoid recalculation on subsequent calls.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Float or Integer
    # The total area of all spaces (in square meters). Returns the cached value if already computed.
    # """
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
    # """
    # Function
    # --------
    # Creates a backup of the current settings and propagates the backup operation to all associated spaces.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value.
    # """
        @b_settings = @settings.clone
        @spaces.each do |s|
            s.backup
        end
    end

    def restore
    # """
    # Function
    # --------
    # restore : None
    # Restores the current instance's settings and spaces to their previous backup states.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any arguments.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value.
    # """
        @settings = nil
        @settings = @b_settings
        @spaces.each do |s|
            s.restore
        end
    end

    def get_all_bounds
    # """
    # Function
    # ----------
    # get_all_bounds
    # Retrieves the combined bounds from all spaces in the instance.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # list of bounds
    # A list containing all bounds from each space in the `@spaces` collection.
    # The bounds from individual spaces are concatenated into a single flat list.
    # """
        bounds = []
        @spaces.each do |s|
            bounds += s.bounds
        end
        return bounds
    end

    def get_all_bounds_in_direction()
    # """
    # Function
    # --------
    # Organizes all boundary objects into groups based on their orientation/direction.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Array of Arrays
    # A 4-element array where each subarray contains boundary objects oriented in a specific direction:
    # - bounds_in_dir[0]: boundaries facing South
    # - bounds_in_dir[1]: boundaries facing West
    # - bounds_in_dir[2]: boundaries facing North
    # - bounds_in_dir[3]: boundaries facing East
    # Each boundary's direction index is obtained via its `get_orientation()` method.
    # """
        all_bounds = self.get_all_bounds

        bounds_in_dir = [[],[],[],[]]  #南、西、北、东

        all_bounds.each do |b|
            dir_i = b.get_orientation()
            bounds_in_dir[dir_i].push b
        end
        return bounds_in_dir
    end

    def get_all_bounds_info_in_direction()
    # """
    # Function
    # --------
    # Retrieve window-to-wall ratio and settings for all boundary surfaces in each directional group.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # list of lists of lists
    # A nested list structure containing window-to-wall ratios and settings for each boundary surface.
    # The outer list corresponds to directional groups; the middle list corresponds to boundary surfaces
    # within a direction; the inner list contains two elements: [wwr (float), settings (dict/object)].
    # """
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
    # """
    # Function
    # --------
    # Retrieve all unique faces from spaces and shading elements.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Array
    # An array of unique face objects (without duplicates) collected from all spaces
    # and shading elements. Each face is represented as an object with an `id` attribute
    # used to ensure uniqueness in the internal hash map.
    # """
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
    # """
    # Function
    # --------
    # Retrieve all radiation materials from faces in the model.
    # 
    # This method collects all faces using `get_all_face`, ensures each face has a material assigned
    # (by assigning one from the global radiation library if missing), and counts the occurrence
    # of each material across all faces.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # Hash
    # A hash where keys are material objects (or names) and values are integers representing
    # the number of faces that use each material. If a face had no material, it is assigned
    # one from the global `$rad_lib` before counting.
    # """
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
    # """
    # Function
    # --------
    # Packs space-related data into a structured hash, optionally including detailed information.
    # 
    # Parameters
    # ----------
    # is_detail : bool, optional
    # If true, includes detailed data in each space's packed result. Defaults to False.
    # 
    # Returns
    # -------
    # Hash
    # A hash containing:
    # - "spaces" : Array of packed space data (Hash objects), each representing individual space details.
    # - "area" : Total floor area of all spaces, calculated via `get_total_area()`.
    # - "height" : Maximum building height in meters, derived from the highest space (including floor thickness converted from inches to meters).
    # - "floor_height" : Average floor-to-floor height across all spaces in meters.
    # """
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
    # """
    # Function
    # --------
    # Prints the bounds information for all spaces in the current context.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value (implicitly returns nil).
    # """
        p "bounds informaton:"
        @spaces.each do |s|
            s.print_bounds_points
        end
    end

    def change_space_parameters(params)
    # Function:
    # Updates a specific attribute of the settings for a space identified by its ID within the @spaces collection.
    # 
    # Parameters:
    # params : Array
    # An array containing three elements:
    # - space_id (Any): The unique identifier of the space to be modified.
    # - attribute (Symbol or String): The name of the setting attribute to update.
    # - space_data (Any): The new value to assign to the specified attribute.
    # 
    # Returns:
    # None
    # This method does not return any value. It modifies the settings of the target space in place.
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
    # Function:
    # Initializes a new instance of the class with face, transformation, and ID attributes.
    # 
    # Parameters:
    # f : object
    # The face object associated with the instance.
    # t : object
    # The transformation data applied to the face.
    # i : int or str
    # A unique identifier for the instance.
    # 
    # Returns:
    # None
    # This constructor does not return a value.
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
    # """
    # Function
    # --------
    # Initializes a new instance of the class with material and category data.
    # 
    # Parameters
    # ----------
    # params : Array
    # An array containing material properties in the following order:
    # - params[0] : String, the category of the material.
    # - params[1] : String, the name of the material.
    # - params[2] : String, the type of the material.
    # - params[3] : Numeric or String, the red component (R) of the color.
    # - params[4] : Numeric or String, the green component (G) of the color.
    # - params[5] : Numeric or String, the blue component (B) of the color.
    # - params[6] : Numeric or String, the specular value (spec) of the material.
    # - params[7] : Numeric or String, the roughness value (rough) of the material.
    # 
    # Returns
    # -------
    # None
    # This constructor does not return a value. It initializes object attributes.
    # """
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
    # Function
    # --------
    # Search for a material index in the material library based on a given name string and material category mapping.
    # 
    # This method attempts to identify a material by matching a provided name string against predefined categories
    # and material names within a material library. It first determines the appropriate category by scanning the
    # input string against known categories (case-insensitive), then searches within that category for a matching
    # material name. If a material has a placeholder name "-", it may be selected as a default.
    # 
    # Parameters
    # ----------
    # name_str : str
    # Input string representing the material name or description. Spaces are replaced with underscores before processing.
    # mat_lib : list of MoosasMaterial objects
    # The material library containing material entries with attributes such as `name`, `category`.
    # 
    # Returns
    # -------
    # idx : int or nil
    # Index of the matched material in the material library. Returns `nil` if no match is found.
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

    def initialize(f,h,c,b,id=nil)
    # Function:
    # Initializes a new instance of the class with floor, height, ceiling, and boundary data, computes derived properties such as total area and height in meters, assigns a unique identifier if not provided, sets up default zone settings, and applies standard-based configurations based on user interface settings.
    # 
    # Parameters:
    # f : Array<Floor>
    # An array of floor objects representing multifloor layout; used to compute total floor area.
    # h : Numeric
    # The height of the space in inches; converted to meters using a constant multiplier.
    # c : Array<Ceiling>
    # An array of ceiling objects associated with the floors.
    # b : Array<Edge>
    # An array of boundary edges defining the perimeter of the space; used for ID generation and spatial calculations.
    # id : String, optional
    # A unique identifier for the space. If not provided, it is automatically generated based on area, height, boundary count, WWR values, and centroid coordinates.
    # 
    # Returns:
    # None
    # This method initializes the object's state and does not return a value.
        @multifloor = f
        @floor=f
        @height = h
        @ceils = c
        @bounds = b
        @id = id
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
        if @id == nil
            #根据空间参数计算id
            @id='s_'+@area_m.round().to_s+@height_m.round().to_s+@bounds.length.to_s
            @id += @bounds.map{|edge| (edge.wwr*10).round()}.sort.join("")
            @id += self.get_weight_center().map{ |v| v.round().to_s  }.join("")
        end
        @settings["zone_name"]= @id
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
    # """
    # Function
    # --------
    # calculate_zone_radation
    # Calculates and aggregates summer and winter solar radiation values for all boundaries
    # within a zone based on the provided model geometry. The method updates the instance's
    # settings with total zone-level radiation values, rounded to two decimal places.
    # 
    # Parameters
    # ----------
    # model : Object
    # A SketchUp model or equivalent structure passed as an argument, though it is
    # immediately reassigned inside the method. The actual model data used comes from
    # the result of `self.get_all_face`, which is expected to return an array of face
    # objects containing geometric data for radiation analysis.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It modifies the `@settings` hash in place by
    # setting the following keys:
    # - "zone_summerrad": Total summer radiation across all boundaries, rounded to 2 decimals.
    # - "zone_winterrad": Total winter radiation across all boundaries, rounded to 2 decimals.
    # """

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
    # """
    # Function
    # ----------
    # Apply settings from a specified setting key to the current configuration.
    # 
    # This method loads a dictionary of settings based on the provided key from a global template (`$template`).
    # It initializes the `zone_standard` in the instance settings if not already set. Then, for each key in the
    # loaded setting dictionary, it sets the value in the instance's `@settings` if the key does not exist, or
    # if its current value matches the corresponding value from the previous `zone_standard`. Finally, it updates
    # the `zone_standard` to the new setting key.
    # 
    # Parameters
    # ----------
    # setting_key : String
    # The key used to look up the setting dictionary in the global `$template` hash. This determines which
    # set of default settings will be applied.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It modifies the `@settings` instance variable in place.
    # """
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
    # Function:
    # Visualizes the orientation of entities within specified bounds by applying a visualization factor to each bound.
    # 
    # Parameters:
    # entities : object
    # The entities to be visualized. The exact type depends on the context in which the method is used, typically representing graphical or geometric data.
    # 
    # Returns:
    # object
    # The modified entities after applying the visualization factor for each bound in @bounds.
        for w in @bounds
            entities=w.visualize_factor(entities)
        end
        return entities
    end

    def get_weight_center()
    # """
    # Function
    # --------
    # Calculate the average weight center across all floor elements.
    # 
    # This method computes the weight center for each floor element, aggregates
    # their coordinates, and returns the averaged center point in 3D space.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters. It operates on the instance
    # variable `@floor`, which is expected to be an array of objects that
    # respond to the `get_weight_center` method.
    # 
    # Returns
    # -------
    # Array<Float>
    # A three-element array representing the [x, y, z] coordinates of the
    # averaged weight center. Each coordinate is the mean of the corresponding
    # coordinates from all floor elements' weight centers.
    # """
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
    # """
    # Function
    # --------
    # Constructs a 3D volume representing a space by creating a face from floor outline vertices and extruding it vertically.
    # 
    # This method extracts the outer loop vertices of the first floor face, raises them vertically by 10,000 units
    # to form a horizontal face, ensures the face normal points upward in the Z direction, and then extrudes
    # (push/pull) the face by the specified height to create a solid volume. The modified entities collection is returned.
    # 
    # Parameters
    # ----------
    # entities : Sketchup::Entities
    # The entities collection to which the new face and volume will be added.
    # Typically part of a SketchUp model's drawing context.
    # 
    # Returns
    # -------
    # Sketchup::Entities
    # The same entities collection after attempting to add the constructed face and extruded volume.
    # If an error occurs during construction, the original entities collection is returned unmodified.
    # """
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
    # """
    # Function
    # --------
    # Calculate the average 3D position (centroid) of all vertices from the outer loops of faces in the floor.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # Array[Float]
    # A three-element array representing the averaged x, y, and z coordinates
    # of all vertices across all outer loops of the faces in @floor.
    # The values are computed by summing each coordinate component and dividing
    # by the total number of vertices.
    # """
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
    # """
    # Function
    # --------
    # assign_type_directly
    # Assigns entity types directly to floor, ceiling, wall, glazing, and shading components based on the given ground height
    # and material properties. This method categorizes building elements such as floors, walls, and glazings into appropriate
    # semantic types (e.g., ground floor, roof, internal/external walls) for further processing or analysis.
    # 
    # Parameters
    # ----------
    # groundHeight : Float
    # The reference height used to determine which floor elements should be classified as ground floor.
    # Any floor with height less than or equal to `groundHeight + 1.0` will be marked as a ground floor.
    # 
    # Returns
    # -------
    # nil
    # Returns nil if any of the required instance variables (`@floor`, `@ceils`, `@bounds`) are not initialized.
    # Otherwise, performs in-place type assignment and returns nothing (nil implicitly).
    # """
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
    # """
    # Function
    # --------
    # get_all_face
    # 
    # Returns a flattened list of all face elements including floors, ceilings, walls, internal walls,
    # and their associated glazing and shading components from the current object's collections.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # Array
    # A flattened array containing all face objects (MoosasFaces) from @floor, @ceils, @bounds.walls,
    # and @internal_wall, along with their respective glazings and shading sub-elements.
    # """
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
    # """
    # Function
    # --------
    # Creates a backup of the current object's settings and all associated floor, ceiling,
    # and boundary objects by cloning the settings and invoking the backup method on each component.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # nil
    # Always returns nil after completing the backup process.
    # """
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
    # """
    # Function
    # --------
    # Restores the object's state to a previously saved configuration by resetting settings and recursively restoring all associated floor, ceiling, and boundary components.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # nil
    # This method always returns nil upon completion.
    # """
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
    # Function:
    # Packs the data of the current object and its associated face data into a structured format.
    # The method collects information about the object's settings and recursively gathers packed
    # data from all faces returned by `get_all_face`. The resulting structure includes both
    # metadata (such as ID and settings) and an array of packed face data.
    # 
    # Parameters:
    # is_detail : bool
    # A flag indicating whether detailed data should be included in the packing process.
    # If true, more comprehensive information is included for each face; otherwise, only basic data is packed.
    # 
    # Returns:
    # Array
    # A two-element array where the first element is a hash containing the object's ID and settings,
    # and the second element is an array of packed face data obtained by calling `pack_data(is_detail)`
    # on each face returned by `get_all_face`.
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
    # """
    # Function
    # --------
    # Initialize a new instance of the class with edge, height, and optional inference settings.
    # 
    # Parameters
    # ----------
    # e : Edge
    # The edge object associated with this instance, representing the geometric edge.
    # height : float
    # The height of the edge in inches. Used to compute area and set spatial properties.
    # require_infer : bool, optional, default=True
    # If True, performs additional initialization tasks such as calculating area and setting center point.
    # If False, skips these computations.
    # 
    # Returns
    # -------
    # None
    # This constructor does not return a value. It initializes instance variables and sets up default settings.
    # 
    # Notes
    # -----
    # - The area in square meters is calculated using the length of the edge, given height, and inch-to-meter squared multiplier.
    # - The center point of the edge is computed if `require_infer` is True.
    # - Default thermal and optical settings are initialized for opaque and glazing components, including U-values, SHGC, and visible transmittance.
    # - Radiation values for summer and winter are initialized to zero.
    # """
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
    # Function:
    # Calculate the total solar radiation for summer and winter periods on glazing elements in a model, weighted by their area. The method computes radiation using cumulative sky data and updates the settings hash with aggregated radiant values.
    # 
    # Parameters:
    # model : object
    # A representation of the building or geometric model used in radiation calculation. This is passed to the radiance calculation function to determine visible geometry from each glazing element's perspective.
    # 
    # Returns:
    # None
    # The method modifies the instance variable @settings in place, setting the keys 'summer_rad' and 'winter_rad' to the total weighted radiation values (in W·h/m² or similar unit) across all glazing elements. No value is returned.
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
    # """
    # Function
    # --------
    # Visualizes a geometric factor by creating a face entity in 3D space based on the wall center and normal vector.
    # 
    # This method computes an origin point from the first wall's weight center and uses the normal vector (scaled)
    # to define the orientation and position of a quadrilateral face. The face is added to the given entities
    # collection, effectively visualizing a directional or structural indicator.
    # 
    # Parameters
    # ----------
    # entities : Sketchup::Entities
    # The entities collection to which the generated face will be added.
    # Must be a valid SketchUp entities container (e.g., from a group or component).
    # 
    # Returns
    # -------
    # Sketchup::Entities
    # The same entities collection with the new face added.
    # Returns the modified entities object to allow for method chaining.
    # """
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
    # """
    # Function
    # --------
    # Sets the length attribute of the instance to the specified value.
    # 
    # Parameters
    # ----------
    # length : int or float
    # The value to be assigned to the instance variable `@len`.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value.
    # """
        @len=length
    end
    
    def assign_value_directly(wwr,normal,len_m,height_m)
    # """
    # Function
    # --------
    # assign_value_directly : Assigns values directly to instance variables for wall-related properties.
    # 
    # Parameters
    # ----------
    # wwr : float
    # Window-to-wall ratio, representing the proportion of window area relative to the wall area.
    # normal : Array<Numeric>
    # Normal vector of the wall surface, typically in the form [x, y, z], indicating orientation.
    # len_m : float
    # Length of the wall in meters.
    # height_m : float
    # Height of the wall in meters.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value; it initializes or updates instance variables.
    # """
        @area_m = len_m * height_m
        @wwr = wwr
        @normal = normal
        @len_m = len_m
    end

    #根据墙体的面推断这条边的类型，只要存在一个面是内部面的类型，就推断为内部边
    def infer_type
    # """
    # Function
    # --------
    # infer_type
    # Determines if the edge is an internal edge by checking whether any wall or glazing associated with the edge
    # is of an internal type. If an internal wall or glazing is found, sets `@is_internal_edge` to true and returns early.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # nil or terminates early
    # The method does not explicitly return a value (returns nil implicitly), but may terminate early upon finding
    # an internal wall or glazing. Its primary effect is setting the instance variable `@is_internal_edge`.
    # """
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
    # """
    # Function
    # --------
    # set_edge_center_point :
    # Calculates and sets the center point of an edge in 3D space, with the z-coordinate adjusted by a given floor height.
    # 
    # Parameters
    # ----------
    # floor_height : Numeric
    # The height value used to adjust the z-coordinate of the center point, typically representing the elevation of the floor.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It modifies the instance variable `@cp` to store the computed center point as a 3-element array [cx, cy, cz].
    # """
        cx = (@edge[0].x + @edge[1].x)/2
        cy = (@edge[0].y + @edge[1].y)/2
        cz = (@edge[0].z + @edge[1].z + floor_height )/2
        @cp  = [cx,cy,cz]
    end

    #获取代表正面的法向量
    def set_edge_normal()
    # Function
    # --------
    # Set the normal vector of an edge based on its direction and length.
    # 
    # The method computes the normalized direction vector of the edge defined by two points,
    # then calculates the perpendicular (normal) vector in 2D plane, assuming the edge lies in the XY-plane.
    # The resulting normal vector is stored as a 3D vector with z-component set to zero.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # None
    # The method modifies the instance variable `@normal` in place,
    # setting it to the computed normal vector as an array [nx, ny, nz].
        len = get_length()
        dx = (@edge[1].x - @edge[0].x) / len   #进行归一化处理
        dy = (@edge[1].y - @edge[0].y) / len
        @normal = [0-dy,dx,0]
    end

    def reverse_normal()
    # """
    # Function
    # --------
    # Reverse the direction of the normal vector.
    # 
    # This method inverts the x and y components of the instance's normal vector
    # while keeping the z component unchanged, effectively reversing its direction
    # in the xy-plane.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # Array<Number>
    # The modified normal vector with the x and y components negated and
    # the z component preserved. The result is assigned back to the instance
    # variable `@normal` and returned implicitly.
    # """
        @normal = [0-@normal[0],0-@normal[1],@normal[2]]
    end

    def get_length
    # """
    # Function
    # --------
    # Calculate and return the length of the edge.
    # 
    # This method computes the Euclidean distance between two points stored in the `@edge` array
    # if `@len` is not already set. The result is cached in the instance variable `@len` to avoid
    # redundant calculations in subsequent calls.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # Float
    # The length of the edge as a floating-point number, representing the Euclidean distance
    # between the two endpoints of the edge.
    # """
        if @len != nil
            return @len
        end
        @len = ( (@edge[0].x - @edge[1].x) ** 2 + (@edge[0].y - @edge[1].y) ** 2 ) ** 0.5
        return @len
    end

    def get_length_in_m
    # """
    # Function
    # --------
    # get_length_in_m : float
    # Converts and returns the length in meters. If the length in meters (@len_m) is already calculated and stored,
    # it returns the cached value. Otherwise, it calculates the length by multiplying the result of `get_length()`
    # (assumed to be in inches) with the inch-to-meter conversion multiplier from MoosasConstant, caches it, and returns it.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # float
    # The length in meters. The value is cached in the instance variable @len_m for subsequent calls.
    # """
        if @len_m != nil
            return @len_m
        end
        @len_m = get_length() * MoosasConstant::INCH_METER_MULTIPLIER
        return @len_m
    end

    def get_vface_ids
    # """
    # Function
    # ----------
    # get_vface_ids
    # 
    # Retrieve the entity IDs of all face objects associated with walls and glazings.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Array<Integer>
    # A list of entity IDs from the face objects of walls and glazings stored in the instance variables @walls and @glazings.
    # """
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
    # """
    # Function:
    # Creates a backup of the current state of the object's properties, including wall and glazing settings,
    # by storing copies of mutable attributes to allow for later restoration.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    # """
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
    # Function:
    # Restores the object's state to its backup values by resetting instance variables
    # and recursively calling restore on associated wall and glazing objects.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    # 
    # Notes:
    # This method resets @wwr to the backup value @b_wwr, sets @settings to nil and then
    # restores it from the backup @b_settings. It also invokes the restore method on each
    # element in the @walls and @glazings collections, propagating the restoration process
    # to associated objects.
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
    # """
    # Function
    # --------
    # Get the orientation based on the normal vector.
    # 
    # Determines the cardinal direction (east, west, north, or south) corresponding to the
    # object's normal vector by computing the cosine of the angle with the x-axis and comparing
    # against predefined angular thresholds. The result is cached in the instance variable `@ori`
    # to avoid recomputation on subsequent calls.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Symbol
    # A symbol representing the orientation, one of:
    # - MoosasConstant::ORIENTATION_EAST
    # - MoosasConstant::ORIENTATION_WEST
    # - MoosasConstant::ORIENTATION_NORTH
    # - MoosasConstant::ORIENTATION_SOUTH
    # The orientation is determined based on the direction of the normal vector.
    # """
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
    # Function
    # --------
    # Retrieves the coordinates of the two end points of an edge, converted to meters.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on the instance's `edge` attribute,
    # which is expected to be a collection of two vertices with `x`, `y`, and `z` coordinate attributes.
    # 
    # Returns
    # -------
    # Array[Array[Float, Float, Float], Array[Float, Float, Float]]
    # A nested array containing two 3D points in meters:
    # - The first inner array represents the (x, y, z) coordinates of the first vertex.
    # - The second inner array represents the (x, y, z) coordinates of the second vertex.
    # Coordinates are converted to meters using the `to_m` method assumed to be available on coordinate values.
        p1 = [edge[0].x.to_m,edge[0].y.to_m,edge[0].z.to_m]
        p2 = [edge[1].x.to_m,edge[1].y.to_m,edge[1].z.to_m]   
        return [p1,p2]
    end
end

#描述每个面
class MoosasFace
    attr_accessor :face, :glazings, :shading, :height, :transformation, :area, :wc, :type,:id,:uid, :normal, :area_m, :settings,:material


    def initialize(face, transformation, area,nor=nil,id=nil,uid=nil)
    # Function:
    # Initializes a new instance of the class with given geometric and physical properties,
    # calculates derived attributes such as height if applicable, and sets default values
    # for optional attributes including material, glazing, shading, and thermal settings.
    # 
    # Parameters:
    # face : Geometric entity representing the surface (e.g., a face in a 3D model)
    # The primary geometry associated with the object; used to derive additional properties.
    # transformation : Transformation matrix or object
    # Defines spatial placement and orientation of the face in 3D space.
    # area : Float
    # Surface area of the face in square inches.
    # nor : Vector or Array, optional, default: nil
    # Normal vector of the face; if not provided, it may be computed from the face.
    # id : String or Integer, optional, default: nil
    # Identifier for the object; used for referencing in larger models.
    # uid : String or Integer, optional, default: nil
    # Unique identifier for the instance; ensures uniqueness across the system.
    # 
    # Returns:
    # None
    # This method is a constructor and does not return a value. It initializes the object's state.
        @face = face
        @transformation = transformation
        @area = area
        @normal = nor
        calculate_height if face != nil
        @wc = nil
        @type = nil
        @material=nil
        @glazings=[]
        @shading=[]
        @id = id
        @uid = uid
        @area_m = area * MoosasConstant::INCH_METER_MULTIPLIER_SQR
        @settings = {"u"=>MoosasConstant::WALL_U,"id":@id}
    end

    def assign_material(mat_lib)
    # Function:
    # Assigns a material to the current object based on its existing material name or type, using a given material library.
    # The method first attempts to match the material by its original name and then by display name. If no match is found,
    # it assigns a default material based on the object's type (e.g., floor, wall, window, roof).
    # 
    # Parameters:
    # mat_lib : Hash or Array
    # A collection representing the available materials, used as input for searching and matching by name.
    # 
    # Returns:
    # None
    # This method does not return a value. It sets the instance variable `@material` to the matched material number
    # (as determined by `MoosasMaterial.search_material`) or leaves it as nil if no match is found.
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
    # """
    # Function
    # --------
    # Calculate the average height (z-coordinate) of the transformed vertices of a face.
    # 
    # Parameters
    # ----------
    # self : object
    # The instance of the class containing this method. It is expected to have
    # the following attributes:
    # - @height (Float): Instance variable to store the computed average height.
    # - @face (Object): An object representing a geometric face, which contains
    # a collection of vertices.
    # - @face.vertices (Array): A list of vertex objects, each having a `position`
    # attribute representing its 3D coordinates.
    # - transformation (Geom::Transformation or similar): A transformation matrix
    # applied to each vertex position.
    # 
    # Returns
    # -------
    # None
    # This method modifies the instance variable @height in place, setting it to
    # the average z-coordinate of the transformed vertex positions.
    # """
        @height = 0
        @face.vertices.each do |v|
            tp = transformation * v.position
            @height += tp.z
        end
        @height /= @face.vertices.length
    end

    def get_transformation_vs
    # """
    # Function
    # --------
    # get_transformation_vs
    # Computes and returns the transformed 2D coordinates of the face's vertices
    # by applying the current transformation matrix to each vertex position.
    # The result is cached to avoid redundant computation on subsequent calls.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters. It operates on instance variables:
    # - @vs: cache for transformed vertex coordinates
    # - @face: contains the vertices to be transformed
    # - @transformation: a transformation matrix applied to each vertex position
    # 
    # Returns
    # -------
    # Array[Array[Numeric, Numeric]]
    # An array of 2-element arrays representing the x and y coordinates
    # of each transformed vertex in 2D space. Each inner array corresponds
    # to one vertex in the format [x, y].
    # """
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
    # """
    # Function
    # --------
    # Computes and returns the 3D transformed vertex positions after applying a transformation matrix and unit conversion.
    # 
    # The method iterates over each vertex of the face, applies a transformation (typically a matrix transformation),
    # and converts the resulting coordinates from inches to meters (using factor 0.0254). The transformed 3D points
    # are stored in the instance variable `@vs_3d` and returned as an array.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on the instance variables:
    # - `@face`: An object with a `vertices` collection.
    # - `@transformation`: A transformation matrix (e.g., from SketchUp's Geom::Transformation) applied to each vertex.
    # - `@vs_3d`: Will be initialized as an empty array to store the resulting 3D points.
    # 
    # Returns
    # -------
    # Array<Array<Float>>
    # An array of 3-element arrays representing 3D points in meters.
    # Each sub-array contains [x, y, z] coordinates after transformation and unit conversion.
    # """
        @vs_3d = []
        @face.vertices.each do |v|
            tv = @transformation * v.position
            @vs_3d.push [tv.x * 0.0254,tv.y * 0.0254,tv.z * 0.0254]
        end
        return @vs_3d
    end
    def centroid
    # Function:
    # Calculates the centroid of a face by transforming the positions of its vertices
    # and computing the average coordinates in 3D space.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # Geom::Point3d : A 3D point representing the centroid of the transformed face vertices.
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
    # """
    # Function
    # --------
    # Extracts height information from transformed vertex positions of the face.
    # 
    # This method computes the z-coordinates (heights) of all vertices of the face
    # after applying a transformation matrix, then returns the minimum height,
    # the reference height (@height), and the maximum height among the transformed vertices.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Array[Float, Float, Float]
    # An array containing three elements:
    # - The minimum z-coordinate (minimum height) among all transformed vertices.
    # - The reference height stored in the instance variable @height.
    # - The maximum z-coordinate (maximum height) among all transformed vertices.
    # """
        hs = [] 
        @face.vertices.each do |fv|
            tfv = @transformation * fv.position
            hs.push tfv.z
        end
        return [hs.min,@height,hs.max]
    end

    def get_triangle_area(p1,p2,p3)
    # """
    # Function
    # --------
    # Calculate the area of a triangle given three points in 2D space using Heron's formula.
    # 
    # Parameters
    # ----------
    # p1 : Point
    # The first vertex of the triangle. Must have a `distance` method to compute Euclidean distance to another point.
    # p2 : Point
    # The second vertex of the triangle. Must have a `distance` method to compute Euclidean distance to another point.
    # p3 : Point
    # The third vertex of the triangle. Must have a `distance` method to compute Euclidean distance to another point.
    # 
    # Returns
    # -------
    # Float
    # The area of the triangle formed by points p1, p2, and p3. Returns a non-negative float value representing the area.
    # """
        a = p1.distance(p2)
        b = p2.distance(p3)
        c = p3.distance(p1)
        t = (a+b+c)/2
        s = (t * (t-a)*(t-b)*(t-c))**0.5
        return s
    end

    def get_transformation_mesh_polygons
    # """
    # Function
    # --------
    # Retrieves the transformed 2D polygon representation of a face's mesh after applying a geometric transformation.
    # 
    # This method extracts the polygons from the underlying mesh of a face, applies a transformation matrix to each vertex of every triangle, and returns the resulting 2D coordinates in an array format suitable for 2D rendering or geometric processing.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Array<Array<Array<Float>>>
    # A nested array structure representing the list of transformed triangular polygons.
    # Each polygon is represented as a triangle with three vertices, and each vertex is an array of two Float values [x, y] in 2D space.
    # The structure follows: [[[x1, y1], [x2, y2], [x3, y3]], ...] for all triangles in the mesh.
    # """
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
    # """
    # Function
    # --------
    # Computes and returns the transformed edge coordinates of the face.
    # 
    # This method iterates over each edge in the associated face, applies a transformation
    # to the start and end positions of the edge, and stores the resulting transformed
    # coordinate pairs.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on instance variables:
    # - @face: An object that contains a collection of edges.
    # - @transformation: A transformation matrix or operator applied to edge endpoints.
    # 
    # Returns
    # -------
    # Array<Array<Vector>>
    # An array of arrays, where each inner array contains two transformed points
    # (start and end positions) representing an edge. Each point is typically a Vector
    # or coordinate-like object resulting from the transformation.
    # """
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
    # """
    # Function
    # --------
    # Returns the edge with the minimum combined z-coordinate value from a collection of edges.
    # 
    # This method caches the result in the instance variable `@be` to avoid recomputation in subsequent calls.
    # If `@be` is already set, it is returned immediately. Otherwise, the method computes the bottom edge by
    # evaluating the sum of z-coordinates of both endpoints of each edge and selecting the edge with the smallest sum.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Array(Endpoint, Endpoint) or nil
    # The edge (represented as an array of two endpoints) with the smallest combined z-coordinate.
    # Each endpoint is expected to have a `z` attribute. Returns nil if no edges are available.
    # """
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
    # """
    # Function
    # ----------
    # is_glazing
    # Determines whether the current face is considered glazing based on material transparency.
    # If the material's alpha value is below a specified threshold, it configures glazing settings
    # and returns true; otherwise, returns false.
    # 
    # Parameters
    # ----------
    # self : object
    # The instance of the class containing this method, assumed to have `@face` and `@settings` attributes.
    # - @face: An object with a `material` attribute representing the surface material.
    # - @settings: A hash that will be updated with glazing thermal properties if the material is transparent.
    # 
    # Attributes (used internally)
    # ----------------------------
    # @face.material : object or nil
    # The material applied to the face. Must respond to `alpha`. Can be nil.
    # @face.material.alpha : float
    # The alpha (transparency) value of the material, expected to be in the range [0.0, 1.0].
    # MoosasConstant::MATERIAL_ALPHA_THRESHOLD : float
    # Class constant defining the alpha threshold below which a material is treated as glazing.
    # MoosasConstant::WIN_U : float
    # Class constant representing the U-value assigned to glazing surfaces.
    # MoosasConstant::WIN_SHGC : float
    # Class constant representing the Solar Heat Gain Coefficient (SHGC) assigned to glazing surfaces.
    # @settings["u"] : float
    # Updated with MoosasConstant::WIN_U if the material is glazing.
    # @settings["s"] : float
    # Updated with MoosasConstant::WIN_SHGC if the material is glazing.
    # 
    # Returns
    # -------
    # Boolean
    # true if the material exists and its alpha value is below the threshold (indicating glazing);
    # false otherwise.
    # """
        if @face.material && @face.material.alpha < MoosasConstant::MATERIAL_ALPHA_THRESHOLD
            @settings["u"] = MoosasConstant::WIN_U
            @settings["s"] = MoosasConstant::WIN_SHGC
            return true
        else
            return false
        end
    end

    def backup
    # """
    # Function
    # --------
    # Creates a backup copy of the current settings by cloning the `@settings` instance variable
    # and assigning it to the `@b_settings` instance variable.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # Object
    # The return value is the result of the `clone` operation, which is the duplicated object
    # assigned to `@b_settings`. While the method does not explicitly return a value,
    # Ruby methods return the result of the last expression, which in this case is the cloned object.
    # """
        @b_settings = @settings.clone
    end

    def restore
    # """
    # Function
    # --------
    # Restores the current settings to a previously stored backup state.
    # 
    # This method resets the `@settings` instance variable to `nil` and then
    # reassigns it with the value stored in the backup instance variable `@b_settings`,
    # effectively reverting any changes made to the settings.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters.
    # 
    # Returns
    # -------
    # Object
    # The value of `@b_settings` assigned to `@settings`, typically a settings object or hash.
    # The return is implicit, as the last evaluated expression is the assignment.
    # """
        @settings = nil
        @settings = @b_settings
    end

    def pack_data(is_detail)
    # Function:
    # Packs the object's data into an array based on the detail level requested.
    # 
    # Parameters:
    # is_detail : bool
    # A flag indicating whether to include detailed information in the packed data.
    # If true, additional properties such as normal vector and transformation matrix are included.
    # 
    # Returns:
    # Array
    # An array containing the object's basic or detailed data.
    # When `is_detail` is true, the array includes: [@id, @type, @area_m, @normal, transformation_vs_3d].
    # When `is_detail` is false, only basic data is included: [@id, @type, @area_m].
        if is_detail == true
            f_data = [@id,@type,@area_m,@normal,self.get_transformation_vs_3d()]
        else
            f_data = [@id,@type,@area_m]
        end
    end
end




