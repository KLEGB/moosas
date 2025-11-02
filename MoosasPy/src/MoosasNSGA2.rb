
class NSGA2
    Ver='0.6.1'

    def initialize(optimizer,num_parameters, x_bounds, num_objectives,population_size,preference=nil,open_preference=true,mutation_rate=0.2, crossover_rate=1.0)
    # """
    # Function
    # --------
    # Initialize the optimizer with given parameters and create an initial population of solutions.
    # 
    # This constructor sets up the optimization environment by configuring the optimizer settings,
    # bounds, population size, genetic algorithm parameters, and preference options. It also
    # initializes the solution pools and generates an initial random population that is evaluated
    # immediately. A timer is started to trigger后续 optimization steps asynchronously.
    # 
    # Parameters
    # ----------
    # optimizer : Object
    # The optimization engine or solver used to evaluate solutions.
    # num_parameters : Integer
    # Number of decision variables in each solution.
    # x_bounds : Array[Array[Numeric]]
    # Bounds for each parameter, where x_bounds[i][0] and x_bounds[i][1] are
    # the lower and upper bounds for the i-th parameter.
    # num_objectives : Integer
    # Number of objectives to optimize (used in multi-objective optimization).
    # population_size : Integer
    # Number of individuals in the main population.
    # preference : Any, optional
    # User preference information used to guide the search (default is None).
    # open_preference : Boolean, optional
    # Flag indicating whether preference-based guidance is enabled (default is True).
    # mutation_rate : Float, optional
    # Probability of mutation in the genetic operations (default is 0.2).
    # crossover_rate : Float, optional
    # Probability of crossover in the genetic operations (default is 1.0).
    # 
    # Returns
    # -------
    # None
    # This method initializes the instance attributes and does not return a value.
    # """
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
    # """
    # Function
    # --------
    # Update the current generation in an evolutionary algorithm using non-dominated sorting and crowding distance assignment.
    # 
    # This method performs one iteration of the generational update process in a multi-objective optimization algorithm (e.g., NSGA-II).
    # It combines parent and offspring populations, applies fast non-dominated sorting and crowding distance assignment to select the best individuals,
    # updates the population for the next generation, records generation data, and generates a new offspring population.
    # 
    # Parameters
    # ----------
    # i_generations : Integer
    # The index of the current generation (0-based). Used for tracking progress and storing generation-specific data.
    # 
    # Returns
    # -------
    # None
    # This method modifies the object's internal state (including @_P, @_Q, @generations_data) and does not return a value.
    # """
 
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
    # Function:
    # Performs fast non-dominated sorting on a population of individuals.
    # This algorithm partitions the population into fronts based on dominance
    # relationships, where each front contains solutions that are not dominated
    # by any other solution within the same front. Used primarily in multi-objective
    # optimization algorithms such as NSGA-II.
    # 
    # Parameters:
    # _P : Array
    # An array of individuals (solutions) to be sorted. Each individual must
    # implement the `can_dominate` method, which determines whether the
    # individual dominates another in terms of objective values.
    # 
    # Returns:
    # Array of Arrays
    # A list of fronts, where each front is an array of individuals.
    # The first front contains the non-dominated individuals (Pareto front),
    # the second front contains individuals dominated only by those in the
    # first front, and so on. Individuals in later fronts are progressively
    # more dominated.
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
    # """
    # Function
    # --------
    # Assigns crowding distance values to individuals in a front for diversity preservation in multi-objective optimization.
    # The crowding distance measures how close an individual is to its neighbors in the objective space; larger distances
    # indicate more isolated (and thus more diverse) solutions. Boundary points are assigned infinite distance to ensure selection.
    # 
    # Parameters
    # ----------
    # front : Array
    # An array of individual objects (typically solutions in a Pareto front). Each individual must have:
    # - `distance` attribute: to store computed crowding distance.
    # - `objectives` array: containing objective function values for that individual.
    # num_objectives : Integer (via instance variable @num_objectives)
    # The number of objectives being optimized. Used to iterate over each objective dimension.
    # 
    # Attributes Modified
    # -------------------
    # front[i].distance : Float
    # Sets the crowding distance of each individual in the front. Boundary individuals receive Float::MAX,
    # while internal individuals receive a normalized sum of distances to neighbors across all objectives.
    # 
    # Returns
    # -------
    # None
    # This method modifies the `distance` attribute of individuals in the `front` array in place and returns nothing.
    # 
    # Notes
    # -----
    # - The method assumes minimization of all objectives.
    # - For each objective, the front is sorted, and the extreme (boundary) solutions are assigned maximum distance to promote inclusion.
    # - The range normalization prevents division by zero by setting minimum range to 1.0.
    # - Commented code suggests optional preference-based ranking that is currently inactive.
    # """

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
    # """
    # Function
    # --------
    # Assigns a rank to each element in the front based on the squared normalized error
    # between its objectives and a given preference vector. Only executed if open_preference
    # is enabled.
    # 
    # Parameters
    # ----------
    # front : Array
    # An array of objects, each containing an `objectives` attribute (array of numerical
    # values representing objective scores) and a `rank` attribute to be updated.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It modifies the `rank` attribute of each
    # element in place. If `@open_preference` is false or nil, the method returns early
    # with no modifications.
    # """
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
    # """
    # Function
    # --------
    # Sorts a list of objects based on the specified objective value in ascending order using bubble sort.
    # 
    # Parameters
    # ----------
    # _P : Array
    # An array of objects, each having an `objectives` attribute which is an array or collection
    # containing objective values.
    # obj_idx : int
    # The index of the objective value within the `objectives` array to sort by.
    # 
    # Returns
    # -------
    # None
    # This method sorts the array `_P` in place and does not return a value.
    # """
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
    # """
    # Function
    # --------
    # Sorts an array of solutions based on crowding distance using a bubble sort variant.
    # 
    # This method performs a descending sort of the input array `_P` by comparing
    # individuals based on their crowding distance via the `crowded_comparison` function.
    # Individuals with higher crowding distance are placed earlier in the array.
    # 
    # Parameters
    # ----------
    # _P : Array
    # An array of solutions (typically candidate solutions in multi-objective optimization),
    # where each element is expected to have a defined crowding distance for comparison.
    # The array is sorted in-place.
    # 
    # Returns
    # -------
    # None
    # The method modifies the input array `_P` in-place and does not return a value.
    # """
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
    # """
    # Function
    # ----------
    # crowded_comparison
    # Compares two solutions (s1 and s2) based on rank and crowding distance
    # for use in multi-objective optimization algorithms (e.g., NSGA-II).
    # Solutions with lower rank are preferred. If ranks are equal, solutions
    # with greater crowding distance are favored to promote diversity.
    # 
    # Parameters
    # ----------
    # s1 : object
    # First solution object with attributes 'rank' (Pareto front rank) and 'distance' (crowding distance).
    # s2 : object
    # Second solution object with same attributes as s1.
    # 
    # Returns
    # -------
    # int
    # Returns 1 if s1 is better than s2, -1 if s2 is better than s1, and 0 if both are equally good.
    # Comparison is first based on rank (lower is better), then on crowding distance (higher is better).
    # """
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
    # """
    # Function
    # --------
    # make_new_pop
    # Generates a new population (_Q) through genetic operations of crossover and mutation
    # based on the given parent population (_P). The size of the new population matches
    # that of the parent population. Selection is guided by crowded comparison, ensuring
    # diversity and elitism in the selection process.
    # 
    # Parameters
    # ----------
    # _P : Array
    # The parent population, represented as an array of solution objects. Each solution
    # object must support methods such as `crossover`, `mutate`, and `evaluate_solution`.
    # These solutions are used to generate offspring via genetic operators.
    # 
    # Returns
    # -------
    # Array
    # A new population (_Q) of the same size as _P, consisting of newly generated
    # offspring solutions. Each offspring is produced through crossover (with probability
    # @crossover_rate) and optionally mutation (with probability @mutation_rate), followed
    # by evaluation of the solution's fitness.
    # """
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
    # Function
    # ----------
    # random_choice : Returns a randomly selected element from the input array.
    # 
    # Parameters
    # ----------
    # _P : Array
    # The input array from which a random element will be selected.
    # 
    # Returns
    # -------
    # Object
    # A randomly chosen element from the array _P.
        return _P[rand(_P.length)]
    end

    def update_view(generation,_P)
    # """
    # Function
    # --------
    # update_view
    # Updates the current view of the optimization process by sending solution data to the MoosasOptimizer visualization interface.
    # 
    # Parameters
    # ----------
    # generation : Integer
    # The current generation index in the optimization process. Used to track progress and label the current iteration.
    # _P : Array<Struct or Object>
    # An array of solution objects, each containing at least two attributes:
    # - `objectives`: an array or list of objective function values.
    # - `x`: an array or list of decision variables (solution vector).
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It sends data asynchronously to MoosasOptimizer.update_view for visualization purposes.
    # """
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
    # Function:
    # A class method that initializes and runs an NSGA-II (Non-dominated Sorting Genetic Algorithm) optimization process
    # with predefined parameters for a multi-objective optimization problem.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None : This method does not return a value. It executes the NSGA2 algorithm instance with specified configuration
    # including number of parameters, bounds, objectives, population size, and generations.
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
    # Function
    # ----------
    # Initializes a new Solution instance with the given optimizer, number of parameters, parameter bounds,
    # and number of objectives. Sets up internal state including decision variables, objectives, ranking,
    # and a unique name based on a global solution counter.
    # 
    # Parameters
    # ----------
    # optimizer : str
    # The name of the optimizer used for optimization; will be modified to reference
    # the `evaluate_solution` method dynamically.
    # num_parameters : int
    # The number of decision variables (parameters) in the solution.
    # x_bounds : list of tuples
    # Bounds for each decision variable, where each tuple contains (lower_bound, upper_bound).
    # num_objectives : int
    # The number of objectives to be evaluated in the optimization problem.
    # 
    # Returns
    # -------
    # None
    # This constructor does not return a value; it initializes instance variables.

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
    # """
    # Function
    # --------
    # evaluate_solution
    # Evaluates the solution by dynamically executing the optimizer function
    # referenced by the instance variable @optimizer_function_name.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It relies on the instance
    # variable @optimizer_function_name to determine which function to evaluate.
    # 
    # Returns
    # -------
    # Object
    # Returns the result of evaluating the function named in @optimizer_function_name.
    # The actual return type depends on the evaluated function's implementation.
    # """
        eval(@optimizer_function_name)
    end


    def evaluate_solution_xuduo()
    # Function:
    # Evaluates the energy performance and shape factor for the Tsinghua Energy-Saving Building design using the MoosasPerformanceEvaluator.
    # 
    # Parameters:
    # None : This method does not take any explicit parameters. It operates on the instance variable `@x` which represents the design variables or configuration.
    # 
    # Returns:
    # None : The method updates the instance variable `@objectives` in place, where `@objectives[1]` is set to the computed energy performance (energy) and `@objectives[0]` is set to the computed shape factor (df). No value is returned.
        energy,df = MoosasPerformanceEvaluator.evaluate_xuduo_energy_and_df(@x)
        @objectives[1] = energy
        @objectives[0] = df
    end

    '''
        计算清华节能楼的体形系数和经济成本
    '''
    def evaluate_solution_thu_env_cn()
    # Function:
    # Evaluates the energy performance and economic cost of a given solution in the context of
    # Tsinghua University's environmental conditions. Updates the instance's objectives array
    # with computed economy as the first objective and energy as the second.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    # The method updates the instance variable @objectives in place, where:
    # - @objectives[0] is set to the economic cost (eco)
    # - @objectives[1] is set to the energy performance (energy)
        energy,eco = MoosasPerformanceEvaluator.evaluate_thu_env_energy_and_economy(@x)
        @objectives[1] = energy
        @objectives[0] = eco
    end

    '''
        计算体形系数和经济成本
    '''
    def evaluate_solution_sc_eco()
    # """
    # Function
    # --------
    # evaluate_solution_sc_eco
    # Evaluates and assigns the shape coefficient (SC) and economic cost (ECO)
    # of the current solution using the MoosasPerformanceEvaluator.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on the instance
    # variable `@x` to compute performance metrics.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It updates the instance variable
    # `@objectives` where `@objectives[1]` is set to the computed shape
    # coefficient (sc) and `@objectives[0]` is set to the computed economic
    # cost (eco).
    # """
        sc,eco = MoosasPerformanceEvaluator.evaluate_sc_and_economy(@x)
        @objectives[1] = sc
        @objectives[0] = eco
    end

     '''
        计算体形系数和经济成本
    '''
    def evaluate_solution_paper_en()
    # """
    # Function
    # --------
    # evaluate_solution_paper_en
    # Evaluates the shape coefficient and economic cost for the current solution using paper-based evaluation method.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters. It operates on instance variables, specifically @x, which is expected to be set prior to invocation.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It updates the instance variable @objectives in place, assigning economic cost to @objectives[0] and shape coefficient to @objectives[1].
    # """
        sc,eco = MoosasPerformanceEvaluator.evaluate_sc_and_economy_paper(@x)
        @objectives[1] = sc
        @objectives[0] = eco
    end

    '''
        计算体形系数和经济成本
    '''
    def evaluate_solution_paper_cn()
    # """
    # Function
    # --------
    # evaluate_solution_paper_cn
    # 
    # Evaluate the solution based on energy consumption per square meter and average daylighting coefficient,
    # specifically for paper-related evaluation criteria.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on instance variables,
    # particularly `@x` (design solution vector) and updates `@objectives`.
    # 
    # Returns
    # -------
    # None
    # The method updates the instance variable `@objectives` in place:
    # - `@objectives[0]`: economy value (e.g., energy consumption per square meter)
    # - `@objectives[1]`: spatial comfort or daylighting performance (e.g., average daylight coefficient)
    # 
    # Notes
    # -----
    # This method relies on `MoosasPerformanceEvaluator.evaluate_sc_and_economy_paper` to compute both
    # sustainability (SC) and economic (eco) performance metrics from the solution encoded in `@x`.
    # """
        sc,eco = MoosasPerformanceEvaluator.evaluate_sc_and_economy_paper(@x)
        @objectives[1] = sc
        @objectives[0] = eco
    end

    '''
        计算平米能耗值和平均采光系数
    '''
    def evaluate_solution_energy_df()
    # Function:
    # Evaluates the energy performance and daylight factor (DF) of a parametrically generated building model.
    # The method creates a building using a shape generator, performs a quick energy and daylight analysis,
    # stores the results in the instance variable `@objectives`, and then removes the generated model from the environment.
    # Execution time is measured and printed along with solution name, design variables, and objectives.
    # 
    # Parameters:
    # None : This method does not take any explicit parameters. It uses instance variables such as `@x` (design variables),
    # `@name` (solution identifier), and `@objectives` (to store evaluation results).
    # 
    # Returns:
    # None : The method does not return a value. It modifies the instance variable `@objectives` in place, where:
    # - `@objectives[0]` is set to the average daylight factor (scaled by 100),
    # - `@objectives[1]` is set to the average energy consumption.
    # Additionally, it prints execution time and evaluation data to standard output.
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
    # """
    # Function
    # --------
    # evaluate_solution_demo
    # 
    # Evaluates a solution by computing two objective values based on the instance variable @x[5]
    # and random noise. This method is typically used in multi-objective optimization contexts
    # to simulate objective function evaluations with stochastic components.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters. It uses the instance variable @x[5]
    # and generates random values using Ruby's rand() function.
    # 
    # Returns
    # -------
    # None
    # The method modifies the instance variable @objectives in place, setting:
    # - @objectives[0]: A value derived from (@x[5]-2)/10 raised to the power of 1, scaled by 3,
    # with an offset of 5 and added random noise (between 0 and 2).
    # - @objectives[1]: A value derived from (@x[5]-1)/10 raised to the power of 1, scaled by 30,
    # with an offset of 50 and added random noise (between 0 and 20).
    # """
        @objectives[0] = 5 +  3 * ((@x[5]-2)/10) ** 1 + 2*rand()
        @objectives[1] = 50 + 30 * ((@x[5]-1)/10) ** 1 + 20 * rand()
    end

    def crossover(other)
    # Function:
    # Performs a crossover operation between this solution and another solution to generate a child solution.
    # The crossover is performed by selecting a random index and combining the parameter values from both parents
    # such that the child inherits parameters from the current solution up to the starting index,
    # and from the other solution beyond that index.
    # 
    # Parameters:
    # other : Solution
    # Another solution instance used as the second parent in the crossover operation.
    # It must have the same number of parameters and compatible bounds and objectives.
    # 
    # Returns:
    # Solution
    # A new Solution instance representing the child solution resulting from the crossover.
    # The child's parameter vector `x` is constructed by combining segments of the current solution's `x`
    # and the other solution's `x`, based on a randomly chosen crossover point.
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
    # Function:
    # Randomly mutates one gene in the individual's parameter array by selecting a random parameter
    # and assigning it a new value uniformly sampled within the specified bounds for that parameter.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    # 
    # Notes:
    # The method modifies the instance variable `@x` in place by randomly selecting one of the parameters
    # (indexed by `mutate_gene_i`) and replacing its value with a uniformly random value within the
    # lower and upper bounds defined in `@x_bounds`. This is typically used in evolutionary algorithms
    # to introduce genetic diversity.
        mutate_gene_i = rand(@num_parameters)
        @x[mutate_gene_i] = @x_bounds[mutate_gene_i][0] + rand() * (@x_bounds[mutate_gene_i][1] - @x_bounds[mutate_gene_i][0])
    end

    '''
        判断本方案是不是比其他方案帕累托更优
    '''
    def can_dominate(other)
    # """
    # Function
    # --------
    # Determine if the current solution dominates another solution in multi-objective optimization.
    # 
    # This method evaluates dominance based on objective values and rank. A solution is considered
    # to dominate another if it is no worse in all objectives and strictly better in at least one.
    # Additionally, if the current solution's rank is both lower than the other's and below a threshold
    # (0.1), it is considered dominant regardless of objective values, indicating proximity to a preferred region.
    # 
    # Parameters
    # ----------
    # other : Object
    # Another solution object to compare against. Must have attributes `rank` and `objectives`
    # where `objectives` is an array of numerical objective values.
    # 
    # Returns
    # -------
    # bool
    # True if the current solution dominates the other solution; False otherwise.
    # """
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
    # """
    # Function
    # --------
    # Normalize the input parameters to the range [0, 1] based on given bounds.
    # If the lower and upper bounds are equal, the parameter is left unchanged.
    # 
    # Parameters
    # ----------
    # @x : Array[Numeric]
    # The array of original parameter values to be normalized.
    # @x_bounds : Array[[Numeric, Numeric]]
    # The array of bound pairs [lower_bound, upper_bound] for each parameter.
    # @num_parameters : Integer
    # The number of parameters to normalize, used to control iteration length.
    # @normal_x : Array[Numeric], optional
    # The array to store normalized parameter values. Modified in place.
    # 
    # Returns
    # -------
    # None
    # This method modifies the instance variable @normal_x in place and does not return a value.
    # """
        for i in 0..@num_parameters-1
            if @x_bounds[i][1] != @x_bounds[i][0]
                @normal_x[i] = (@x[i] - @x_bounds[i][0]) / (@x_bounds[i][1] - @x_bounds[i][0]) 
            else
                @normal_x[i]  = @x[i]
            end
        end
    end

    def denormalize
    # """
    # Function
    # --------
    # denormalize
    # 
    # Denormalizes the normalized parameter values stored in `@normal_x` to their original scale
    # based on the specified bounds in `@x_bounds`, and stores the result in `@x`.
    # 
    # This method reverses the normalization process, transforming values from the [0, 1] range
    # (or similar normalized range) back to their original physical or logical range defined by
    # the lower and upper bounds for each parameter.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any arguments. It operates on instance variables:
    # - `@num_parameters`: Integer, number of parameters to denormalize.
    # - `@normal_x`: Array of Floats, normalized parameter values (typically in [0, 1]).
    # - `@x_bounds`: Array of Arrays, where each sub-array contains two elements:
    # [lower_bound, upper_bound] for the corresponding parameter.
    # - `@x`: Array of Floats, output array to store denormalized values.
    # 
    # Returns
    # -------
    # None
    # This method modifies the instance variable `@x` in place and does not return a value.
    # """
        for i in 0..@num_parameters-1
            if @x_bounds[i][1] != @x_bounds[i][0]
                @x[i] = @x_bounds[i][0] + @normal_x[i] * (@x_bounds[i][1] - @x_bounds[i][0]) 
            else
                @x[i] = @x_bounds[i][0]
            end
        end
    end
end
