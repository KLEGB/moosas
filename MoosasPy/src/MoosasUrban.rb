#encoding: utf-8

module MoosasUrban
    p 'MoosasUrban Ver.0.0.0'
    R = 6371000.0
    A2PI = Math::PI / 180.0
    BEIJING_CENTER_LAT = 39.90648
    BEIJING_CENTER_LNG = 116.39127

    ENABLE_ANALYSIS = true


    def self.load_osm_building_from_json(json_string)
        begin
            osm = JSON.parse(json_string)

            count = 0
            center = [0,0]   
            osm["features"].each do |f|
                count += 1
                center[0] += f["geometry"]["coordinates"][0][0][0]
                center[1] += f["geometry"]["coordinates"][0][0][1]
                #p "第#{count}个：" + f['properties']['address'] +", " + f['properties']['Name']
            end

            return if count == 0
            center[0] /= count
            center[1] /= count

            p "一共有#{count}个建筑"
            blgs = []
            osm["features"].each do |f|
                coords = []

                f["geometry"]["coordinates"][0].each do |c|
                    m = (c[1] + center[1]) / 2 * A2PI
                    d_lon = (c[0] - center[0]) * A2PI
                    d_lat = (c[1] - center[1]) * A2PI

                    x = R * d_lon * Math.cos(m)
                    y = R * d_lat
                    coords.push([x.m,y.m,0.m])
                end

                height = f["properties"]["Floor"].to_f
                if height != nil
                    height *= 3.0  #默认层高3米
                else
                    height = 15.0  #缺失高度的建筑，默认15米高   
                end
                blgs.push([coords,height])
            end

            
            #绘制建筑
            entities = Sketchup.active_model.active_entities
            blgs.each do |b|
                begin
                    face = entities.add_face(b[0])
                    face.reverse!  if face.normal[2] == -1
                    #p face.normal
                    face.pushpull(b[1].m, true)
                rescue Exception => e
                    MoosasUtils.rescue_log(e)
                end
            end

        rescue Exception => e
            MoosasUtils.rescue_log(e)
            UI.messagebox "加载建筑数据失败"
        end
    end


    #load from file
    def self.load_osm_building

        osm_file = UI.openpanel("选择OSM文件", "d:/code/urban_svf/", "json")

        begin
            json_string = File.open(osm_file, "r:UTF-8", &:read)
            json_string = json_string.strip()
            json_string = json_string[1,json_string.length-1]

            self.load_osm_building_from_json(json_string)

        rescue Exception => e
            MoosasUtils.rescue_log(e)
            UI.messagebox "读取OSM文件失败"
        end

    end



    ALPHA = 1.0
    DELTA_B = 1.0 / 180 * Math::PI  #1度角度对应的弧度
    ANGLE_TO_DEGREE = 1.0 / 180 * Math::PI 
    def self.analysis_single_point_svf(model,point)

        svf  = 0
        for a in 0..359
            min = 0
            max = Math::PI / 2
            b = 0
            while (max - min) > DELTA_B do
                b = (max + min)/2.0
                alpha = a * ANGLE_TO_DEGREE 
                direction = Geom::Vector3d.new(Math.cos(a), Math.sin(a), Math.sin(b))
                ray = [point,direction]
                if model.raytest(ray) 
                    min = b
                else
                    max = b
                end
            end
            b = (max + min)/2.0
            svf += Math.cos(b) ** 2
        end
        svf /= 360.0
        return svf
    end

    '''
        生成计算网格，去除被建筑覆盖住的网格
        逐点计算svf
        渲染svf
    '''
    BLUE_COLOR = Sketchup::Color.new "Blue"
    RED_COLOR = Sketchup::Color.new "Red"
    YELLOW_COLOR = Sketchup::Color.new "Yellow"
    def self.analysis_urban_svf()
        model = Sketchup.active_model


        result = UI.messagebox('需要分析全部模型吗?', MB_YESNO)
        if result == IDYES
            #生成计算网格
            bounds = model.bounds
        else
            model=Sketchup.active_model
            #ents=model.active_entities
            ss=model.selection
            bounds = ss[0].bounds
            #ssa=ss.to_a
            #ssg=ents.add_group(ssa)
            #center=ssg.bounds.center ### <<<<
            #ssa=ssg.entities.to_a
            #ssg.explode
            #ss.clear
            #ss.add(ssa)
        end
        min_point = bounds.min
        width = bounds.width
        height = bounds.height

        grid_size = 10.m
        prompts = ["Grid Size(m)"]
        defaults = ["5"]
        input = UI.inputbox(prompts, defaults, "Tell me about grid size")
        begin
            grid_size = input[0].to_f
            grid_size = grid_size.m
        rescue Exception => e
        end
        nx = width / grid_size 
        ny = height / grid_size 

        up_direction = Geom::Vector3d.new(0, 0, 1)

        point_list = []
        for ix in 0..nx
            x = min_point.x + (ix +0.5) * grid_size
            for iy in 0..ny
                y = min_point.y + (iy +0.5) * grid_size
                point = Geom::Point3d.new(x,y,-0.1.m)
                if not model.raytest([point, up_direction]) 
                    point_list.push(point)
                end
            end
        end
        p "一共生成#{point_list.length}个网格点"


        return if not ENABLE_ANALYSIS

        #逐点计算
        size = point_list.length - 1 
        svf_list = []
        p "一共需要计算#{size}个网格点"
        for i in 0..size do 
            pt = point_list[i]
            svf = self.analysis_single_point_svf(model,pt)
            p "第#{i}个点，svf取值=#{svf}"
            svf_list.push(svf)
        end
        svf_mean =  svf_list.length == 0 ? 0 : svf_list.reduce(:+) / svf_list.size.to_f 
        p "SVF平均值#{svf_mean},最大值#{svf_list.max}，最小值#{svf_list.min}"

        #绘制网格
        half_grid_size = grid_size / 2
        group = model.active_entities.add_group
        entities = group.entities
        for i in 0..size do 
            pt = point_list[i]
            p1 = [pt.x - half_grid_size, pt.y - half_grid_size, pt.z]
            p2 = [pt.x - half_grid_size, pt.y + half_grid_size, pt.z]
            p3 = [pt.x + half_grid_size, pt.y + half_grid_size, pt.z]
            p4 = [pt.x + half_grid_size, pt.y - half_grid_size, pt.z]

            face = entities.add_face([p1,p2,p3,p4])

            svf = svf_list[i]
            color = get_svf_color(svf)
            face.material = face.back_material = color
        end
    end

    def self.get_svf_color(svf)
        if svf > 0.5
            color = YELLOW_COLOR.blend(RED_COLOR,(svf-0.5)/0.5)
        else
            color = RED_COLOR.blend(BLUE_COLOR,svf/0.5)
        end
        return color
    end

    DEFAULT_GRID_SIZE = 10.m
    def self.load_urban_svf_data()
        urban_svf_file = UI.openpanel("选择城市光环境数据文件", "d:/code/urban_svf/", "json")
        begin
            json_string = File.open(urban_svf_file, "r:UTF-8", &:read)
            json_string = json_string.strip()

            urban_svf = JSON.parse(json_string)

            count = 0
            blgs = []
            urban_svf["buildings"].each do |b|

                coords = []
                b["geometry"]["coordinates"][0].each do |c|
                    m = (c[1] + BEIJING_CENTER_LAT) / 2 * A2PI
                    d_lon = (c[0] - BEIJING_CENTER_LNG) * A2PI
                    d_lat = (c[1] - BEIJING_CENTER_LAT) * A2PI

                    x = R * d_lon * Math.cos(m)
                    y = R * d_lat
                    coords.push([x.m,y.m,0.m])
                end

                height = b["properties"]["Floor"].to_f
                if height != nil
                    height *= 3.0  #默认层高3米
                else
                    height = 15.0  #缺失高度的建筑，默认15米高   
                end
                blgs.push([coords,height])

                count += 1
                p "第#{count}个：" + b['properties']['address'] +", " + b['properties']['Name']
            end

            #绘制建筑
            model = Sketchup.active_model
            building_group = model.active_entities.add_group
            entities = building_group.entities
            blgs.each do |b|
                begin
                    face = entities.add_face(b[0])
                    face.reverse!  if face.normal[2] == -1
                    #p face.normal
                    face.pushpull(b[1].m, true)
                rescue Exception => e
                    MoosasUtils.rescue_log(e)
                end
            end

            p "一共导入#{count}个建筑"

            grid_group = model.active_entities.add_group
            entities = grid_group.entities
            half_grid_size = DEFAULT_GRID_SIZE / 2.0
            grid_count = 0
            min_svf = 10.0
            max_svf = -10.0
            sum_svf = 0.0
            urban_svf["grid_svf"].each do |g|
                c = g["loc"]["coordinates"]
                m = (c[1] + BEIJING_CENTER_LAT) / 2 * A2PI
                d_lon = (c[0] - BEIJING_CENTER_LNG) * A2PI
                d_lat = (c[1] - BEIJING_CENTER_LAT) * A2PI
                x = R * d_lon * Math.cos(m)
                y = R * d_lat
                x = x.m
                y = y.m

                p1 = [x - half_grid_size, y - half_grid_size, -0.5.m]
                p2 = [x - half_grid_size, y + half_grid_size, -0.5.m]
                p3 = [x + half_grid_size, y + half_grid_size, -0.5.m]
                p4 = [x + half_grid_size, y - half_grid_size, -0.5.m]
                face = entities.add_face([p1,p2,p3,p4])

                svf = g["svf"]
                color = get_svf_color(svf)
                face.material = face.back_material = color
                grid_count += 1

                sum_svf += svf
                if svf < min_svf
                    min_svf = svf
                elsif svf > max_svf
                    max_svf = svf
                end                        
            end
            p "一共导入#{grid_count}个网格点"
            ave_svf = grid_count == 0 ? 0 : sum_svf/grid_count
            p "SVF平均值#{ave_svf},最大值#{max_svf}，最小值#{min_svf}"

        rescue Exception => e
            MoosasUtils.rescue_log(e)
            UI.messagebox "导入城市光环境数据失败"
        end
    end

end