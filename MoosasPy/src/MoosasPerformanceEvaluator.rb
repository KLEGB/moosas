class MoosasPerformanceEvaluator
    Ver='0.6.1'

    '''
        计算体形系数和经济成本
    '''
    def self.evaluate_sc_and_economy(x)

        type = x[0].to_f
        type = type.round()

        case type
        when 0  #矩形
            result = self.evaluate_sc_and_economy_rectangle(x)
        when 1  #三角形
            result = self.evaluate_sc_and_economy_triangle(x)
        when 2  #L形
            result = self.evaluate_sc_and_economy_l_shape(x)
        when 3  #凹形
            result = self.evaluate_sc_and_economy_spill_shape(x)
        else
            result = nil
        end

        return result
    end

    '''
        矩形
    '''
    def self.evaluate_sc_and_economy_rectangle(x)
        l1 = x[1]
        l2 = x[2]
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = l1 * l2 * h * n
        wall = (l1 * h * (1-wwr_south) + l1 * h * (1-wwr_north) + l2*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south + l1 * h * wwr_north + l2*h*wwr_east+l2*h*wwr_west) * n 
        floor = l1 * l2 * n  #内部的水平结构
        roof = l1 * l2  #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]
    end

    '''
        三角形
    '''
    def self.evaluate_sc_and_economy_triangle(x)

        l1 = x[1]
        l2 = x[2]
        l3 = (l1 ** 2 + l2 ** 2) ** 0.5
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = l1 * l2 / 2 * h * n
        wall = (l1 * h * (1-wwr_south) + l3*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south +  l3*h*wwr_east+l2*h*wwr_west) * n 
        floor = l1 * l2 / 2 * n  #内部的水平结构
        roof = l1 * l2 / 2 #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]

    end

    '''
        L形
    '''
    def self.evaluate_sc_and_economy_l_shape(x)
        l1 = x[1]
        l2 = x[2]
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = (l1 * l2 - 0.6 * l1 * 0.6 * l2)*h * n
        wall = (l1 * h * (1-wwr_south) + l1 * h * (1-wwr_north) + l2*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south + l1 * h * wwr_north + l2*h*wwr_east+l2*h*wwr_west) * n 
        floor = (l1 * l2 - 0.6 * l1 * 0.6 * l2) * n  #内部的水平结构
        roof = (l1 * l2 - 0.6 * l1 * 0.6 * l2)  #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]
    end

    '''
        凹形
    '''
    def self.evaluate_sc_and_economy_spill_shape(x)
        l1 = x[1]
        l2 = x[2]
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = (l1 * l2 - 0.4 * l1 * 0.4 * l2) * h * n
        wall = (l1 * h * (1-wwr_south) + l1 * h * (1-wwr_north) + l2*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south + l1 * h * wwr_north + l2*h*wwr_east+l2*h*wwr_west) * n 
        floor = (l1 * l2 - 0.4*l1 *0.4*l2) * n  #内部的水平结构
        roof = (l1 * l2 - 0.4*l1 *0.4*l2)  #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]
    end


    '''
        计算体形系数和经济成本
    '''
    def self.evaluate_sc_and_economy_paper(x)
        w1 = x[0]
        w3 = x[1]
        d21 = x[2]
        d31 = x[3]
        d41 = x[4]
        d22 = x[5]
        d32 = x[6]
        d42 = x[7] 

        wwr_east = 0.4
        wwr_south = 0.4
        wwr_west = 0.5
        wwr_north = 0.3
        h = 6.0

        f1 = self.paper_calculate_floor_info(60,w1,w3,40,32,h,wwr_east,wwr_south,wwr_west,wwr_north)
        f2 = self.paper_calculate_floor_info(60,w1,w3,d21,d22,h,wwr_east,wwr_south,wwr_west,wwr_north)
        f3 = self.paper_calculate_floor_info(60,w1,w3,d31,d32,h,wwr_east,wwr_south,wwr_west,wwr_north)
        f4 = self.paper_calculate_floor_info(60,w1,w3,d41,d42,h,wwr_east,wwr_south,wwr_west,wwr_north)

        volumn = f1[3] + f2[3] + f3[3] + f4[3]
        wall = f1[1] + f2[1] + f3[1] + f4[1]
        window = f1[2] + f2[2] + f3[2] + f4[2]
        floor = f1[0] + f2[0] + f3[0] + f4[0]
        roof = f1[0]

        #计算体形系数
        sc = (wall + window + roof) / volumn
        energy = (sc * 100) ** 3 / 20 - 140
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)
        eco = (eco -1000) ** 3 / 1000 + 680

        return [energy,eco]
    end

    def self.paper_calculate_floor_info(w,w1,w3,d1,d2,h,we,ws,ww,wn)
        area = w * d1 - (w - w1 -w3) * (d1 - d2)
        volumn = area * h
        wall_area = w * h * (1-ws) + w * h * (1-wn) + d1 * h * (1-we) + d1 * h * (1-ww) + (d1 - d2) * h * (1-we) + (d1 - d2) * h * (1-ww)
        window_area = w * h * ws + w * h * wn + d1 * h * we + d1 * h * ww + (d1 - d2) * h * we + (d1 - d2) * h * ww
        return [area,wall_area,window_area,volumn]
    end

    ''' 
        计算清华节能楼的体形系数和经济成本
    ''' 
    def self.evaluate_thu_env_sc_and_economy(x)
        floor_info = []
        volumn = 0.0
        wall = 0.0
        window_wse = 0.0
        window_n = 0.0
        area = 0.0
        x.each do |l|
            f = self.calculate_thu_env_floor_info(56,16,20,l,18,4.0,0.7,0.7,0.7,0.2)
            floor_info.push(f)
            area += f[0]
            volumn += f[4]
            wall += f[1]
            window_wse += f[2]
            window_n += f[3]
        end

        floor = 0.0
        n = floor_info.length
        for i in 0..n-2
            floor += (floor_info[i][0] - floor_info[i+1][0]).abs
        end
        roof = floor_info[n-1][0]

        # p volumn
        # p floor
        # p roof
        # p window_wse
        # p window_n
        outer_surface_area = wall + window_wse +window_n+ roof+floor

        #计算体形系数
        sc = outer_surface_area*0.9 / volumn

        #计算平米围护结构造价
        eco = (350 * wall  + 1250 * window_wse + 1250 * window_n) #/ (wall + window_wse +window_n)

        p "wall=#{wall},window_wse=#{window_wse},window_n=#{window_n}"


        return [sc,eco]
    end

    def self.calculate_thu_env_floor_info(w,w1,w3,d1,d2,h,we,ws,ww,wn)
        area = w * d1 - (w - w1 -w3) * (d1 - d2)
        volumn = area * h
        wall_area = w * h * (1-ws) + w * h * (1-wn) + d1 * h * (1-we) + d1 * h * (1-ww) + (d1 - d2) * h * (1-we) + (d1 - d2) * h * (1-ww)
        window_area_wse = w * h * ws  + d1 * h * we + d1 * h * ww + (d1 - d2) * h * we + (d1 - d2) * h * ww
        window_area_n = w * h * wn
        return [area,wall_area,window_area_wse,window_area_n,volumn]
    end

    ''' 
        计算清华节能楼的能耗和经济成本
    ''' 
    def self.evaluate_thu_env_energy_and_economy(x)

        floor_info = []
        volumn = 0.0
        wall = 0.0
        window_wse = 0.0
        window_n = 0.0
        area = 0.0
        x.each do |l|
            f = self.calculate_thu_env_floor_info(56,16,20,l,18,4.0,0.7,0.7,0.7,0.2)
            floor_info.push(f)
            area += f[0]
            volumn += f[4]
            wall += f[1]
            window_wse += f[2]
            window_n += f[3]
        end

        floor = 0.0
        n = floor_info.length
        for i in 0..n-2
            floor += (floor_info[i][0] - floor_info[i+1][0]).abs
        end
        roof = floor_info[n-1][0]

        # p volumn
        # p floor
        # p roof
        # p window_wse
        # p window_n
        outer_surface_area = wall + window_wse +window_n+ roof+floor

        #计算体形系数
        energy = outer_surface_area*0.9 / volumn * 600.0

        #计算平米围护结构造价
        eco = (350 * wall  + 1250 * window_wse + 1250 * window_n) #/ (wall + window_wse +window_n)

        #p "wall=#{wall},window_wse=#{window_wse},window_n=#{window_n}"


        return [energy,eco]
    end

    def self.calculate_thu_env_floor_zone_and_floor(w,w1,w3,d1,d2,h,we,ws,ww,wn)
        area = w * d1 - (w - w1 -w3) * (d1 - d2)
        volumn = area * h
        wall_area = w * h * (1-ws) + w * h * (1-wn) + d1 * h * (1-we) + d1 * h * (1-ww) + (d1 - d2) * h * (1-we) + (d1 - d2) * h * (1-ww)
        window_area_wse = w * h * ws  + d1 * h * we + d1 * h * ww + (d1 - d2) * h * we + (d1 - d2) * h * ww
        window_area_n = w * h * wn


        floor = MoosasFace.new(nil,nil,area / MoosasConstant::INCH_METER_MULTIPLIER_SQR)
        floor.type = MoosasConstant::ENTITY_FLOOR
        ceil = MoosasFace.new(nil,nil,area / MoosasConstant::INCH_METER_MULTIPLIER_SQR)
        ceil.type = MoosasConstant::ENTITY_FLOOR
        s = MoosasSpace.new(floor,h / MoosasConstant::INCH_METER_MULTIPLIER,ceil)

        #e1 = 

        return [area,wall_area,window_area_wse,window_area_n,volumn]

    end

    '''
        评价许多毕设生形方案的性能
    '''
    def self.evaluate_xuduo_energy_and_df(params)
        #第一步，生成MoosasModel


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

        floor_height = 4.5

        fn = (10000.0 / (w * w)).round()  #楼层数
        h = fn * 4.5   #层高

        fz = (fn * z_r).round()   #对应z的起始楼层
        z = fz * 4.5

        if z < 50
            c = (50 - z) * c_r
            fc = (c / 4.5).round()   #交错空间的层数
            if fc + fz > fn
                fc = fn - fz
            end
        else
            c = 0
            fc = 0
        end
        spaces = []

        n_s = [0.0,-1.0,0.0]
        n_e = [1.0,0.0,0.0]
        n_n = [0.0,1.0,0.0]
        n_w = [-1.0,0.0,0.0]

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

            h1 = i * 4.5
            h2 = h1 + 4.5

            area_m = 0  #面积
            bounds = []
            height = 4.5 /  MoosasConstant::INCH_METER_MULTIPLIER
            
            if shape_type == 0  #矩形
                area_m = w * w
                #南向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,w,floor_height)
                bounds.push(sb)
                #北向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,w,floor_height)
                bounds.push(sb)
                #西向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)

            elsif shape_type == 1  #x边超出，y边未超出
                area_m = w * w + (x +a-w)*b
                #南1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,y,floor_height)
                bounds.push(sb)
                #南2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,(x+a-w),floor_height)
                bounds.push(sb)
                #东2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,b,floor_height)
                bounds.push(sb)
                #北1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,(x+a-w),floor_height)
                bounds.push(sb)
                #东3
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,(w-b-y),floor_height)
                bounds.push(sb)
                #北2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,w,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)
            elsif shape_type == 2  #x边未超出,y边超出
                area_m = w *w + (y + b - w)*a

                #南1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,w,floor_height)
                bounds.push(sb)
                #北1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,(w-x-a),floor_height)
                bounds.push(sb)
                #东2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,(y+b-w),floor_height)
                bounds.push(sb)
                #北2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,a,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,(y+b-w),floor_height)
                bounds.push(sb)
                #北3
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,x,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)

            elsif shape_type == 3  #x边和y边均超出
                area_m = w*w + a *b - (w - x) * (w - y)

                #南1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,y,floor_height)
                bounds.push(sb)
                #南2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,(x+a-w),floor_height)
                bounds.push(sb)
                #东2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,b,floor_height)
                bounds.push(sb)
                #北1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,a,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,(y+b-w),floor_height)
                bounds.push(sb)
                #北2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,x,floor_height)
                bounds.push(sb)
                #西2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)
            end
            area = area_m / MoosasConstant::INCH_METER_MULTIPLIER_SQR
            floor = MoosasFace.new(nil,nil,area,[0.0,0.0,1.0])
            if i == 0
                floor.type = MoosasConstant::ENTITY_GROUND_FLOOR
            else
                floor.type = MoosasConstant::ENTITY_FLOOR
            end
            ceils = []
            ceil = MoosasFace.new(nil,nil,area,[0.0,0.0,1.0])
            if i == fn-1
                ceil.type = MoosasConstant::ENTITY_ROOF
            else
                ceil.type = MoosasConstant::ENTITY_FLOOR
            end
            ceils.push(ceil)

            s = MoosasSpace.new(floor,height,ceils)
            s.bounds = bounds
            s.is_outer = true
            spaces.push(s)
            #s.print_info
            i += 1
        end

        model = MoosasModel.new(spaces)

        #第二步，分析模型
        #2.1分析能耗
        er = MoosasEnergy.analysis(model)
        eui = eval(er.total.to_array().join("+")) #能耗密度
        #p "energy = #{er.total.to_array()}"
        p "eui =#{eui} kWh/m2"

        #2.2分析采光
        dfs = MoosasDaylight.quick_analysis_ave_daylight_factor(model)
        ave_df = 0.0
        weight_df = 0.0
        area_all = 0.0
        dfs_pecent = [0.0,0.0,0.0]
        dfs.each do |t|
            df = t[0]

            if df <= 3.0
                dfs_pecent[0] += t[1]
                weight_df += t[0] * t[1] * 10.0
            elsif df < 8.0
                weight_df += t[0] * t[1]
                dfs_pecent[1] += t[1]
            else
                weight_df += t[0] * t[1]
                dfs_pecent[2] += t[1]
            end
            ave_df += t[0] * t[1]
            area_all += t[1]
        end
        ave_df = ave_df / area_all
        if ave_df <3  or ave_df > 8
            ave_df += 10.0
        else
            ave_df = 10.0 - ave_df
        end

        p "ave_df = #{ave_df}"
        
        #weight_df = weight_df / area_all
        #p "weight_df = #{weight_df}"

        #df_unnormal_ratio = (1 - dfs_pecent[1]/area_all)*100.0  #不达标采光面积比例
        #p "df_unnormal_ratio=#{df_unnormal_ratio} %"

        return [eui,ave_df]
    end

end