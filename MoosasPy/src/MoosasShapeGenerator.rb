class MoosasShapeGenerator

    '''
        params = []
        L1:底层南向长度
        L2:底层西向长度
        n: 层数
        h: 层高
        s：顶层与首层边长比例
        t：顶层与首层偏转角度
        wwri：[],东、南、西、北窗墙比
    '''
    def self.generate_parametric_building(params)

        p "generate_parametric_building #{params}"

        type = params[0].to_f
        type = type.round()
        case type
        when 0  #矩形
            building = self.generate_rectangle_building(params)
        when 1  #三角形
            building = self.generate_triangle_building(params)
        when 2  #L形
            building = self.generate_l_shape_building(params)
        when 3  #凹形
            building = self.generate_spill_shape_building(params)
        when 4 #paper 定制的形状
            building = self.generate_paper_shape_building(params)
        else
            building = nil
        end

        return building
    end


    def self.generate_rectangle_building(params)
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1 / 2.0
            il2 = l2 / 2.0

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m

            pts = []
            pts.push Geom::Point3d.new(0.0 - il1, 0 - il2 ,h1)
            pts.push Geom::Point3d.new(0.0 + il1, 0 - il2 ,h1)
            pts.push Geom::Point3d.new(0.0 + il1, 0 + il2 ,h1)
            pts.push Geom::Point3d.new(0.0 - il1, 0 + il2 ,h1)
            pts.push Geom::Point3d.new(0.0 - il1, 0 - il2 ,h2)
            pts.push Geom::Point3d.new(0.0 + il1, 0 - il2 ,h2)
            pts.push Geom::Point3d.new(0.0 + il1, 0 + il2 ,h2)
            pts.push Geom::Point3d.new(0.0 - il1, 0 + il2 ,h2)

            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[3],pts[2],pts[1],pts[0]]
            front,w1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[5],pts[4]],wwr_south)
            right,w2 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[6],pts[5]],wwr_east)
            back,w3 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[7],pts[6]],wwr_north)
            left,w4 = self.generate_face_wwr(entities,[pts[3],pts[0],pts[4],pts[7]],wwr_west)
            top = entities.add_face [pts[4],pts[5],pts[6],pts[7]]
        end

        return group
    end

    def self.generate_triangle_building(params)
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1
            il2 = l2

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m

            pts = []
            pts.push Geom::Point3d.new(0.0, 0, h1)
            pts.push Geom::Point3d.new(il1, 0, h1)
            pts.push Geom::Point3d.new(0.0, il2, h1)
            pts.push Geom::Point3d.new(0.0, 0, h2)
            pts.push Geom::Point3d.new(il1, 0, h2)
            pts.push Geom::Point3d.new(0.0, il2, h2)

            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[2],pts[1],pts[0]]
            front,w1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[4],pts[3]],wwr_south)
            right,w2 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[5],pts[4]],wwr_east)
            left,w3 = self.generate_face_wwr(entities,[pts[2],pts[0],pts[3],pts[5]],wwr_west)
            top = entities.add_face [pts[3],pts[4],pts[5]]
        end

        return group
    end

    def self.generate_l_shape_building(params)
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1
            il2 = l2

            il3 = l1 * 0.4
            il4 = l2 * 0.4

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m
            il3 = il3.m
            il4 = il4.m

            pts = []
            pts.push Geom::Point3d.new(0.0, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, il4 ,h1)
            pts.push Geom::Point3d.new(il1, il4 ,h1)
            pts.push Geom::Point3d.new(il1, il2 ,h1)
            pts.push Geom::Point3d.new(0, il2 ,h1)

            pts.push Geom::Point3d.new(0.0, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, il4 ,h2)
            pts.push Geom::Point3d.new(il1, il4 ,h2)
            pts.push Geom::Point3d.new(il1, il2 ,h2)
            pts.push Geom::Point3d.new(0, il2 ,h2)


            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]

            s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[7],pts[6]],wwr_south)
            e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[8],pts[7]],wwr_east)
            s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[9],pts[8]],wwr_south)
            e2,we2 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[10],pts[9]],wwr_east)
            n1,wn1 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[11],pts[10]],wwr_north)
            w1,ww1 = self.generate_face_wwr(entities,[pts[5],pts[0],pts[6],pts[11]],wwr_west)

            top = entities.add_face [pts[6],pts[7],pts[8],pts[9],pts[10],pts[11]]
        end

        return group
    end

    def self.generate_spill_shape_building(params)
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1
            il2 = l2

            il3 = l1 * 0.3
            il4 = l2 * 0.4
            il5 = l1 * 0.7

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m
            il3 = il3.m
            il4 = il4.m
            il5 = il5.m

            pts = []
            pts.push Geom::Point3d.new(0.0, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, il4 ,h1)
            pts.push Geom::Point3d.new(il5, il4 ,h1)
            pts.push Geom::Point3d.new(il5, 0 ,h1)
            pts.push Geom::Point3d.new(il1, 0 ,h1)
            pts.push Geom::Point3d.new(il1, il2 ,h1)
            pts.push Geom::Point3d.new(0, il2 ,h1)

            pts.push Geom::Point3d.new(0.0, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, il4 ,h2)
            pts.push Geom::Point3d.new(il5, il4 ,h2)
            pts.push Geom::Point3d.new(il5, 0 ,h2)
            pts.push Geom::Point3d.new(il1, 0 ,h2)
            pts.push Geom::Point3d.new(il1, il2 ,h2)
            pts.push Geom::Point3d.new(0, il2 ,h2)


            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
            s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_south)
            e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_east)
            s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_south)
            w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_west)
            s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_south)
            e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_east)
            n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_north)
            w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_west)
            top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
        end

        return group
    end

    '''
        生成文章所有的建筑形体
    '''
    def self.generate_paper_shape_building(params)
        w1 = params[1]
        w3 = params[2]
        d11 = 40
        d21 = params[3]
        d31 = params[4]
        d41 = params[5]
        d12 = 32
        d22 = params[6]
        d32 = params[7]
        d42 = params[8] 


        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities


        self.add_single_floor_spill(entities,60,d11,w3,d11-d12,60-w1,0,6,40-d11)
        self.add_single_floor_spill(entities,60,d21,w3,d21-d22,60-w1,6.05,12.05,40-d21)
        self.add_single_floor_spill(entities,60,d31,w3,d31-d32,60-w1,12.1,18.1,40-d31)
        self.add_single_floor_spill(entities,60,d41,w3,d41-d42,60-w1,18.15,24.15,40-d41)

        return group
    end


    @roof_material = Sketchup.active_model.materials.add('Roof_M')
    @roof_material.color =  Sketchup::Color.new(102, 204, 0)
    def self.add_single_floor_spill(entities,il1,il2,il3,il4,il5,h1,h2,y_offset=0,with_window=true)
        wwr_east = 0.4
        wwr_south = 0.4
        wwr_west = 0.5
        wwr_north = 0.3

        h1 = h1.m
        h2 = h2.m
        il1 = il1.m
        il2 = il2.m
        il3 = il3.m
        il4 = il4.m
        il5 = il5.m

        y_offset = y_offset.m

        pts = []
        pts.push Geom::Point3d.new(0.0, 0.0+y_offset ,h1)
        pts.push Geom::Point3d.new(il3, 0.0+y_offset ,h1)
        pts.push Geom::Point3d.new(il3, il4+y_offset ,h1)
        pts.push Geom::Point3d.new(il5, il4+y_offset ,h1)
        pts.push Geom::Point3d.new(il5, 0+y_offset ,h1)
        pts.push Geom::Point3d.new(il1, 0+y_offset ,h1)
        pts.push Geom::Point3d.new(il1, il2+y_offset ,h1)
        pts.push Geom::Point3d.new(0, il2+y_offset ,h1)

        pts.push Geom::Point3d.new(0.0, 0.0+y_offset ,h2)
        pts.push Geom::Point3d.new(il3, 0.0+y_offset ,h2)
        pts.push Geom::Point3d.new(il3, il4+y_offset ,h2)
        pts.push Geom::Point3d.new(il5, il4+y_offset ,h2)
        pts.push Geom::Point3d.new(il5, 0+y_offset ,h2)
        pts.push Geom::Point3d.new(il1, 0+y_offset ,h2)
        pts.push Geom::Point3d.new(il1, il2+y_offset ,h2)
        pts.push Geom::Point3d.new(0, il2+y_offset ,h2)


        bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
        s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_south,with_window)
        e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_east,with_window)
        s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_south,with_window)
        w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_west,with_window)
        s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_south,with_window)
        e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_east,with_window)
        n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_north,with_window)
        w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_west,with_window)
        top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
        top.material = top.back_material = @wall_materail
    end


    @window_material = Sketchup.active_model.materials.add('Joe')
    @window_material.color =  Sketchup::Color.new(100,149,237)
    @window_material.alpha = 0.5
    @wall_materail =  Sketchup.active_model.materials.add('moosas_wall')
    @wall_materail.color =  Sketchup::Color.new(255,255,255)
    def self.generate_face_wwr(entities,pts,wwr,with_window=true)
        face =  entities.add_face pts

        face.material = face.back_material = @wall_materail


        if not with_window
            return [face,nil]
        end

        w = (1.0 - Math.sqrt(wwr)) / 2.0

        wpts = []
        wpts.push Geom::Point3d.linear_combination(1-w, pts[0], w, pts[2])
        wpts.push Geom::Point3d.linear_combination(1-w, pts[1], w, pts[3])
        wpts.push Geom::Point3d.linear_combination(1-w, pts[2], w, pts[0])
        wpts.push Geom::Point3d.linear_combination(1-w, pts[3], w, pts[1])

        window = entities.add_face wpts
        window.material = window.back_material = @window_material

        [face,window]
    end

    def self.generate_thu_env_building(ls)

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "thu_env_building#{(rand()*1000).round()}"
        entities = group.entities

        h = 0.0
        ls.each do |l|
            MoosasShapeGenerator.add_single_floor_spill(entities,56,l,16,l-18,36,h,h+4,57-l)
            h += 4.0
        end
    end

    #生成许多毕业的方案
    def self.generate_xuduo_building(params)
        with_window = true

        w = params[0]
        a = w * params[1]
        b = w * params[2]
        c_r = params[3]
        x = w * params[4]
        y = w * params[5]
        z_r = params[6]
        wwr_s = params[7]
        wwr_w = params[8]
        wwr_e = params[9]
        wwr_n = 0.2

        fn = (10000.0 / (w * w)).round()  #楼层数
        h = fn * 4.5   #层高

        fz = (fn * z_r).round()   #对应z的起始楼层
        z = fz * 4.5

        if z < 50
            c = (50 - z) * c_r
            fc = (c / 4.5).round()   #交错空间的层数
            if fc + fz > fn
                fc = fn - fz
            end5
        else
            c = 0
            fc = 0
        end

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        w = w.m
        a = a.m
        b = b.m
        c = c.m
        x = x.m
        y = y.m
        z = z.m

        i = 0
        shape_type = nil
        while i < fn
            if i < fz or i >= fz + fc
                shape_type = 0  #矩形
            else
                if x + a <= w
                    if y + b <= w  #嵌入其中
                        shape_type = 0
                    else
                        shape_type = 2
                    end
                else
                    if y + b <= w
                        shape_type = 1
                    else
                        shape_type = 3
                    end
                end
            end
            #p "shape_type=#{shape_type}"

            h1 = (i * 4.5).m
            h2 = ((i +1)* 4.5).m
            if shape_type == 0  #矩形
                pts  =  []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)
                bottom = entities.add_face [pts[3],pts[2],pts[1],pts[0]]
                self.generate_face_wwr(entities,[pts[0],pts[1],pts[5],pts[4]],wwr_s,with_window)
                self.generate_face_wwr(entities,[pts[1],pts[2],pts[6],pts[5]],wwr_e,with_window)
                self.generate_face_wwr(entities,[pts[2],pts[3],pts[7],pts[6]],wwr_n,with_window)
                self.generate_face_wwr(entities,[pts[3],pts[0],pts[4],pts[7]],wwr_w,with_window)
                top = entities.add_face [pts[4],pts[5],pts[6],pts[7]]
            elsif shape_type == 1  #x边超出，y边未超出
                pts = []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, y, h1)
                pts.push Geom::Point3d.new(x+a, y, h1)
                pts.push Geom::Point3d.new(x+a, y+b, h1)
                pts.push Geom::Point3d.new(w, y+b, h1)
                pts.push Geom::Point3d.new(w, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, y, h2)
                pts.push Geom::Point3d.new(x+a, y, h2)
                pts.push Geom::Point3d.new(x+a, y+b, h2)
                pts.push Geom::Point3d.new(w, y+b, h2)
                pts.push Geom::Point3d.new(w, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)

                bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
                s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_s,with_window)
                e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_s,with_window)
                w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_w,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_n,with_window)
                e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_e,with_window)
                n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_n,with_window)
                w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_w,with_window)
                top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]

            elsif shape_type == 2  #x边未超出,y边超出

                pts = []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, w, h1)
                pts.push Geom::Point3d.new(x+a, w, h1)
                pts.push Geom::Point3d.new(x+a, y+b, h1)
                pts.push Geom::Point3d.new(x, y+b, h1)
                pts.push Geom::Point3d.new(x, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, w, h2)
                pts.push Geom::Point3d.new(x+a, w, h2)
                pts.push Geom::Point3d.new(x+a, y+b, h2)
                pts.push Geom::Point3d.new(x, y+b, h2)
                pts.push Geom::Point3d.new(x, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)

                bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
                s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_s,with_window)
                e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_n,with_window)
                w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_n,with_window)
                e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_w,with_window)
                n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_n,with_window)
                w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_w,with_window)
                top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
            
            elsif shape_type == 3  #x边和y边均超出

                pts = []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, y, h1)
                pts.push Geom::Point3d.new(x+a, y, h1)
                pts.push Geom::Point3d.new(x+a, y+b, h1)
                pts.push Geom::Point3d.new(x, y+b, h1)
                pts.push Geom::Point3d.new(x, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, y, h2)
                pts.push Geom::Point3d.new(x+a, y, h2)
                pts.push Geom::Point3d.new(x+a, y+b, h2)
                pts.push Geom::Point3d.new(x, y+b, h2)
                pts.push Geom::Point3d.new(x, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)

                bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
                s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_s,with_window)
                e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_s,with_window)
                w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_n,with_window)
                e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_w,with_window)
                n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_n,with_window)
                w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_w,with_window)
                top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
            end
                    
            i += 1
        end
    end


    def self.test_xuduo()
        params = [30 + 70 * rand(),rand(),rand(),rand(),rand(),rand(),rand(),rand(),rand(),rand()]
        p "x=#{params}"
        MoosasShapeGenerator.generate_xuduo_building(params)
    end

    def self.test(type=0)
        params = [type,60.0,50.0,10,4.0,0.0,0.4,0.4,0.4,0.4]
        self.generate_parametric_building(params)
    end

end



end
