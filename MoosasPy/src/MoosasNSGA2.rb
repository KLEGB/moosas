
class NSGA2
    Ver='0.6.1'

    def initialize(optimizer,num_parameters, x_bounds, num_objectives,population_size,preference=nil,open_preference=true,mutation_rate=0.2, crossover_rate=1.0)
        @optimizer = optimizer
        @num_parameters = num_parameters
        @x_bounds = x_bounds
        @num_objectives = num_objectives
        @preference = preference
        @open_preference = open_preference
        @mutation_rate = mutation_rate
        @crossover_rate = crossover_rate


        @generations_data = []  #记录各代数据

        p "initialize pools"
        @_P = []
        pool_size = population_size * 3
        for i in 0..pool_size-1
            s = Solution.new(@optimizer,@num_parameters, @x_bounds, @num_objectives)
            for j in 0..@num_parameters-1
                s.x[j] = @x_bounds[j][0] + rand() * (@x_bounds[j][1] - @x_bounds[j][0])
            end
            s.evaluate_solution()
            @_P.push(s)
        end
        @_Q = []
        @_R = nil
        @population_size = population_size
        p "================================================"
        self.update_view(0,@_P)
        id = UI.start_timer(1, false) { MoosasOptimizer.nasg2_ready }
    end      

    def update_generation(i_generations)
 
        p "Generation #{i_generations+1}"

        @_R =  @_P + @_Q
        p "fast_nondominated_sort"
        rank_assigment(@_R)
        fronts = fast_nondominated_sort(@_R)
        @_P = []

        for j in 0..fronts.length-1
            break if fronts[j].length == 0
            p "crowding_distance_assignment"
            crowding_distance_assignment(fronts[j])
            @_P = @_P + fronts[j]

            break if @_P.length >= @population_size
        end

        p "sort_crowding"
        sort_crowding(@_P)
        @_P =  @_P[0,@population_size] if @_P.length > @population_size

        @generations_data.push([i_generations,@_P])

        p "make_new_pop"
        @_Q = make_new_pop(@_P)

        #p _P
        self.update_view(i_generations,@_P)
        #p "=================================================================================================="
    end

    def fast_nondominated_sort(_P)
        fronts = []
        _S = {}
        n = {}

        for i in 0.._P.length-1
            _S[_P[i]] = []
            n[_P[i]] = 0
        end

        fronts.push([])
        for i in 0.._P.length-1
            _p = _P[i]
            for j in 0.._P.length-1
                next if i==j
                _q = _P[j]
                if _p.can_dominate(_q)
                    _S[_p].push(_q)
                elsif _q.can_dominate(_p)
                    n[_p] += 1
                end
            end
            fronts[0].push(_p) if n[_p]==0  #prato最前沿
        end

        i = 0
        while fronts[i].length != 0 do
            next_front = []

            for j in 0..fronts[i].length-1
                r = fronts[i][j]
                for k in 0.._S[r].length-1
                    s = _S[r][k]
                    n[s] -= 1
                    next_front.push(s) if n[s]==0
                end
            end

            i += 1
            fronts.push(next_front)
        end        

        return fronts
    end

    def crowding_distance_assignment(front)

        for i in 0..front.length-1
            front[i].distance = 0
            #front[i].rank = 0 if @open_preference
        end

        for j in 0..@num_objectives-1
            #以下对拥挤度进行区分，使得目标分布均匀
            sort_objective(front,j)
            front[0].distance = Float::MAX
            front[front.length-1].distance = Float::MAX

            range = front[0].objectives[j] - front[front.length-1].objectives[j]  #此目标的最大值剪去最小值
            range = 1.0 if range==0
            for i in 1..front.length-2
                front[i].distance += (front[i+1].objectives[j] - front[i-1].objectives[j]) /range
            end

            #if @open_preference
            #    error = front[i].objectives[j]-@preference[j]
            #    error /= @preference[j]
            #    front[i].rank += error ** 2.0
            #end
        end
    end

    def rank_assigment(front)
        return if not @open_preference
        #以下统计目标与偏好的距离程度
        for i in 0..front.length-1
            front[i].rank = 0
            for j in 0..@num_objectives-1
                error = front[i].objectives[j]-@preference[j]
                error /= @preference[j]
                #error /= @num_objectives
                front[i].rank += error ** 2.0 / (@num_objectives)
            end 
        end
    end


    def sort_objective(_P,obj_idx)
        i = _P.length-1
        while i >= 0 do 
            j =  1
            while j < i+1 do 
                if _P[j-1].objectives[obj_idx] > _P[j].objectives[obj_idx]
                    temp = _P[j-1]
                    _P[j-1] = _P[j]
                    _P[j] = temp
                end
                j += 1
            end
            i -= 1
        end
    end

    def sort_crowding(_P)
        i = _P.length-1
        while i >= 0 do 
            j =  1
            while j < i+1 do 
                if crowded_comparison(_P[j-1],_P[j]) < 0
                    temp = _P[j-1]
                    _P[j-1] = _P[j]
                    _P[j] = temp
                end
                j += 1
            end
            i -= 1
        end
    end

    def crowded_comparison(s1,s2)
        if s1.rank < s2.rank
            return 1
        elsif s1.rank > s2.rank 
            return -1
        elsif s1.distance > s2.distance 
            return 1
        elsif s1.distance < s2.distance 
            return -1
        else 
            return 0
        end
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
                    for i in 0..1
                        s1 = random_choice(_P)
                        s2 = s1
                        while s1 == s2 do
                            s2 = random_choice(_P)
                        end
                        if crowded_comparison(s1,s2) > 0
                            selected_solutions[i] = s1
                        else
                            selected_solutions[i] = s2
                        end
                    end
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

    def update_view(generation,_P)
        solutions = []

        _P.each do |s|
            solutions.push({
                "objectives" => s.objectives,
                "x" => s.x
            })
        end

        data = {
            "i_generation" => generation,
            "solutions" => solutions
        }

        p "update_view #{data}"

        MoosasOptimizer.update_view(data)
    end

    def self.test
        num_parameters = 1
        x_bounds = [[-1000.0,1000.0]]
        num_objectives = 2
        population_size = 5
        num_generations = 3
        nsga2  = NSGA2.new(num_parameters, x_bounds, num_objectives)
        nsga2.run(population_size, num_generations)
    end

