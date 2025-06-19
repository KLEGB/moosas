class MoosasVent
    Ver='0.6.4'
    def self.analysis()
        # 朝向转换角度：西向（0）、南向（90）、东向（180）、北向（270）
        if $language == 'Chinese'
            prompts = ["风速：", "风向：", "计算热压通风"]
            defaults = ["3.0", "225", "No"]
            lists=["","","No|Yes"]
            input = UI.inputbox(prompts, defaults,lists, "请输入室外风况条件！")
        else
            prompts = ["Wind Speed", "Wind Direction", "Simulate Thermal Ventilation"]
            defaults = ["3.0", "225", "No"]
            lists=["","","No|Yes"]
            input = UI.inputbox(prompts, defaults,lists, "Please Enter The Wind Condition")
        end
        wind_speed, wind_direction = input[0].to_f, 270 - input[1].to_i
        if input[2]=='Yes'
            thermal = true
            if $language == 'Chinese'
            prompts = ["模拟室外温度", "模拟室内温度"]
            defaults = ["20", "27"]
            input = UI.inputbox(prompts, defaults, "请输入室外风况条件！")
        else
            prompts = ["Outdoor Temperature", "Indoor Temperature"]
            defaults = ["20", "27"]
            input = UI.inputbox(prompts, defaults, "Please Enter The Temperature Settings")
        end
        out_temp,in_temp = input[0].to_f,input[1].to_f
        else
            thermal = false
            out_temp,in_temp = 20.0,20.0
        end
        alpha = 0.22
        if wind_direction < 0
            wind_direction = 360 + wind_direction
        end
        t1 = Time.new
        ach = calculate_ach($current_model, wind_speed, wind_direction, out_temp,in_temp,alpha,thermal)
        t2 = Time.new
        p "全建筑换气次数：#{ach} 次/小时"
        p "通风分析用时： #{t2-t1}s"
    end

    def self.calculate_ach(model, wind_speed, wind_direction,out_temp,in_temp, alpha,thermal)
        zones, paths, paths_inner, bdh, params, heights, rv = [], [], {}, calculate_bdh(model), "", [], 0
        for i in 0..model.spaces.length - 1 do
            s = model.spaces[i]
            vertices_=[]
            s.floor.each{|floor| floor.face.vertices.each{|ver| vertices_.push(ver)}}
            z = (s.area_m * s.height_m).round(2).to_s  + "," + self.calculate_midpoint(vertices_)
            vertices_.each do |v|
                x = (v.position[0].to_f * 2.54).round().to_s
                y = (v.position[1].to_f * 2.54).round().to_s
                z += "," + x + "," + y
            end
            zones.push(z)
            s.bounds.each do |b|
                b.glazings.each do |g|
                    h = self.calculate_height(g.face.vertices)
                    w = (g.area_m / h).round(2)
                    p = h.to_s + "," + w.to_s + "," + self.calculate_midpoint(g.face.vertices) + ","
                    if b.is_internal_edge
                        if paths_inner.include?(g.to_s)
                            paths.push(p + paths_inner[g.to_s] + "," + i.to_s + ",0")
                        else
                            paths_inner[g.to_s] = i.to_s
                        end
                    else
                        paths.push(p + "-1," + i.to_s + ",")
                        pi = pressure_input(wind_direction, bdh, b, g)
                        params += pi[0]
                        heights.push(pi[1])
                    end
                end
            end
            rv += s.area_m * s.height_m
        end
        # 调用xgb生成风压
        pressures = []
        xgbinput = MPath::DATA+"vent/xgb.input"
        xgboutput = MPath::DATA+"vent/xgb.output"
        File.write(xgbinput, params.chomp)
        if FileTest::exists?(xgboutput)
            File.delete(xgboutput)
        end
        code = ["from MoosasPy.vent import callXgb"]
        code+= ["callXgb(\"#{xgbinput}\",\"#{xgboutput}\")"]
        MoosasUtils.exec_python("ventXgb.pyw",code)
        MoosasUtils.wait(MPath::DATA+"vent/xgb.output")
        File.open(MPath::DATA+"vent/xgb.output","r") do |file|
            index = 0
            while line = file.gets
                pressures.push((line.to_f * 1.205 * (wind_speed ** 2) * ((heights[index] / 10) ** (alpha * 2)) / 2).round(2)) 
                index += 1
            end
        end
        # 给paths添加风压
        index = 0
        for i in 0..paths.length - 1 do
            if paths[i][-1] == ','
                paths[i] += pressures[index].to_s
                index += 1
            end
        end
        # 调用contam执行模拟
        pwd = MPath::VENT
        Dir.chdir pwd
        File.write("zones", zones.join("\n"))
        File.write("paths", paths.join("\n"))
        if thermal
            p 'calculating radiance heat gain...'
            roomheat = self.calculate_rooomheat(model)
        else
            roomheat = model.spaces.map{ |s| 0.0  }
        end
        zone_name = model.spaces.map{ |s| s.settings["zone_name"]  }
        thermal_param=(0..roomheat.length-1).map{ |i| [zone_name[i],in_temp,roomheat[i]].join(",") }
        thermal_param.push(['Outdoor',out_temp,-1].join(","))
        File.write("roomheat", thermal_param.join("\n"))
        p 'executing afn.exe...'
        system("afn.exe")
        if thermal 
            prjdict = MPath::VENT+"thermal"
            p 'executing Thermal Iteration...'
            self.run_auto_contamx(prjdict,t0=out_temp,max_iteration=10)
            # 等待result出现
            MoosasUtils.wait(MPath::DATA+"vent/result.csv")
            UI.openURL(MPath::DATA+"vent/result.csv")
        end
        # 输出建筑换气次数
        airVol=0
        # 等待airVol出现
        MoosasUtils.wait(pwd+"/airVol")
        Dir.chdir pwd
        File.open("airVol","r") do |file|
            airVol=file.gets.to_f 
        end

        # 可视化各外窗流量
        self.visulization(model,airVol/ rv)

        return (airVol/ rv).round(2)
    end
    def self.visulization(model,airVol)
        airVel = {}
        File.open("airVel","r") do |file|
            while line = file.gets
                av = line.split("|")
                airVel[av[0]] = av[1].to_f
            end
        end
        arrowLines = {} 
        vent = {}
        for i in 0..model.spaces.length - 1 do
            airVol_space=0
            s = model.spaces[i]
            s.bounds.each do |b|
                nor=b.normal
                nor.length=1
                b.glazings.each do |g|
                    vertices_=[]
                    s.floor.each{|floor| floor.face.vertices.each{|ver| vertices_.push(ver)}}
                    vel = airVel[self.calculate_midpoint(vertices_) + "," + self.calculate_midpoint(g.face.vertices)]
                    airVol_space += vel.abs()*g.area_m if b.is_internal_edge == false
                    arrowLines[g.id] = self.calculate_arrow(g,vel,nor)
                end
            end
            vent[s.id] = airVol_space.abs()*3600/2/s.area_m/s.height_m
        end
        self.flow_visualization(arrowLines.values,airVol)
        #self.room_visulization(vent)
    end
    def self.calculate_bdh(model)
        domain = [1e+9, -1e+9, 1e+9, -1e+9, 1e+9, -1e+9]
        model.spaces.each do |s|
            vertices_=[]
            s.floor.each{|floor| floor.face.vertices.each{|ver| vertices_.push(ver)}}
            vertices_.each do |v|
                vx = (v.position[0].to_f * 0.0254).round(2)
                vy = (v.position[1].to_f * 0.0254).round(2)
                vz = (v.position[2].to_f * 0.0254).round(2)
                if vx < domain[0]
                    domain[0] = vx
                elsif vx > domain[1]
                    domain[1] = vx
                end
                if vy < domain[2]
                    domain[2] = vy
                elsif vy > domain[3]
                    domain[3] = vy
                end
                if vz < domain[4]
                    domain[4] = vz
                elsif vz > domain[5] - s.height_m
                    domain[5] = vz + s.height_m
                end
            end
        end
        return [domain[1] - domain[0], domain[3] - domain[2], domain[5] - domain[4]]
    end

    def self.calculate_midpoint(vertices)
        c, x, y ,z = 0, 0, 0, 0
        vertices.each do |v|
            c += 1
            x += v.position[0].to_f * 2.54
            y += v.position[1].to_f * 2.54
            z += v.position[2].to_f * 2.54
        end
        return (x / c).round.to_s + "," + (y / c).round.to_s + "," + (z / c).round.to_s
    end

    def self.calculate_height(vertices)
        height = (vertices[1].position[2].to_f - vertices[0].position[2].to_f).abs
        backup = (vertices[2].position[2].to_f - vertices[1].position[2].to_f).abs
        if height < backup
            height = backup
        end
        return (height * 0.0254).round(2)
    end

    def self.pressure_input(wind_direction, bdh, b, g)
        ori, db, hb, index, reverse = calculate_orientation(b.normal), 0, 0, 0, 0
        if (ori > 45 and ori <= 135) or (ori > 225 and ori <= 315)
            db, hb = bdh[1] / bdh[0], bdh[2] / bdh[0]
        else
            db, hb = bdh[0] / bdh[1], bdh[2] / bdh[1]
            index = 1
        end
        theta = (ori - wind_direction).abs
        if theta > 180
            theta = 360 - theta
        end
        db, hb, theta = ((db - 0.4) / 2.1).round(2), ((hb - 0.1) / 0.9).round(2), (theta / 180).round(2)
        if db < 0
            db = 0
        elsif db > 1
            #db = g.face.vertices
            db = 1
        end
        if hb < 0
            hb = 0
        elsif hb > 1
            hb = 1
        end
        if ori <= 45 or ori > 225
            reverse = 1
        end
        domain = [1e+9, -1e+9, 1e+9, -1e+9]
        b.walls[0].face.vertices.each do |v|
            ht, hn = (v.position[2].to_f * 0.0254).round(2), (v.position[index].to_f * 0.0254).round(2)
            if ht < domain[0]
                domain[0] = ht
            elsif ht > domain[1]
                domain[1] = ht
            end
            if hn < domain[2]
                domain[2] = hn
            elsif hn > domain[3]
                domain[3] = hn
            end
        end
        ht, hn, c = 0, 0, g.face.vertices.length
        g.face.vertices.each do |v|
            ht += (v.position[2].to_f * 0.0254).round(2)
            hn += (v.position[index].to_f * 0.0254).round(2)
        end
        ht, hn = ht / c, hn / c
        height = ((ht - domain[0]) / (domain[1] - domain[0])).round(2)
        horizon = ((hn - domain[2]) / (domain[3] - domain[2])).round(2)
        if reverse == 1
            horizon = 1 - horizon
        end
        return [db.to_s + "," + hb.to_s + "," + theta.to_s + "," + height.to_s + "," + horizon.to_s + "\n", ht]
    end

    def self.calculate_orientation(n)
        o = Math.acos((-1) * (n[0]) / Math.sqrt((n[0])**2 + (n[1])**2)) * 180 / Math::PI
        if n[1] > 0
            o = 360-o
        end
        if o == 360
            o = 0
        end
        return o
    end

    def self.calculate_arrow(g,vel,nor)
        #p nor
        vel=0.01 if vel==0
        c, x, y ,z = 0, 0, 0, 0
        transformation=g.transformation
        g.face.vertices.each do |v|
            pt = transformation * v.position
            c += 1
            x += pt[0].to_f
            y += pt[1].to_f
            z += pt[2].to_f
        end
        x, y, z = x / c, y / c, z / c
        #nx, ny = n[0] / Math.sqrt((n[0])**2 + (n[1])**2), n[1] / Math.sqrt((n[0])**2 + (n[1])**2)
        centroid = Geom::Point3d.new(x,y,z)
        vector = Geom::Vector3d.new(nor)
        vector.length=vel
        return [centroid,vector,vel]
        #puts nx,ny
        #sx, sy, ex, ey = x, y, x + nx * l, y + ny * l
        #if l < 0
        #    sx, sy, ex, ey = x - nx * l, y - ny * l, x, y
        #end

        #a1 = [[ex, ey, z], [sx, sy, z]]
        #a2 = [[ex, ey, z], [(sx + ex) / 2, (sy + ey) / 2, z + l *0.5]]
        #a3 = [[ex, ey, z], [(sx + ex) / 2, (sy + ey) / 2, z - l *0.5]]
        #return [a1, a2, a3]
    end

    def self.flow_visualization(arrowLines,airVol)
        scale = 3/0.0254
        ent = Sketchup.active_model.entities.add_group
        ent=ent.entities

        vel_max = 0
        for i in 0..arrowLines.length - 1 do
            al = arrowLines[i]
            vel_max=[vel_max,al[2].to_f.abs()].max
        end
        vel_max=vel_max.round(1)
        description="Air Speed on Windows\nLocation:#{MoosasWeather.singleton.station_info["city"]}\nCodition:Wind pressure natural ventilation\nPriod:Summer\nTotal Air Change:#{airVol.round(2)} ACH"
        scaleRender=MoosasGridScaleRender.new(0,vel_max,description = description,unit='m/s',colors=[Sketchup::Color.new("Blue"),Sketchup::Color.new("Green"), Sketchup::Color.new("Yellow"),Sketchup::Color.new("Red")])
        scaleRender.draw_panel(Sketchup.active_model.selection)

        for i in 0..arrowLines.length - 1 do
            al = arrowLines[i]

            centroid = al[0]
            airarrow = Geom::Vector3d.new(al[1])
            horizonal = airarrow*Geom::Vector3d.new(0,0,1)
            vel = al[2]

            airarrow.length = vel.to_f.round(2).abs()*scale/2
            horizonal.length = airarrow.length/10

            ventilation_bar=ent.add_face([
                centroid-horizonal,
                centroid+horizonal,
                centroid+horizonal+airarrow,
                centroid+airarrow+airarrow,
                centroid-horizonal+airarrow,
            ])
            ventilation_bar.material = scaleRender.get_color(vel.to_f.round(2).abs())
            ventilation_bar.back_material = ventilation_bar.material
            lgtext = ent.add_group
            lgtext.entities.add_3d_text(vel.to_f.round(2).abs().to_s+'m/s',TextAlignLeft,"Arial",false,false,horizonal.length*2)
            lgtext.move!(centroid+Geom::Vector3d.new([0,0,0.1]))
            angle = airarrow.angle_between(Geom::Vector3d.new([1,0,0]))
            angle = -angle if airarrow[1]<0
            lgtext.transform!(Geom::Transformation.rotation(centroid,Geom::Vector3d.new([0,0,1]),angle))
            lgtext.material = Sketchup::Color.new ("Black")
        end
    end

    def self.room_visulization(vent)
        ent = Sketchup.active_model.entities.add_group
        ent=ent.entities
        description="Air Change Coefficiency of Rooms\nLocation:#{MoosasWeather.singleton.station_info["city"]}\nCodition:Wind pressure natural ventilation\nPriod:Summer"
        scaleRender=MoosasGridScaleRender.new(0,vent.values.max.round(1),description = description,unit='ACH',colors=[Sketchup::Color.new("Blue"),Sketchup::Color.new("Green"), Sketchup::Color.new("Yellow"),Sketchup::Color.new("Red")])
        #scaleRender.draw_panel(Sketchup.active_model.selection,origin=Geom::Vector3d.new([0,1,0]))
        $current_model.spaces.each{|space|
            col = scaleRender.get_color(vent[space.id])
            ach_text= vent[space.id].round(1).to_s + "ACH"
            lgtext = ent.add_group
            lgtext.entities.add_3d_text(ach_text,TextAlignCenter,"Arial",false,false,Math.sqrt(space.area_m)*4.5)
            midpoint=space.get_weight_center()
            lgtext.move!(Geom::Vector3d.new(midpoint)+Geom::Vector3d.new([-Math.sqrt(space.area_m)*12,0,0.1]))
            lgtext.material = col
            }
    end

    def self.run_auto_contamx(prjdict,t0 = 20,max_iteration = 10)
        Dir.chdir MPath::PYTHON
        File.open(MPath::DATA+"script/auto_contam.pyw","w+") do |f|
            f.puts "import os\n"
            f.puts "from MoosasPy import iterateProjects\n"
            f.puts "prjfiles = [for f in os.listdir(#{prjdict}) if f.endswith(.prj)]\n"
            f.puts "zonefiles = [for f in os.listdir(#{prjdict}) if f.endswith(.heat)]\n"
            f.puts "iterateProjects(prjfiles,zonefiles,#{MPath::DATA}vent/resultconcatResult.csv,outdoorTemperature=#{t0},maxIteration=#{max_iteration})\n"
        end
        begin
            system("python.exe \"#{MPath::DATA}script/auto_contam.pyw\"")
            return true
        rescue => e
             MoosasUtils.rescue_log(e)
             return false
        ensure 
            Dir.chdir MPath::VENT
        end
    end

    def self.calculate_rooomheat(model)

        t2 = Time.new
            $current_model.spaces.each{ |s| 
                #p "#{s.id}:#{s.settings['zone_summerrad']}"
                if s.settings['zone_summerrad'] == nil
                    s.calculate_zone_radation(model)
                end   
            }
        MoosasUtils.backup_setting_data()
        
        t3 = Time.new
        p "辐射计算用时： #{t3-t2}s"

        roomheat = []
        model.spaces.each{ |s|
            heat = s.settings['zone_summerrad'].to_f / (5832-3624)*1000
            heat += s.settings['zone_ppsm'].to_f * s.settings['zone_popheat'].to_f * s.area_m
            heat += s.settings['zone_equipment'].to_f * s.area_m
            heat += s.settings['zone_lighting'].to_f * s.area_m
            roomheat.push(heat)
          }
        return roomheat
    end
end
