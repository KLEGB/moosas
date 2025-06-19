
module MoosasAnalysis
    Ver='0.6.3'

    def self.main_analysis(require_recognize_model,building_type,require_radiation)

        if require_recognize_model == "true"
            t1 = Time.new
            model = MMR.recognize_floor
            t2 = Time.new
            p "模型识别用时： #{t2-t1}s"
        else
            model = $current_model
        end
        t1 = Time.new
        e_data = MoosasEnergy.analysis(model,building_type,require_radiation == "true")
        t2 = Time.new
        p "能耗分析用时： #{t2-t1}s"
        dfs = MoosasDaylight.quick_analysis_ave_daylight_factor(model)
        #p dfs
        data = {
            "area" => model.get_total_area(),
            "energy" => e_data,
            "dfs" => dfs
        }
        meta_current_data = MoosasMeta.get_and_set_dic("moosas","current",JSON.generate(data),false)
        #备份数据
        $performance_data["energy"] = e_data
        MoosasWebDialog.send("main_analysis_result",data)
        
        #备份模型文件
        backup_path = MoosasUtils.back_up_model()
        history_data = {
            "area" => model.get_total_area(),
            "energy" => e_data["total"],
            "backup_path" => backup_path
        }
        #存储历史分析数据（模型路径，总能耗，照明、空调、采暖三个分项能耗）
        meta_history_data = MoosasMeta.get_and_set_dic("moosas","history",JSON.generate(history_data),true)
        #更新历史数据图表
        #p history_data
        MoosasWebDialog.send("update_analysis_history",meta_history_data)
    end



    def self.params_analysis(type,params)

        begin
            if $current_model == nil
                MMR.recognize_floor
            end

            if @all_bounds_in_dir == nil
                @all_bounds_in_dir = $current_model.get_all_bounds_in_direction
            end

            $current_model.backup

            #参数分析
            case type
            when "wall_u","win_u","win_shgc","wwr"
                results = self.params_analysis_mode_1($current_model,type,params)        
            else
            end
            $current_model.restore

            #统计参数取值分布
            results.each do |res|
                res["bis"] = self.get_target_bounds_info(res["type"],res["target"])
                #if $performance_data["energy"] != nil
                #    res["cur_energy"] = $performance_data["energy"].total
                #end
            end

            if MoosasWebDialog.dialog != nil
                MoosasWebDialog.send("params_analysis_result",results)
            end
        rescue Exception => e
            MoosasUtils.rescue_log(e)
        end
        
    end

    #多目标参数分析
    def self.multi_goal_params_analysis(type, params)

        begin
            if $current_model == nil
                MMR.recognize_floor
            end
            if @all_bounds_in_dir == nil
                @all_bounds_in_dir = $current_model.get_all_bounds_in_direction
            end

            $current_model.backup

            #参数分析
            case type
            when "wwr"
                results = self.params_analysis_mode_2($current_model,type,params)        
            else
            end

            $current_model.restore

            #统计参数取值分布
            results.each do |res|
                res["bis"] = self.get_target_bounds_info(res["type"],res["target"])
                #if $performance_data["energy"] != nil
                #    res["cur_energy"] = $performance_data["energy"].total
                #end
            end

            if MoosasWebDialog.dialog != nil
                MoosasWebDialog.send("params_multi_goal_analysis_result",results)
            end
        rescue Exception => e
            MoosasUtils.rescue_log(e)
        end
        
    end


    #对东、西、南、北面墙体的参数进行变化分析
    #params = [{"target"=>0,"range"=>[0,1], "step"=>0.1}]
    #target: 8=all, 0=south, 3=east, 1=west, 2=north, 4=roof
    def self.params_analysis_mode_1(model,type,params)
        results = []
        
        params.each do |param|
            res = {}
            #根据分析目标，先收集，需要改变数据的边
            all_bounds = model.get_all_bounds
            target = param["target"].to_i
            if target == MoosasConstant::ORIENTATION_ALL
                target_bounds = all_bounds
            else
                target_bounds =[]
                all_bounds.each do |b|
                    if b.get_orientation() == target
                        target_bounds.push b
                    end
                end
                all_bounds = nil
            end
            range = param["range"]
            min_v = range[0].to_f
            max_v = range[1].to_f
            step = param["step"].to_f
            x = min_v
            values = []
            while x <= max_v  
                #修改参数
                case type
                when "wwr"
                    target_bounds.each do |b|
                        b.wwr = x
                    end  
                when "wall_u" 
                    target_bounds.each do |b|
                        b.settings["opaque" ][1] = x
                    end       
                when "win_u"
                    target_bounds.each do |b|
                        b.settings["glazing" ][1] = x
                    end  
                when "win_shgc"
                    target_bounds.each do |b|
                        b.settings["glazing" ][2] = x
                    end                         
                else
                    y = 0.0
                end
                #调用模拟
                e_data = MoosasEnergy.analysis(model,param['buildingtype'],true)
                y = e_data["total"]
                pair = {"x"=>x,"y"=>y}
                #p "#{x},#{y.join(",")}"
                values.push pair
                x += step
            end
            #逐个分析，并且记录
            res["type"] = type
            res["target"] = param["target"]
            res["range"] = [min_v,max_v]
            res["step"] = step
            res["values"] = values
            res["name"] = param["name"]
            results.push res
        end
        #返回数据
        return results
    end

    #参数：窗墙比
    #目标：快速能耗分析，快速采光分析
    def self.params_analysis_mode_2(model,type,params)
        results = []
        
        params.each do |param|
            res = {}
            #根据分析目标，先收集，需要改变数据的边
            all_bounds = model.get_all_bounds
            target = param["target"].to_i
            if target == MoosasConstant::ORIENTATION_ALL
                target_bounds = all_bounds
            else
                target_bounds =[]
                all_bounds.each do |b|
                    if b.get_orientation() == target
                        target_bounds.push b
                    end
                end
                all_bounds = nil
            end
            range = param["range"]
            min_v = range[0].to_f
            max_v = range[1].to_f
            step = param["step"].to_f
            x = min_v
            values = []
            while x <= max_v  
                #修改参数
                case type
                when "wwr"
                    target_bounds.each do |b|
                        b.wwr = x
                    end                           
                else
                    y1 = 0.0
                    y2 = 0.0
                end
                #调用能耗模拟
                e_data = MoosasEnergy.analysis(model,param["buildingtype"],true)
                y1 = e_data["total"].reduce(:+)
                #调查快速采光分析
                dfs = MoosasDaylight.quick_analysis_ave_daylight_factor(model)
                area = 0
                df = 0
                dfs.each do |d|
                    area += d[1]
                    df += d[0] * d[1]
                end
                y2 = df / area
                pair = {"x"=>x,"y1"=>y1,"y2"=>y2}
                p "multi_goal_params_analysis: #{type}, #{target}, #{pair}"
                values.push pair
                x += step
            end
            #逐个分析，并且记录
            res["type"] = type
            res["target"] = param["target"]
            res["range"] = [min_v,max_v]
            res["step"] = step
            res["values"] = values
            res["name"] = param["name"]
            results.push res
        end
        #返回数据
        return results
    end


    def self.get_target_bounds_info(type,target)
        bs = @all_bounds_in_dir[target]
        bis = []
        bs.each do |b|
            case type
            when "wwr"
                bis.push b.wwr
            when "wall_u" 
                bis.push b.settings["opaque" ][1]   
            when "win_u"
                bis.push b.settings["glazing" ][1] 
            when "win_shgc"
                bis.push b.settings["glazing" ][2]                     
            else
                
            end
        end
        #p bis
        return bis
    end

    def self.update_moosas_model_parameters_setting(tag,value)
        arr = tag.split("-")
        type = arr[0]
        target = arr[1].to_i
        value = value.to_f

        all_bounds = $current_model.get_all_bounds
        if target == MoosasConstant::ORIENTATION_ALL
            target_bounds = all_bounds
        else
            target_bounds =[]
            all_bounds.each do |b|
                if b.get_orientation() == target
                    target_bounds.push b
                end
            end
            all_bounds = nil
        end

        case type
        when "wwr"
            target_bounds.each do |b|
                b.wwr = value
            end  
        when "wall_u" 
            target_bounds.each do |b|
                b.settings["opaque" ][1] = value
            end       
        when "win_u"
            target_bounds.each do |b|
                b.settings["glazing" ][1] = value
            end  
        when "win_shgc"
            target_bounds.each do |b|
                b.settings["glazing" ][2] = value
            end                         
        else
        end
        p "success: update_moosas_model_parameters_setting!"
    end
end

$performance_data = {}