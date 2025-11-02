# 主入口
class GA
  p 'GA_Solution Ver.0.6.1'

  def initialize(optimizer, num_parameters, x_bounds, population_size, mutation_rate = 0.5, crossover_rate = 0.5)
    # """
    # Function
    # --------
    # Initializes a new instance of the optimizer class with specified parameters and settings.
    # 
    # Parameters
    # ----------
    # optimizer : Object
    # The optimization algorithm or strategy to be used, typically defining the search behavior.
    # num_parameters : Integer
    # The number of parameters (dimensions) to be optimized in the problem space.
    # x_bounds : Array[Array[Numeric]]
    # A 2D array specifying the lower and upper bounds for each parameter, where each sub-array
    # contains [lower_bound, upper_bound] for the corresponding parameter.
    # population_size : Integer
    # The number of individuals in the population used by the evolutionary algorithm.
    # mutation_rate : Float, optional
    # The probability of mutation occurring in an individual, default is 0.5.
    # crossover_rate : Float, optional
    # The probability of crossover occurring between two individuals, default is 0.5.
    # 
    # Returns
    # -------
    # None
    # This constructor does not return a value but initializes the object's state.
    # """
    @optimizer = optimizer
    @num_parameters = num_parameters
    @x_bounds = x_bounds
    @mutation_rate = mutation_rate
    @crossover_rate = crossover_rate
    @population_size = population_size

    @generations_data = [] # 记录各代数据
    # id = UI.start_timer(1, false) { MoosasOptimizer.nasg2_ready }
  end

  def init
    # """
    # Function
    # --------
    # Initialize the population pools for the genetic algorithm.
    # 
    # This method creates an initial population of solutions (`_P`) with size
    # twice the specified `@population_size`. Each solution is randomly initialized
    # within the variable bounds, evaluated, and then sorted by objective value.
    # Additional pools `_Q` and `_R` are reset, and the generation counter is set to zero.
    # The model state is backed up before initialization and restored afterward.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters. It uses instance variables:
    # - @population_size : Integer
    # The desired size of the population.
    # - @optimizer : Object
    # The optimizer instance used to create new solutions.
    # - @num_parameters : Integer
    # The number of decision variables in each solution.
    # - @x_bounds : Array[Array[Numeric]]
    # A 2D array where each sub-array contains [lower_bound, upper_bound]
    # for the corresponding parameter.
    # - $current_model : Global object
    # Represents the global simulation/model state which is backed up and restored.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It initializes internal state variables:
    # - @_P : Array[GA_Solution]
    # Initialized and sorted pool of parent solutions.
    # - @_Q : Array
    # Reset to empty array (used for offspring).
    # - @_R : nil
    # Set to nil (typically used for combined population in some algorithms).
    # - @i_generations : Integer
    # Initialized to 0.
    # Also updates external view via `update_view`.
    # """
    p "initialize pools"
    @_P = []
    pool_size = @population_size * 2
    $current_model.backup
    for i in 0..pool_size - 1
      s = GA_Solution.new(@optimizer, @num_parameters, @x_bounds)
      for j in 0..@num_parameters - 1
        s.x[j] = @x_bounds[j][0] + rand() * (@x_bounds[j][1] - @x_bounds[j][0])
      end
      s.evaluate_solution()
      @_P.push(s)
    end
    @_Q = []
    @_R = nil
    @i_generations = 0
    $current_model.restore
    # p "================================================"
    @_P = @_P.sort do |a, b|
      a.objective <=> b.objective
    end
    self.update_view(@_P)
  end

  def set_webdialog(wd)
    # """
    # Function
    # --------
    # Sets the web dialog instance for the current object.
    # 
    # Parameters
    # ----------
    # wd : Object
    # The web dialog object to be assigned. Expected to be a WebDialog or compatible object.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value.
    # """
    @web_dialog = wd
  end

  def update_generation()
    # Function:
    # Updates the current generation in an evolutionary algorithm by incrementing the generation counter,
    # combining parent and offspring populations, selecting new parents via round-robin selection,
    # generating a new offspring population, and updating the view accordingly.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    # 
    # Notes:
    # - The method modifies the internal state by incrementing `@i_generations` and updating
    # population arrays `@_P` (parent population) and `@_Q` (offspring population).
    # - Uses `round_robin_select` to select individuals from the combined population `@_R = @_P + @_Q`.
    # - Calls `make_new_pop` to generate a new offspring population after backing up and restoring
    # the global model state via `$current_model`.
    # - Invokes `update_view` to refresh the visualization with the updated parent population.
    @i_generations += 1
    p "Generation #{@i_generations}"

    @_R = @_P + @_Q
    # 选择
    @_P = self.round_robin_select(@_R)

    # 产生新一代
    $current_model.backup
    @_Q = make_new_pop(@_P)
    $current_model.restore

    # 更新视图
    self.update_view(@_P)
    # p "=================================================================================================="
  end

  # 轮盘选择算法
  def round_robin_select(_R)
    # Function:
    # Perform round-robin selection on a list of candidate solutions based on their objective values,
    # assigning selection probabilities inversely proportional to objective (lower objective = higher chance),
    # then selecting individuals via cumulative probability until the desired population size is reached.
    # 
    # Parameters:
    # _R : Array
    # An array of candidate solution objects, each having an `objective` attribute representing its fitness value.
    # Lower objective values indicate better solutions.
    # 
    # Returns:
    # _P : Array
    # An array of selected candidate solutions with length equal to `@population_size`.
    # The first `rank_n` elements are the top-ranked candidates; the remaining are selected probabilistically
    # based on normalized and cumulative probabilities derived from their energy (inverse of objective).
    # 排序
    _R = _R.sort do |a, b|
      a.objective <=> b.objective
    end
    # 计算各个方案的概率
    pr = []
    total_p = 0
    max_energy = 200.0
    n = _R.length
    _R.each do |r|
      t = max_energy - r.objective
      if t < 0
        t = 0
      end
      total_p += t
      pr.push t
    end
    for i in 0...n
      pr[i] /= total_p
    end

    # 计算各个方案的累计概率
    cpr = []
    cpr[0] = pr[0]
    for i in 1...n
      cpr[i] = cpr[i - 1] + pr[i]
    end
    _P = []
    selected_index = []
    rank_n = 3 # 每次留下前几名
    for i in 0...rank_n
      _P.push _R[i]
      selected_index.push(i)
    end

    while _P.length < @population_size
      ps = rand()
      for i in rank_n...n
        if not selected_index.include?(i) and cpr[i] >= ps
          _P.push _R[i]
          selected_index.push i
          break
        end
      end
    end
    return _P
  end

  # 根据父代P，产生子代Q
  def make_new_pop(_P)
    # """
    # Function
    # ----------
    # make_new_pop
    # Generates a new population (_Q) through genetic operations of crossover and mutation
    # based on the given parent population (_P). The size of the new population matches
    # that of the parent population.
    # 
    # Parameters
    # ----------
    # _P : Array
    # The parent population, represented as an array of solution objects. Each solution
    # object must support methods `crossover`, `mutate`, and `evaluate_solution`.
    # 
    # Returns
    # -------
    # _Q : Array
    # The newly generated population, represented as an array of solution objects.
    # Its length is equal to that of _P. Each individual in _Q is either a result of
    # crossover (and possibly mutation) from two selected parents or remains empty
    # if no operation was performed (though loop ensures full population).
    # """
    _Q = []

    while _Q.length != _P.length do

      # 杂交和变异产生下一代
      if rand() < @crossover_rate

        # 从P中挑选的两个精英
        selected_solutions = [nil, nil]
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
    # """
    # Function
    # --------
    # Selects a random element from the given array.
    # 
    # Parameters
    # ----------
    # _P : Array
    # The input array from which a random element will be selected.
    # It should not be empty to avoid potential errors.
    # 
    # Returns
    # -------
    # object
    # A randomly chosen element from the array `_P`.
    # The type of the returned object matches the element type of the array.
    # """
    return _P[rand(_P.length)]
  end

  def update_view(_P)
    # """
    # Function
    # --------
    # update_view
    # 
    # Update the view with current optimization state and send data to web interface if available.
    # 
    # This method processes the current population of solutions, extracts key information,
    # and sends the structured data to a web-based visualization interface. It also prints
    # objective value range for monitoring purposes.
    # 
    # Parameters
    # ----------
    # _P : Array
    # An array of solution objects, each containing attributes such as 'objective',
    # 'x' (parameter vector), and 'obj_record' (objective function record/history).
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. Its primary purpose is side-effect driven:
    # updating the UI and printing progress information.
    # """
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
      "x_bounds" => @x_bounds,
      "optimizer" => @optimizer,
      "num_parameters" => @num_parameters
    }

    # p "update_view #{data}"

    p "range: #{solutions[0]["objective"]}  --- #{solutions[solutions.length - 1]["objective"]}"

    if @web_dialog != nil
      @web_dialog.send("optmize_energy", data)
    end
    # MoosasOptimizer.update_view(data)
  end

  def self.test
    # Function:
    # Runs a test simulation of a genetic algorithm (GA) optimization process with predefined parameters.
    # Initializes a GA instance with a specific problem name, dimensionality, variable bounds, and population size.
    # Evolves the population over a fixed number of generations by iteratively calling the update_generation method.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    x_bounds = [[0.0, 10.0], [0.0, 10.0]]
    ga = GA.new("optimizer_test", 2, x_bounds, 20)
    # ga.update_generation(0)
    for i in 0..50
      ga.update_generation(i)
    end
  end

