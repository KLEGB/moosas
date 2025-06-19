
#主入口
class GA
    p 'GA_Solution Ver.0.6.1'

    def initialize(optimizer,num_parameters, x_bounds,population_size,mutation_rate=0.5, crossover_rate=0.5)
        @optimizer = optimizer
        @num_parameters = num_parameters
        @x_bounds = x_bounds
        @mutation_rate = mutation_rate
        @crossover_rate = crossover_rate
        @population_size = population_size


        @generations_data = []  #记录各代数据
        #id = UI.start_timer(1, false) { MoosasOptimizer.nasg2_ready }
    end


    def init
        p "initialize pools"
        @_P = []
        pool_size = @population_size * 2
        $current_model.backup
        for i in 0..pool_size-1
            s = GA_Solution.new(@optimizer,@num_parameters, @x_bounds)
            for j in 0..@num_parameters-1
                s.x[j] = @x_bounds[j][0] + rand() * (@x_bounds[j][1] - @x_bounds[j][0])
            end
            s.evaluate_solution()
            @_P.push(s)
        end
        @_Q = []
        @_R = nil
        @i_generations = 0
        $current_model.restore
        #p "================================================"
        @_P = @_P.sort do |a, b|
            a.objective <=> b.objective 
        end
        self.update_view(@_P)
    end

    def set_webdialog(wd)
        @web_dialog = wd
    end


    def update_generation()
        @i_generations += 1
        p "Generation #{@i_generations}"

        @_R =  @_P + @_Q
        #选择
        @_P = self.round_robin_select(@_R)

        #产生新一代
        $current_model.backup
        @_Q = make_new_pop(@_P)
        $current_model.restore

        #更新视图
        self.update_view(@_P)
        #p "=================================================================================================="
    end

    #轮盘选择算法
    def round_robin_select(_R)
        #排序
        _R = _R.sort do |a, b|
            a.objective <=> b.objective 
        end
        #计算各个方案的概率
        pr = []
        total_p = 0
        max_energy = 200.0
        n = _R.length
        _R.each do |r|
            t =  max_energy - r.objective
            if t < 0
                t = 0 
            end
            total_p += t
            pr.push t
        end
        for i in 0...n
            pr[i] /= total_p
        end

        #计算各个方案的累计概率
        cpr = []
        cpr[0] = pr[0]
        for i in 1...n
            cpr[i] = cpr[i-1] + pr[i]
        end
        _P = [ ]
        selected_index = []
        rank_n = 3  #每次留下前几名
        for i in 0...rank_n
            _P.push _R[i]
            selected_index.push(i)
        end

        while _P.length < @population_size
            ps = rand()
            for i in rank_n...n
                if not selected_index.include?(i)  and cpr[i] >= ps
                    _P.push _R[i]
                    selected_index.push i
                    break
                end
            end
        end
        return _P
    end
      
    #根据父代P，产生子代Q
    def make_new_pop(_P)
        _Q = []

        while _Q.length != _P.length do

            #杂交和变异产生下一代
            if rand() < @crossover_rate
                
                #从P中挑选的两个精英
                selected_solutions = [nil,nil]
                while selected_solutions[0] == selected_solutions[1] do
                    selected_solutions[0] = random_choice(_P)
                    selected_solutions[1] = random_choice(_P)
                end

                child_solution = selected_solutions[0].crossover(selected_solutions[1])

                if rand() < @mutation_rate
                    child_solution.mutate()
                end

                child_solution.evaluate_solution()

                _Q.push(child_solution)
            end
        end
        return _Q
    end

    def random_choice(_P)
        return _P[rand(_P.length)]
    end

    def update_view(_P)
        solutions = []

        _P.each do |s|
            solutions.push({
                "objective" => s.objective,
                "x" => s.x,
                "obj_record" => s.obj_record
            })
        end

        data = {
            "i_generation" => @i_generation,
            "solutions" => solutions,
            "x_bounds"=>@x_bounds,
            "optimizer"=>@optimizer,
            "num_parameters"=>@num_parameters
        }

        #p "update_view #{data}"

        p "range: #{solutions[0]["objective"]}  --- #{solutions[solutions.length-1]["objective"]}"  


        if @web_dialog != nil
            @web_dialog.send("optmize_energy",data)
        end    
        #MoosasOptimizer.update_view(data)
    end

    def self.test
        x_bounds = [[0.0,10.0],[0.0,10.0]]
        ga = GA.new("optimizer_test",2,x_bounds,20)
        #ga.update_generation(0)
        for i in 0..50
            ga.update_generation(i)
        end
    end

end


#每个方案
class GA_Solution
    attr_accessor :x, :normal_x, :objective, :obj_record

    @@solution_counter = 0

    def initialize(optimizer,num_parameters,x_bounds)

        @optimizer = optimizer
        @optimizer_function_name = optimizer.gsub('optimizer','self.evaluate_solution') + "()"

        @num_parameters = num_parameters
        @x = [0] * num_parameters
        @x_bounds = x_bounds
        @normal_x = [0] * num_parameters

        @objective = nil
        @obj_record = nil
    
        @@solution_counter += 1
        @name = "s" + @@solution_counter.to_s
    end


    '''
        根据x，求解objectives
    '''
    def evaluate_solution()
        eval(@optimizer_function_name)
    end

    def crossover(other)
        child_solution = GA_Solution.new(@optimizer,@num_parameters, @x_bounds)

        started_index = rand(@num_parameters)
        for i in 0...started_index
            child_solution.x[i] = @x[i]
        end
        for i in started_index...@num_parameters
            child_solution.x[i] = other.x[i]
        end

        return child_solution
    end

    #在x上下限范围内进行某个基因位的突变
    def mutate()
        mutate_gene_i = rand(@num_parameters)
        @x[mutate_gene_i] = @x_bounds[mutate_gene_i][0] + rand() * (@x_bounds[mutate_gene_i][1] - @x_bounds[mutate_gene_i][0])
    end

    def normalize
        for i in 0..@num_parameters-1
            if @x_bounds[i][1] != @x_bounds[i][0]
                @normal_x[i] = (@x[i] - @x_bounds[i][0]) / (@x_bounds[i][1] - @x_bounds[i][0]) 
            else
                @normal_x[i]  = @x[i]
            end
        end
    end

    def denormalize
        for i in 0..@num_parameters-1
            if @x_bounds[i][1] != @x_bounds[i][0]
                @x[i] = @x_bounds[i][0] + @normal_x[i] * (@x_bounds[i][1] - @x_bounds[i][0]) 
            else
                @x[i] = @x_bounds[i][0]
            end
        end
    end

    def evaluate_solution_energy

        #根据x，修改模型的参数
        if @bounds_in_dir == nil
            @bounds_in_dir = $current_model.get_all_bounds_in_direction
        end
        wwr = [@x[0],@x[1],@x[2],@x[3]]

        for dir_i in 0...4
            wwr_i = wwr[dir_i]
            @bounds_in_dir[dir_i].each do |b|
                b.wwr = wwr_i
            end
        end

        #评价模型
        er = MoosasEnergy.analysis($current_model)
        @obj_record = er.total.to_array()
        p @obj_record
        @objective = eval(@obj_record.join("+"))
    end

    def evaluate_solution_test
        @objective = (@x[0] - 2) ** 2 + (@x[1]-4)**2
    end
end

$moosas_energy_ga = nil

