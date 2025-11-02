module MoosasAnalysis
  Ver = '0.6.3'

  def self.main_analysis(require_recognize_model, building_type, require_radiation)
    # """
    # Function
    # --------
    # Perform main analysis including model recognition, energy analysis, and daylight factor calculation,
    # then store and send the results through web interface.
    # 
    # Parameters
    # ----------
    # require_recognize_model : str
    # A string indicating whether to perform model recognition. Expected values are "true" or "false".
    # If "true", the method will invoke model recognition; otherwise, it uses the current model.
    # building_type : str
    # The type of building for energy analysis. This affects how energy consumption is calculated.
    # require_radiation : str
    # A string indicating whether solar radiation analysis is required. Interpreted as boolean:
    # if "true", radiation will be included in energy analysis.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It sends analysis results via MoosasWebDialog,
    # updates metadata storage, and saves backup files.
    # """

    if require_recognize_model == "true"
      t1 = Time.new
      model = MMR.recognize_floor(remodel = false)
      t2 = Time.new
      p "模型识别用时： #{t2 - t1}s"
    else
      model = $current_model
    end
    t1 = Time.new
    e_data = MoosasEnergy.analysis(model, building_type, require_radiation == "true")
    t2 = Time.new
    p "能耗分析用时： #{t2 - t1}s"
    dfs = MoosasDaylight.quick_analysis_ave_daylight_factor(model)
    # p dfs
    data = {
      "area" => model.get_total_area(),
      "energy" => e_data,
      "dfs" => dfs
    }
    meta_current_data = MoosasMeta.get_and_set_dic("moosas", "current", JSON.generate(data), false)
    # 备份数据
    $performance_data["energy"] = e_data
    MoosasWebDialog.send("main_analysis_result", data)

    # 备份模型文件
    backup_path = MoosasUtils.back_up_model()
    history_data = {
      "area" => model.get_total_area(),
      "energy" => e_data["total"],
      "backup_path" => backup_path
    }
    # 存储历史分析数据（模型路径，总能耗，照明、空调、采暖三个分项能耗）
    meta_history_data = MoosasMeta.get_and_set_dic("moosas", "history", JSON.generate(history_data), true)
    # 更新历史数据图表
    # p history_data
    MoosasWebDialog.send("update_analysis_history", meta_history_data)
  end

  def self.params_analysis(type, params)
    # Function:
    # Perform parameter analysis for a given type and set of parameters in the current model context. The method handles different types of analyses (e.g., wall_u, win_u, etc.) using a specific mode, retrieves associated boundary information, and sends results to a web dialog if available. It also ensures model state is preserved via backup and restore operations.
    # 
    # Parameters:
    # type : str
    # A string specifying the type of parameter analysis to perform. Supported values include "wall_u", "win_u", "win_shgc", and "wwr". Other values are currently unhandled.
    # params : dict or list
    # Input parameters required for the analysis. Structure and content depend on the analysis type. Used as input for the corresponding analysis mode method.
    # 
    # Returns:
    # None
    # This method does not explicitly return a value. However, it modifies internal state (e.g., caches bounds data), generates analysis results stored in `results`, enriches them with boundary information, and optionally sends the results to a web-based dialog interface. Any exceptions during execution are logged.

    begin
      if $current_model == nil
        MMR.recognize_floor
      end

      if @all_bounds_in_dir == nil
        @all_bounds_in_dir = $current_model.get_all_bounds_in_direction
      end

      $current_model.backup

      # 参数分析
      case type
      when "wall_u", "win_u", "win_shgc", "wwr"
        results = self.params_analysis_mode_1($current_model, type, params)
      else
      end
      $current_model.restore

      # 统计参数取值分布
      results.each do |res|
        res["bis"] = self.get_target_bounds_info(res["type"], res["target"])
        # if $performance_data["energy"] != nil
        #    res["cur_energy"] = $performance_data["energy"].total
        # end
      end

      if MoosasWebDialog.dialog != nil
        MoosasWebDialog.send("params_analysis_result", results)
      end
    rescue Exception => e
      MoosasUtils.rescue_log(e)
    end

  end

  # 多目标参数分析
  def self.multi_goal_params_analysis(type, params)
    # Function:
    # Perform multi-goal parameter analysis for specific building envelope components based on given parameters and analysis type.
    # The method supports different directional surfaces (e.g., south, east, west, north, roof) and modifies model parameters accordingly.
    # It conducts the analysis by backing up the current model state, executing the specified analysis mode, and restoring the model afterward.
    # Results include boundary information for each target and can be sent to a web dialog interface if available.
    # 
    # Parameters:
    # type : str
    # The type of analysis to perform. Currently supports "wwr" (window-to-wall ratio) and potentially other custom types.
    # Determines which analysis mode is invoked.
    # params : Array<Hash>
    # An array of hashes, each defining a parameter set for analysis. Each hash contains:
    # - "target": Integer indicating the building surface to modify:
    # 8 = all surfaces,
    # 0 = south wall,
    # 3 = east wall,
    # 1 = west wall,
    # 2 = north wall,
    # 4 = roof.
    # - "range": Array of two numeric values [min, max] specifying the parameter variation range.
    # - "step": Numeric value indicating the increment step within the range.
    # 
    # Returns:
    # None
    # This method does not return a value directly. Instead, it processes results internally and sends them asynchronously
    # via MoosasWebDialog.send() if a dialog instance is active. The actual results are structured as an array of hashes
    # containing analysis outcomes, including modified parameter values, associated boundary information ("bis"),
    # and potentially current performance metrics (e.g., energy).

    begin
      if $current_model == nil
        MMR.recognize_floor
      end
      if @all_bounds_in_dir == nil
        @all_bounds_in_dir = $current_model.get_all_bounds_in_direction
      end

      $current_model.backup

      # 参数分析
      case type
      when "wwr"
        results = self.params_analysis_mode_2($current_model, type, params)
      else
      end

      $current_model.restore

      # 统计参数取值分布
      results.each do |res|
        res["bis"] = self.get_target_bounds_info(res["type"], res["target"])
        # if $performance_data["energy"] != nil
        #    res["cur_energy"] = $performance_data["energy"].total
        # end
      end

      if MoosasWebDialog.dialog != nil
        MoosasWebDialog.send("params_multi_goal_analysis_result", results)
      end
    rescue Exception => e
      MoosasUtils.rescue_log(e)
    end

  end

  # 对东、西、南、北面墙体的参数进行变化分析
  # params = [{"target"=>0,"range"=>[0,1], "step"=>0.1}]
  # target: 8=all, 0=south, 3=east, 1=west, 2=north, 4=roof
  def self.params_analysis_mode_1(model, type, params)
    # """
    # Function
    # --------
    # Perform a parametric analysis on a building energy model by varying specific parameters
    # (such as window-to-wall ratio, U-values, SHGC) across a defined range and recording energy performance.
    # 
    # This method modifies the specified parameter for selected building boundaries (based on orientation),
    # runs energy simulations iteratively, and collects the resulting energy data. It supports different
    # types of envelope parameter analyses including WWR, wall U-value, window U-value, and window SHGC.
    # 
    # Parameters
    # ----------
    # model : object
    # The building energy model object that contains geometry, boundary conditions, and simulation settings.
    # Must support `get_all_bounds` and be compatible with `MoosasEnergy.analysis`.
    # 
    # type : str
    # The type of parameter to analyze. Supported values are:
    # - "wwr": Window-to-Wall Ratio
    # - "wall_u": Wall thermal transmittance (U-value)
    # - "win_u": Window U-value
    # - "win_shgc": Window Solar Heat Gain Coefficient
    # 
    # params : list of dict
    # A list of parameter configurations, each containing:
    # - "target" (int): Orientation target (e.g., MoosasConstant::ORIENTATION_ALL for all orientations).
    # - "range" (array-like): A two-element array specifying the [min, max] value range for the parameter.
    # - "step" (float): Increment step size for sweeping through the range.
    # - "name" (str): Descriptive name for this parameter set.
    # - "buildingtype" (str): Building type used in energy simulation (passed to MoosasEnergy.analysis).
    # 
    # Returns
    # -------
    # list of dict
    # A list where each element represents the result of one parametric run, containing:
    # - "type" (str): The analyzed parameter type.
    # - "target" (int): The orientation target.
    # - "range" (list): The [min_v, max_v] range used.
    # - "step" (float): Step size used in the sweep.
    # - "values" (list of dict): List of {"x": param_value, "y": energy_result} pairs from simulation.
    # - "name" (str): Name identifier for the parameter set.
    # """
    results = []

    params.each do |param|
      res = {}
      # 根据分析目标，先收集，需要改变数据的边
      all_bounds = model.get_all_bounds
      target = param["target"].to_i
      if target == MoosasConstant::ORIENTATION_ALL
        target_bounds = all_bounds
      else
        target_bounds = []
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
        # 修改参数
        case type
        when "wwr"
          target_bounds.each do |b|
            b.wwr = x
          end
        when "wall_u"
          target_bounds.each do |b|
            b.settings["opaque"][1] = x
          end
        when "win_u"
          target_bounds.each do |b|
            b.settings["glazing"][1] = x
          end
        when "win_shgc"
          target_bounds.each do |b|
            b.settings["glazing"][2] = x
          end
        else
          y = 0.0
        end
        # 调用模拟
        e_data = MoosasEnergy.analysis(model, param['buildingtype'], true)
        y = e_data["total"]
        pair = { "x" => x, "y" => y }
        # p "#{x},#{y.join(",")}"
        values.push pair
        x += step
      end
      # 逐个分析，并且记录
      res["type"] = type
      res["target"] = param["target"]
      res["range"] = [min_v, max_v]
      res["step"] = step
      res["values"] = values
      res["name"] = param["name"]
      results.push res
    end
    # 返回数据
    return results
  end

  # 参数：窗墙比
  # 目标：快速能耗分析，快速采光分析
  def self.params_analysis_mode_2(model, type, params)
    # Function:
    # Performs a parametric analysis on a building model using a specified parameter set, modifying
    # geometric or performance-related properties (e.g., window-to-wall ratio) and evaluating energy
    # consumption and daylighting performance across a range of values. This method supports multi-goal
    # evaluation by recording both energy usage and average daylight factor.
    # 
    # Parameters:
    # model : OpenStudio::Model::Model
    # The OpenStudio building model to be analyzed.
    # type : str
    # The type of parameter to vary; currently supports "wwr" (window-to-wall ratio). Other types
    # result in no parameter modification.
    # params : list of dict
    # A list of dictionaries, each defining a parameter variation scenario. Each dictionary contains:
    # - "target": int, specifies the orientation to modify (using MoosasConstant::ORIENTATION_ALL for all).
    # - "range": list of float, defines the [min, max] range of the parameter value.
    # - "step": float, increment step size for sweeping through the range.
    # - "buildingtype": str, building type used in energy simulation.
    # - "name": str, name identifier for the parameter set.
    # 
    # Returns:
    # list of dict
    # A list where each element is a dictionary containing:
    # - "type": str, the parameter type being varied.
    # - "target": int, the orientation target.
    # - "range": list of float, the [min, max] range of variation.
    # - "step": float, step size used.
    # - "values": list of dict, time-series data for each step with keys:
    # - "x": float, current parameter value.
    # - "y1": float, total energy consumption (summed over all fuel types).
    # - "y2": float, average daylight factor across the model.
    # - "name": str, name of the parameter set.
    results = []

    params.each do |param|
      res = {}
      # 根据分析目标，先收集，需要改变数据的边
      all_bounds = model.get_all_bounds
      target = param["target"].to_i
      if target == MoosasConstant::ORIENTATION_ALL
        target_bounds = all_bounds
      else
        target_bounds = []
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
        # 修改参数
        case type
        when "wwr"
          target_bounds.each do |b|
            b.wwr = x
          end
        else
          y1 = 0.0
          y2 = 0.0
        end
        # 调用能耗模拟
        e_data = MoosasEnergy.analysis(model, param["buildingtype"], true)
        y1 = e_data["total"].reduce(:+)
        # 调查快速采光分析
        dfs = MoosasDaylight.quick_analysis_ave_daylight_factor(model)
        area = 0
        df = 0
        dfs.each do |d|
          area += d[1]
          df += d[0] * d[1]
        end
        y2 = df / area
        pair = { "x" => x, "y1" => y1, "y2" => y2 }
        p "multi_goal_params_analysis: #{type}, #{target}, #{pair}"
        values.push pair
        x += step
      end
      # 逐个分析，并且记录
      res["type"] = type
      res["target"] = param["target"]
      res["range"] = [min_v, max_v]
      res["step"] = step
      res["values"] = values
      res["name"] = param["name"]
      results.push res
    end
    # 返回数据
    return results
  end

  def self.get_target_bounds_info(type, target)
    # """
    # Function
    # --------
    # Get target bounds information based on the specified type and target.
    # 
    # This method retrieves a list of specific property values (such as WWR, U-values, or SHGC)
    # from boundary objects associated with a given target. The property extracted is determined
    # by the `type` parameter, which selects which attribute or setting from each bound to return.
    # 
    # Parameters
    # ----------
    # type : str
    # A string specifying the type of information to retrieve. Valid options include:
    # - "wwr": Window-to-wall ratio.
    # - "wall_u": U-value of the opaque wall component.
    # - "win_u": U-value of the glazing component.
    # - "win_shgc": Solar heat gain coefficient of the glazing component.
    # target : str
    # A string identifying the target whose bounds are to be queried. This key is used
    # to access the corresponding bounds stored in the class variable `@all_bounds_in_dir`.
    # 
    # Returns
    # -------
    # list
    # A list of values corresponding to the requested property (`type`) for each bound
    # associated with the given `target`. The elements in the list are typically numeric
    # (Float), but may vary depending on the data stored in the bound objects' settings.
    # """
    bs = @all_bounds_in_dir[target]
    bis = []
    bs.each do |b|
      case type
      when "wwr"
        bis.push b.wwr
      when "wall_u"
        bis.push b.settings["opaque"][1]
      when "win_u"
        bis.push b.settings["glazing"][1]
      when "win_shgc"
        bis.push b.settings["glazing"][2]
      else

      end
    end
    # p bis
    return bis
  end

  def self.update_moosas_model_parameters_setting(tag, value)
    # Function:
    # Updates the model parameters for a specific boundary type and target orientation in the Moosas model. The method modifies properties such as window-to-wall ratio (WWR), wall U-value, window U-value, and SHGC based on the provided tag and value.
    # 
    # Parameters:
    # tag : str
    # A string in the format "type-target", where "type" specifies the parameter to update
    # (e.g., "wwr", "wall_u", "win_u", "win_shgc"), and "target" indicates the orientation
    # index or MoosasConstant::ORIENTATION_ALL for all orientations.
    # value : float or str
    # The numeric value to set for the specified parameter. Will be converted to float before assignment.
    # 
    # Returns:
    # None
    # This method does not return a value. It performs in-place updates on the model's boundary settings
    # and prints a success message upon completion.
    arr = tag.split("-")
    type = arr[0]
    target = arr[1].to_i
    value = value.to_f

    all_bounds = $current_model.get_all_bounds
    if target == MoosasConstant::ORIENTATION_ALL
      target_bounds = all_bounds
    else
      target_bounds = []
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
        b.settings["opaque"][1] = value
      end
    when "win_u"
      target_bounds.each do |b|
        b.settings["glazing"][1] = value
      end
    when "win_shgc"
      target_bounds.each do |b|
        b.settings["glazing"][2] = value
      end
    else
    end
    p "success: update_moosas_model_parameters_setting!"
  end
end

$performance_data = {}