end



class Solution
    attr_accessor :x, :normal_x, :objectives, :rank, :distance

    @@solution_counter = 0

    def initialize(optimizer,num_parameters,x_bounds,num_objectives)

        @optimizer = optimizer
        @optimizer_function_name = optimizer.gsub('optimizer','self.evaluate_solution') + "()"

        @num_parameters = num_parameters
        @x = [0] * num_parameters
        @x_bounds = x_bounds
        @normal_x = [0] * num_parameters

        @num_objectives = num_objectives
        @objectives =[0] * num_objectives
    
        @rank = 999999999999
        @distance = 0.0

        @@solution_counter += 1
        @name = "s" + @@solution_counter.to_s
    end

    '''
        根据x，求解objectives
    '''
    def evaluate_solution()
        eval(@optimizer_function_name)
    end


    def evaluate_solution_xuduo()
        energy,df = MoosasPerformanceEvaluator.evaluate_xuduo_energy_and_df(@x)
        @objectives[1] = energy
        @objectives[0] = df
    end

    '''
        计算清华节能楼的体形系数和经济成本
    '''
    def evaluate_solution_thu_env_cn()
        energy,eco = MoosasPerformanceEvaluator.evaluate_thu_env_energy_and_economy(@x)
        @objectives[1] = energy
        @objectives[0] = eco
    end

    '''
        计算体形系数和经济成本
    '''
    def evaluate_solution_sc_eco()
        sc,eco = MoosasPerformanceEvaluator.evaluate_sc_and_economy(@x)
        @objectives[1] = sc
        @objectives[0] = eco
    end

     '''
        计算体形系数和经济成本
    '''
    def evaluate_solution_paper_en()
        sc,eco = MoosasPerformanceEvaluator.evaluate_sc_and_economy_paper(@x)
        @objectives[1] = sc
        @objectives[0] = eco
    end

    '''
        计算体形系数和经济成本
    '''
    def evaluate_solution_paper_cn()
        sc,eco = MoosasPerformanceEvaluator.evaluate_sc_and_economy_paper(@x)
        @objectives[1] = sc
        @objectives[0] = eco
    end

    '''
        计算平米能耗值和平均采光系数
    '''
    def evaluate_solution_energy_df()
        t1 = Time.new
        #生成建筑
        group = MoosasShapeGenerator.generate_parametric_building(x)
        #评价建筑
        ave_energy,ave_df = MoosasGeometry.quick_analysis_energy_and_df
        @objectives[1] = ave_energy
        @objectives[0] = ave_df * 100
        #删除建筑
        Sketchup.active_model.entities.erase_entities(group)
        t2 = Time.new
        cost_time = t2 - t1 
        p "evaluate_solution #{@name} time #{cost_time}s, #{@x}, #{@objectives}"
    end


    '''
        示例评估
    '''
    def evaluate_solution_demo()
        @objectives[0] = 5 +  3 * ((@x[5]-2)/10) ** 1 + 2*rand()
        @objectives[1] = 50 + 30 * ((@x[5]-1)/10) ** 1 + 20 * rand()
    end

    def crossover(other)
        child_solution = Solution.new(@optimizer,@num_parameters, @x_bounds, @num_objectives)
        
        #交换某些部分
        started_index = rand(@num_parameters)
        for i in 0...started_index
            child_solution.x[i] = @x[i]
        end
        for i in started_index...@num_parameters
            child_solution.x[i] = other.x[i]
        end

        '''
        #平方求下代
        normalize()
        other.normalize()
        for i in 0..@num_parameters-1
            child_solution.normal_x[i] = Math.sqrt(@normal_x[i] * other.normal_x[i])
        end
        child_solution.denormalize()
        '''

        return child_solution
    end

    #在x上下限范围内进行某个基因位的突变
    def mutate()
        mutate_gene_i = rand(@num_parameters)
        @x[mutate_gene_i] = @x_bounds[mutate_gene_i][0] + rand() * (@x_bounds[mutate_gene_i][1] - @x_bounds[mutate_gene_i][0])
    end

    '''
        判断本方案是不是比其他方案帕累托更优
    '''
    def can_dominate(other)
        dominates = false
        #如果离偏好点很近，且距离比其它方案更近，则认为是更优的
        if @rank < other.rank and @rank < 0.1
            return true
        end
        for i in 0..@num_objectives-1
            if @objectives[i] > other.objectives[i]
                return false
            else
                dominates = true
            end
        end
        return dominates
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
end
