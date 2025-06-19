
class MoosasDaylight
    Ver='0.6.3'
    class << self
        attr_accessor :current_grids,:ssg #sourrouding_shading_geometry
    end

    def self.local_analysis_daylight(space_id)
        
        rendered=true
        if $language == 'Chinese'
            result = UI.messagebox('需要分析全部空间吗?', MB_YESNO)
        else
            result = UI.messagebox('Analizing all spaces?', MB_YESNO)
        end
        analysis_faces = []
        transformations = []
        if result == IDYES
            $current_model.spaces.each do |s|
                s.floor.each{|f| 
                    analysis_faces.push(f.face)
                    transformations.push (f.transformation)
                }
            end
        else
            #选择分析的房间编号
            #prompts = ["空间编号："]
            #defaults = ["0"]
            #input = UI.inputbox(prompts, defaults, "请输入待分析的空间编号！")
            #space_id = input[0].to_i()
            p "Analize the space No.#{space_id}"
            $current_model.spaces[space_id.to_i].floor.each{|fl| 
                analysis_faces.push(fl.face)
                transformations.push(fl.transformation)
            }
        end

        model = Sketchup.active_model
        entities = model.active_entities
        selection = model.selection   
        if $language == 'Chinese'
            prompts = ["网格大小：","网格高度：","模拟时间：","天空模型"]
            defaults = ["0.5","0.72","01-20-14:00","晴朗天空，清澄大气"]
            params=defaults
            params.push(15000)
            lists=["","","","晴朗天空，清澄大气|晴朗天空，浑浊大气|多云天空，太阳的周边亮|多云天空，看不见太阳|全阴天"]
            input = UI.inputbox(prompts, defaults,lists, "请输入采光计算参数")
            params[0] = input[0].to_f()
            params[1] = input[1].to_f()
            params[2] = input[2]
            params[3] = input[3]

            if input[3] == "全阴天"
                uni_diff = UI.inputbox(["全阴天照度"], ["15000"], "全阴天模拟设定")
                params[4] = uni_diff[0].to_f()
            end
        else
            prompts = ["Grid size","Reference height","Date and time","Sky model"]
            defaults = ["0.5","0.72","01-20-14:00","clear sky"]
            params=defaults
            params.push(15000)
            lists=["","","","clear sky|clear sky without sun|cloudy sky|cloudy sky without sun|uniform sky"]
            input = UI.inputbox(prompts, defaults,lists, "Please enter required simulation parameters")
            params[0] = input[0].to_f()
            params[1] = input[1].to_f()
            params[2] = input[2]
            params[3] = input[3]

            if input[3] == "uniform sky"
                uni_diff = UI.inputbox(["sky illuminance(lux)"], ["15000"], "uniform sky illuminance")
                params[4] = uni_diff[0].to_f()
            end
        end
        #p params[4]
        #rendered=(input[4]=="Y")
        rendered=true

        #导出rad文件
        #if $exported_model_updated_number != $model_updated_number
            self.export_radiance_geometry(params)
            #p "成功导出几何文件"
        #    $exported_model_updated_number = $model_updated_number
        #end

        #grids = MoosasGrid.fit_selection(selection, model, entities, faces,params,true,global_transformation)
        grids = MoosasGrid.fit_grids_for_horizational_face(entities,analysis_faces,transformations,params,rendered)

        #p grids
        self.export_grid_file(grids)
        #p "成功导出分析网格"
        p "RADIANCE export successfully. Executing *.bat......"
        #if rendered == true
        #    scaleObserver = Moosas::GridScaleObservers[model]
        #    scaleObserver.closeScale() if scaleObserver
        #    scaleObserver.clearGridStasticsInfo() if scaleObserver
        #end

        #调用radiance文件进行计算
        if self.execute_radiance_bat_script()
            #读取结果,并将结果赋予grid
            valuerange=self.assign_result_to_grid(grids)
            params.push(valuerange)
        end

        #采光模拟结果数据备份
        MoosasDaylight.current_grids = grids 
        #p grids

        if rendered == true
            MoosasDaylight.render_daylight_in_skp(params)
            # #可视化方式一：在SketchUp模型中渲染网格
            # grids.each do |grid|
            #     MoosasGrid.color_grid(grid)
            # end
            # selection.clear
            # selection.add(grids)
            # Moosas::GridScaleObservers[model].showScale
            # Moosas::GridScaleObservers[model].showGridStasticsInfo
        else
            #可视化方式二：在html上绘制结果
            daylight_gird_data = [] 
            grids.each do |grid|
                daylight_gird_data.push MoosasGrid.pack_grid_data(grid)
            end
            daylight_result = {
                "grids"  => daylight_gird_data
            }
            #p daylight_result
            MoosasWebDialog.send("update_daylight_webgl",daylight_result)
        end
        
        
    rescue => e
        MoosasUtils.rescue_log(e)
    end

    def self.render_daylight_in_skp(params)
        Sketchup.active_model.start_operation("采光渲染", true)
        #可视化方式一：在SketchUp模型中渲染网格
        MoosasDaylight.current_grids.each do |grid|
            MoosasGrid.color_grid(grid)
        end
        model = Sketchup.active_model
        entities = model.active_entities
        selection = model.selection
        selection.clear
        selection.add(MoosasDaylight.current_grids)
        description="Point in Time Simulation\nLocation:#{MoosasWeather.singleton.station_info["city"]}\nPriod:#{params[2]}\nSky model:#{params[3]}"
        if $language == 'Chinese'
            prm = "全阴天"
        else
            prm = "uniform sky"
        end
        if params[3] == prm
            description+="\nIlluminance:#{params[4]}"
        end
        scaleRender=MoosasGridScaleRender.new(0,params[5],description = description)
        scaleRender.draw_panel()
        #Moosas::GridScaleObservers[model].showScale
        #Moosas::GridScaleObservers[model].showGridStasticsInfo
        Sketchup.active_model.commit_operation
    end

    def self.execute_radiance_bat_script

        pwd = MPath::RAD
        Dir.chdir pwd 

        t1 = Time.new
        begin
            system("run_moosas.bat")
            return true
        rescue => e
             MoosasUtils.rescue_log(e)
             return false
        ensure 
            Dir.chdir File.dirname(__FILE__)
        end


        t2 = Time.new

        p "Simulation duration#{t2-t1}s"
    end

    def self.assign_result_to_grid(grids)
        rads = []
        
        output_file = MPath::RAD+"ill_moosas.output"
        File.open(output_file,"r").each_line do |line|
            if line != nil
                rads.push line.to_f()
            end
        end
        all_satis = 0.0
        all_i = 0
        i = 0
        valuerange=(rads.sort[(rads.length*0.8).to_i]/500).ceil()*500
        #p valuerange

        grids.each do |grid|
            dict = grid.attribute_dictionaries["grid"]
            nodes = dict["nodes"]
            results = []
            nodes.each do |row|
                rad_row = [] 
                row.each do |node| 
                    if node 
                        rad_row.push rads[i]
                        i += 1
                    else
                        rad_row.push 0.0
                    end
                end
                results.push rad_row
            end
            dict["results"] = results
            dict["type"] = "illuminance"
            dict["valueRange"] = valuerange

            #统计外区参数
            satis = 0.0  #统计采光满足率 > 300 lux
            sum = 0.0
            min = 9999999.0
            n = 0   #外区网格数
            ny = nodes.length
            iy = 0
            j = 0
            nodes.each do |row|
                nx = row.length
                ix = 0
                row.each do |node| 
                    if node 
                        lux = rads[j]
                        if (iy < 6 or (ny -iy)<=6 ) and  (ix < 6 or (nx -ix)<=6 )  #属于外区
                            n += 1
                            if lux > 300
                                satis += 1
                            end
                            if lux < min
                                min = lux
                            end
                            sum += lux
                        end
                        j += 1
                    end
                    ix += 1
                end
                iy += 1
            end
            if n != 0
                all_satis = all_satis+satis
                satis =  satis / n * 100
                
                all_i = all_i+n
                ave = sum / n
                sameness = min / ave   #统计采光均匀度 一个值
                p "Daylighting satifaction of outer zone(>300lux) = #{format("%04.2f",satis)}%"
                p "Daylighting uniformity = #{format("%03.2f",sameness)}"
            end

        end
        all_satis=all_satis/all_i
        p "Average satification(>300lux) = #{format("%04.2f",all_satis)}%"
        return valuerange
    end

    IDENTITY_TRANSFORMATION = Geom::Transformation.new


    #可进一步优化，只获取待分析建筑周围的几何体
    def self.export_radiance_geometry(params)

        geo_text = ""

        mofaces=$current_model.get_all_face

        mofaces.each{|mf|
            if mf.type != MoosasConstant::ENTITY_IGNORE and not mf.face.deleted?
                e=mf.face
                pts = e.vertices.map {|v|  
                    pt = mf.transformation * v.position
                    [pt.x * 0.0254,pt.y * 0.0254,pt.z * 0.0254]
                }
                geo_text += self.format_face_text(mf.id, pts,mf.material)+ "\n"
            end
        }

        rad_text = self.get_sky(params) + "\n" +get_material_lib()  + "\n"+geo_text
        rad_file =MPath::RAD+"model.rad"
        File.open(rad_file,"w+") do |f|
            f.puts rad_text
        end
    end

    def self.get_mesh_polygons(mesh,transformation)
        tpts = mesh.points.map{ |x|  transformation * x}
        polys = []
        #p "tpts=#{tpts}"
        for pol in mesh.polygons
            pts = []
            #p "pol=#{pol}"
            for i in 0..2
                pi = tpts[pol[i].abs-1]
                pt = [pi.x * 0.0254, pi.y * 0.0254, pi.z * 0.0254]
                pts.push(pt)
            end
            polys.push(pts)
        end
        return polys
    end

    def self.is_glazing(face)
        if face.material && face.material.alpha < MoosasConstant::MATERIAL_ALPHA_THRESHOLD
            return true
        else
            return false
        end
    end

    def self.format_face_text(poly_name, pts,idx)
        material_name=$rad_lib[idx].category+"_"+$rad_lib[idx].name
        text =  material_name+" polygon #{poly_name} 0 0 #{pts.length*3}\n"
        pts.each do |pt|
            text += "   #{pt[0]} #{pt[1]} #{pt[2]}\n"
        end
        return text
    end

    def self.get_material_lib()
        '''
        sketch_win：根据用户设定的可见光透过率来设定
        Visible Light Transmittance (VLT) : Tn
        =>    void glass sketch_win 0 0 3 tn tn tn 
        =>    tn =  (Math.sqrt(0.8402528435+0.0072522239*Tn*Tn)-0.9166530661)/0.0036261119/Tn
        => VLT : 0.737, tn = 0.803
        => VLT : 0.803, tn = 0.874
        => VLT : 0.915, tn = 0.996
        '''
        lines=["####Materials"]
        rad_lab=$current_model.get_all_rad_material
        rad_str=rad_lab.keys.each{|idx|
            material=$rad_lib[idx]
            lines.push(["void",material.rad_mat["type"],material.category+"_"+material.name].join(" "))
            lines.push("0")
            lines.push("0")
            if material.rad_mat["type"]=="plastic"
                lines.push(["5",material.rad_mat["R"],material.rad_mat["G"],material.rad_mat["B"],material.rad_mat["spec"],material.rad_mat["rough"]].join(" "))
            elsif material.rad_mat["type"]=="glass"
                tn=[material.rad_mat["R"],material.rad_mat["G"],material.rad_mat["B"]].each{|trans| (Math.sqrt(0.8402528435+0.0072522239*trans.to_f*trans.to_f)-0.9166530661)/0.0036261119/trans.to_f}
                lines.push(["3",tn[0].to_s,tn[1].to_s,tn[2].to_s].join(" "))
            elsif material.rad_mat["type"]=="trans"
                lines.push(["7",material.rad_mat["R"],material.rad_mat["G"],material.rad_mat["B"],material.rad_mat["spec"],material.rad_mat["rough"],0,0].join(" "))
            end    
        }
        lines.push("")
        lines.push("####Materials")
        return lines.join("\n")
    end

    def self.get_sky(params)
        date=params[2].split('-')
        date[2]=date[2].split(':')[0]
        sky=MoosasCIESky.new(MoosasCIESky::SKY_TYPE[params[3]],params[4])
        #sky=MoosasCIESky.new()
        sky_str=sky.gen_sky_from_date(datetime=date)
        return sky_str
    end

    def self.export_grid_file(grids)
        lines = []
        grids.each do |grid|
            nodes = grid.get_attribute("grid", "nodes")
            #t_nodes = []
            nodes.each do |row|
                #t_row = []
                row.each do |node|
                    if node
                        x = (node[0]*0.0254).round(5)
                        y = (node[1]*0.0254).round(5)
                        z = (node[2]*0.0254).round(5)
                        lines.push "#{x} #{y} #{z} 0 0 1"
                    end
                    #t_row.push(node)
                end
                #t_nodes.push(t_row)
            end
            #grid.set_attribute("grid", "nodes",t_nodes)
        end
        text = lines.join("\n")
        grid_file = MPath::RAD+"grid.input"
        File.open(grid_file,"w+") do |f|
            f.puts text
        end
    end

    def self.get_ent_global_transformantion(ent)
        instance_paths = self.collect_occurences(ent)
        p "instance_paths=#{instance_paths}"
        global_transformation = self.get_transformation_for_instance_path(instance_paths)
        return global_transformation
    end

    def self.get_transformation_for_instance_path(instance_path)
        transformation =   Geom::Transformation.new()
        instance_path.reject{ |noninstance| # Model or DrawingElement do not have a transformation.
            !noninstance.respond_to?(:transformation)
        }.each{ |instance|
            transformation *= instance.transformation
        }
        p "get_transformation_for_instance_path=#{transformation}"
        return transformation
    end

    def self.collect_occurences(instance)
        instance_paths = []
        queue = [ [instance] ]
        until queue.empty?
            path = *(queue.shift)
            outer = path.first
            if outer.parent.is_a?(Sketchup::Model)
                instance_paths << path
            else
                outer.parent.instances.each{ |uncle|
                queue << [uncle] + path
            }
            end
        end
        return instance_paths
    end

    def self.traverse_faces(entity, path=[], &func)
        case entity
        when Sketchup::Face
            func.arity == 1 ? func.call(entity) : func.call(entity, path)
        when Sketchup::Group 
            traverse_faces(entity.entities, path + [entity], &func)
        when Sketchup::ComponentInstance
            traverse_faces(entity.definition.entities, path + [entity], &func)
        when Sketchup::Entities, Sketchup::Selection, Enumerable
            entity.each {|e| traverse_faces(e,path,&func)}
        end
    end

    def self.user_visible?(e)
        e.visible? && e.layer.visible?
    end



    #快速估算采光系数值 
    def self.quick_analysis_ave_daylight_factor(model)
        spaces = model.spaces
        sn = spaces.length
        dfs = []
        light_transmittance = 0.6 #采光透过率
        for i in 0..sn-1
            s = spaces[i]
            floor_area = s.area_m
            window_area = 0.0
            s.bounds.each do |b|
                if not b.is_internal_edge
                    window_area += b.area_m * b.wwr
                end
            end
            df = 45 * window_area * light_transmittance / floor_area / 0.76
            if df > 100
                df = 100
            end
            dfs.push [df,floor_area]
        end
        return dfs
    end

    # 旧版本backup
    def self.format_wall_text(poly_name, pts)
        text =  "sketch_wall polygon #{id} 0 0 #{pts.length*3}\n"
        pts.each do |pt|
            text += "   #{pt[0]} #{pt[1]} #{pt[2]}\n"
        end
        return text
    end

    def self.format_glazing_text(id,pts)
        text =  "sketch_win polygon #{id} 0 0 #{pts.length*3}\n"
        pts.each do |pt|
            text += "   #{pt[0]} #{pt[1]} #{pt[2]}\n"
        end
        return text
    end

    #标注周围遮挡的面，纳入计算
    def self.label_sourrouding_shading
    end
end

$exported_model_updated_number = nil