end

# 每个方案
class GA_Solution
  attr_accessor :x, :normal_x, :objective, :obj_record

  @@solution_counter = 0

  def initialize(optimizer, num_parameters, x_bounds)
    # Function:
    # Initialize a new solution instance with given optimizer, number of parameters, and parameter bounds.
    # Sets up internal state including optimization function mapping, decision variables, normalization,
    # and unique naming. Increments global solution counter for unique identification.
    # 
    # Parameters:
    # optimizer : str
    # Name of the optimizer method to be used, which will be mapped to 'self.evaluate_solution'.
    # num_parameters : int
    # Number of decision variables (parameters) in the solution vector.
    # x_bounds : list of tuples
    # Bounds for each parameter in the form [(x1_min, x1_max), (x2_min, x2_max), ...].
    # 
    # Returns:
    # None
    # This constructor does not return a value; it initializes instance attributes.

    @optimizer = optimizer
    @optimizer_function_name = optimizer.gsub('optimizer', 'self.evaluate_solution') + "()"

    @num_parameters = num_parameters
    @x = [0] * num_parameters
    @x_bounds = x_bounds
    @normal_x = [0] * num_parameters

    @objective = nil
    @obj_record = nil

    @@solution_counter += 1
    @name = "s" + @@solution_counter.to_s
  end

  '' '
        根据x，求解objectives
    ' ''

  def evaluate_solution()
    # """
    # Function
    # --------
    # evaluate_solution
    # 
    # Evaluates the solution by dynamically executing the optimizer function
    # referenced by the instance variable `@optimizer_function_name`.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # Any
    # The return value is the result of evaluating the optimizer function
    # specified in `@optimizer_function_name`. The type and value depend on
    # the definition of that function.
    # """
    eval(@optimizer_function_name)
  end

  def crossover(other)
    # """
    # Function
    # --------
    # Perform crossover operation between two genetic algorithm solutions to generate a child solution.
    # 
    # Parameters
    # ----------
    # other : GA_Solution
    # The other parent solution used for crossover. It must have the same number of parameters and bounds compatibility.
    # 
    # Returns
    # -------
    # GA_Solution
    # A new child solution resulting from the crossover, where part of the genes comes from the current solution (self)
    # and the rest from the 'other' solution, split at a randomly chosen index.
    # """
    child_solution = GA_Solution.new(@optimizer, @num_parameters, @x_bounds)

    started_index = rand(@num_parameters)
    for i in 0...started_index
      child_solution.x[i] = @x[i]
    end
    for i in started_index...@num_parameters
      child_solution.x[i] = other.x[i]
    end

    return child_solution
  end

  # 在x上下限范围内进行某个基因位的突变
  def mutate()
    # """
    # Function
    # --------
    # mutate
    # Randomly selects one gene (parameter) from the individual's parameter array and mutates it by assigning a new
    # random value within the specified bounds for that parameter. This method is typically used in evolutionary
    # algorithms to introduce genetic diversity.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on instance variables:
    # - @num_parameters: The total number of parameters (genes) in the individual.
    # - @x: An array representing the current values of the parameters (the individual's genotype).
    # - @x_bounds: A 2D array where each row contains the lower and upper bounds [min, max] for the corresponding parameter.
    # 
    # Returns
    # -------
    # None
    # This method modifies the @x array in place and does not return any value.
    # """
    mutate_gene_i = rand(@num_parameters)
    @x[mutate_gene_i] = @x_bounds[mutate_gene_i][0] + rand() * (@x_bounds[mutate_gene_i][1] - @x_bounds[mutate_gene_i][0])
  end

  def normalize
    # """
    # Function
    # --------
    # normalize
    # 
    # Normalizes the input parameters to the unit interval [0, 1] based on their respective bounds.
    # If the lower and upper bounds for a parameter are equal, the normalized value is set to the original value.
    # 
    # Parameters
    # ----------
    # None
    # This method operates on instance variables:
    # - @x : Array[Numeric]
    # The array of original parameter values to be normalized.
    # - @x_bounds : Array[[Numeric, Numeric]]
    # The array of bound pairs [lower_bound, upper_bound] for each parameter.
    # - @num_parameters : Integer
    # The number of parameters to normalize.
    # - @normal_x : Array[Numeric]
    # The array that will store the normalized parameter values (must be pre-initialized).
    # 
    # Returns
    # -------
    # None
    # This method modifies the instance variable @normal_x in place and does not return a value.
    # """
    for i in 0..@num_parameters - 1
      if @x_bounds[i][1] != @x_bounds[i][0]
        @normal_x[i] = (@x[i] - @x_bounds[i][0]) / (@x_bounds[i][1] - @x_bounds[i][0])
      else
        @normal_x[i] = @x[i]
      end
    end
  end

  def denormalize
    # """
    # Function
    # --------
    # denormalize
    # 
    # Denormalizes the normalized parameter values back to their original scale
    # based on the specified bounds. This method transforms each parameter from
    # its normalized value (typically in [0,1]) to the corresponding real-world
    # value within the given bounds.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any arguments. It operates on instance variables:
    # - @num_parameters : Integer
    # Number of parameters to denormalize.
    # - @x_bounds : Array[Array[Numeric]]
    # An array of [min, max] bounds for each parameter.
    # - @normal_x : Array[Numeric]
    # Array of normalized parameter values (usually in [0, 1]).
    # - @x : Array[Numeric]
    # Output array where denormalized values will be stored.
    # 
    # Returns
    # -------
    # None
    # This method modifies the instance variable @x in place and does not return a value.
    # """
    for i in 0..@num_parameters - 1
      if @x_bounds[i][1] != @x_bounds[i][0]
        @x[i] = @x_bounds[i][0] + @normal_x[i] * (@x_bounds[i][1] - @x_bounds[i][0])
      else
        @x[i] = @x_bounds[i][0]
      end
    end
  end

  def evaluate_solution_energy
    # """
    # Function
    # --------
    # evaluate_solution_energy
    # 
    # Evaluates the energy performance of a solution by updating window-to-wall ratios (WWR)
    # on model boundaries based on design variables and computes the total objective value
    # from energy analysis results.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any explicit parameters. It uses instance variables:
    # - @x : Array[Numeric]
    # An array of four numeric values representing WWRs for four directions.
    # - @bounds_in_dir : Array[Array[Boundary]] or nil
    # Stores boundary elements grouped by direction; initialized if nil.
    # - $current_model : Model
    # Global variable representing the current building model to be analyzed.
    # - MoosasEnergy : Module
    # External module used for performing energy analysis.
    # 
    # Returns
    # -------
    # Numeric
    # The computed objective value as the sum of all components in the energy analysis
    # result (`er.total`). This value is stored in `@objective`. The method also updates:
    # - @obj_record : Array[Numeric]
    # Raw energy result components returned by `er.total.to_array()`.
    # - @bounds_in_dir : Array[Array[Boundary]]
    # Lazily initialized list of boundaries grouped by cardinal direction.
    # """

    # 根据x，修改模型的参数
    if @bounds_in_dir == nil
      @bounds_in_dir = $current_model.get_all_bounds_in_direction
    end
    wwr = [@x[0], @x[1], @x[2], @x[3]]

    for dir_i in 0...4
      wwr_i = wwr[dir_i]
      @bounds_in_dir[dir_i].each do |b|
        b.wwr = wwr_i
      end
    end

    # 评价模型
    er = MoosasEnergy.analysis($current_model)
    @obj_record = er.total.to_array()
    p @obj_record
    @objective = eval(@obj_record.join("+"))
  end

  def evaluate_solution_test
    # Function:
    # Evaluates the objective function for a given solution in a two-dimensional space.
    # The objective function is defined as the sum of squared differences between
    # the first element of the solution vector and 2, and the second element and 4.
    # 
    # Parameters:
    # None (the method uses the instance variable @x, which is expected to be an array of numeric values
    # with at least two elements, and modifies the instance variable @objective)
    # 
    # Returns:
    # None (the result is stored in the instance variable @objective)
    @objective = (@x[0] - 2) ** 2 + (@x[1] - 4) ** 2
  end
end

$moosas_energy_ga = nil

