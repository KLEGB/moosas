
class MoosasRadiance
    Ver='0.6.4'

    def self.calculate_radiance()
        Sketchup.active_model.start_operation("辐射分析", true)

        t1 = Time.new
        model = Sketchup.active_model

        selection =[]
        MMR.traverse_faces(model.selection){|e,path|selection.push(e)}
        # Find all grids in the selection
        grids = []
        selection.each { |ent|
            # A grid is identified by having the "SunHours_grid_properties" attribute dictionary
            if ent.attribute_dictionaries and ent.attribute_dictionaries["grid"]
                grids << ent
            end
        }
        # If no grids are found in the selection, inform the user and stop immediately
        if grids.length == 0
            ent=MoosasGrid.fit_grids()
            if ent==nil or ent.length==0
                p "**Error: Grids are not found or fail to create Grids"
                return 
            else
                grids=ent
            end
        end

        self.calculate_grid_radiance(grids)

        selection=model.selection
        selection.clear
        selection.add(grids)
        description="Solar Radiation Intensity\nLocation:#{MoosasWeather.singleton.station_info["city"]}\nPriod:Annual"

        scaleRender=MoosasGridScaleRender.new(0,1500,description = description,unit='kWh/m2',colors=MoosasGrid.color_setting["radiance"]["colours"])
        
        scaleRender.draw_panel(Sketchup.active_model.selection)

        #Moosas::GridScaleObservers[model].showScale
        #Moosas::GridScaleObservers[model].showGridStasticsInfo

        t2 = Time.new

        p "Radiance analysis duration #{t2-t1}s"
        Sketchup.active_model.commit_operation
    end

    def self.calculate_position_radiance(position,model,cum_sky)
        #model = Sketchup.active_model
        if position != nil and position != false
            #begin
                position=position.to_a.each{ |b| b.to_f.round(2) }
                #puts "x = #{x},y=#{y}"
                rad = 0
                for i in 0..cum_sky.length-1
                    ray = [position, cum_sky[i][0]]   
                    #puts ray
                    begin
                        if model.is_a?(Sketchup::Model)
                            intersection = model.raytest(ray,true)
                        else
                            #p "face_test #{model.length}"
                            intersection = self.intersection(ray,model)
                        end
                        #p intersection
                    rescue Exception => e
                        #p "daylight error: #{ray}"
                    end    
                    if not intersection
                       rad += cum_sky[i][1]
                    end
                end
            #rescue
            #    rad = 0
            #end
            
        else
            rad = 0
        end
        return rad
    end

    def self.calculate_grid_radiance(grids)

        model = Sketchup.active_model
        model_dict = model.attribute_dictionary("Grids", false)
        cum_sky_value = $current_CumSky.m_CumSky #使用全年辐射数据
        entities = model.entities.add_group.entities

        #计算网格的采光系数值
        result = []
        sum=0
        number=0
        #MoosasCumSky.load_cum_sky_from_file(MoosasWeather.station_id)
        #raw_cum_sky = MoosasCumSky.get_cum_sky_with_patch_position
        #cum_sky = []
        #ave_sky_lum = 0
        #raw_cum_sky.each do |p|
        #    cum_sky.push([ Geom::Vector3d.new(p[0], p[1], p[2]), p[3]])
        #    ave_sky_lum += p[3]
        #end
        #p cum_sky
        #ave_sky_lum /= 145.0
        

        # 隐藏玻璃面
        MoosasRender.hide_glazing

        gridnum = 0

        grids.each { |grid|

            gridnum+=1

            # Fetch grid info
            dict = grid.attribute_dictionaries["grid"]
            dict['text']=entities
            nodes = dict["nodes"]

            # 投影辐射值
            cum_sky=$current_CumSky.get_cum_sky(Geom::Vector3d.new(dict["norm"]),cum_sky_value)
            # Number of grid cells in the x and y directions
            nx = nodes[0].length-1
            ny = nodes.length-1    
            #p "nx=#{nx},ny=#{ny}"
            # Give the grid an ID if it doesn't already have one
            if not dict["id"]
                dict["id"] = model_dict["grid_id"]
                # Update the model's next available ID
                model_dict["grid_id"] += 1
            end

            radGrid = []
            min = Float::INFINITY
            max = 0 - Float::INFINITY
            #sum = 0.0
            #number = 0

            #p nodes

            for y in 0..ny
                row = []
                for x in 0..nx
                    node = nodes[y][x] # This is a Point3d (actually it's just a 3-element array)
                    # If the node is valid (i.e. included in the grid)
                    rad = calculate_position_radiance(node,model,cum_sky)
                    max = rad if rad > max
                    min = rad if rad < min
                    sum += rad
                    number += 1
                    row.push(rad)
                end
                radGrid.push(row)
            end

            dict["results"] = radGrid
            dict["minRad"] = min
            dict["maxRad"] = max 
            dict["valueRange"] = 1500  #1000000.0 #认为最大辐射值为1500kWh/m2 #马克！
            dict["type"] = "radiance"

            p "Grid#{gridnum}, Maximum intensity=#{max}kwh/m2"

            p "Average intensity#{sum / number}"

            #p radGrid
            result.push(radGrid)

            Sketchup.status_text="Analize" + (grids.length>1 ? (" #{gridnum} grid，#{grids.length} in total") : "") + "..."
        }

        grids.each { |grid|
            #3.渲染网格值
            MoosasGrid.color_grid(grid)
        }

        MoosasRender.show_all_face

        return result
    end

    def self.intersection(ray,model)
        model.each do |face|
            n = face.normal
            u = ray[1]
            #p n,u
            if n*u == 0 #平行时不相交
                #p 'parellel'
                next 
            end
            n.length = 1
            u.length = 1
            p0 = face.vertices[0].position
            p1 = Geom::Point3d.new(ray[0])
            #p p0,p1
            '''
                平面参数方程: (P - p0).n = 0
                射线参数方程: P(t) = p1 + tu
                相交点方程：(P(t) - p0).n = (p1 + tu - p0).n = 0
                解得： P(t) = p1 + t*u = p1 + ((p0 - p1).n/u.n) * u
            '''
            t = ((p0 - p1)%n)/(n%u)
            if t < 0 # t<0时为负方向相交，即不相交
                #p  "#{t}"
                next 
            end
            u.length = u.length * t
            pt = p1 + u 
            if face.classify_point(pt) == Sketchup::Face::PointInside
                #p 'intersect'
                return true 
            end
        end
        #p 'no intersect'
        return false
    end

end