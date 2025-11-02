class MoosasEnergy
  Ver = '0.6.3'

  @sr = [280100, 175200, 213200, 116300, 280100]
  @wr = [150800, 355200, 123600, 051500, 150800]

  def self.analysis(model, building_type, require_radiation)
    # Function
    # --------
    # Perform energy analysis on a building model based on weather data and space geometry, optionally calculating solar radiation.
    # This method computes thermal loads for cooling, heating, and lighting by analyzing each space's envelope (walls, windows, roof, etc.),
    # and invokes an external energy simulation executable to generate results. Output is structured into totals, per-space breakdowns,
    # and monthly load profiles.
    # 
    # Parameters
    # ----------
    # model : Model
    # The building model containing spaces, weather data, and settings. Must have valid `spaces`, `weather`, and associated attributes.
    # building_type : str
    # Specifies the type of building. Used to determine which energy simulation executable to invoke:
    # if matching localized "居住建筑" or "Residence", uses residential energy simulator; otherwise uses public/commercial.
    # require_radiation : bool
    # If true, skips internal radiation calculation and assumes radiation values are already present in space settings.
    # If false, triggers zone-level solar radiation computation via `calculate_zone_radation` for each space.
    # 
    # Returns
    # -------
    # e_data : dict
    # A dictionary containing the following keys:
    # - "total": Array of three floats representing total annual cooling, heating, and lighting energy (in kWh).
    # - "spaces": Array of arrays, each representing a space with elements:
    # [cooling_energy, heating_energy, lighting_energy, total_energy, normalized_area_factor, zone_name],
    # sorted by total energy consumption.
    # - "months": Array of arrays, each representing monthly energy loads (cooling, heating, lighting) over the year.
    # - "area": Array of normalized area factors for each space, calculated as scaled proportional floor areas raised to 0.2 power.
    model.load_weather_data()
    weather = model.weather
    weather_path = MPath::WEATHER + weather.station_id + ".csv"

    if not require_radiation
      # p require_radiation
      t2 = Time.new
      $current_model.spaces.each { |s|
        # p "#{s.id}:#{s.settings['zone_summerrad']}"
        if s.settings['zone_summerrad'] == nil
          s.calculate_zone_radation(model)
        end
      }
      MoosasUtils.backup_setting_data()

      t3 = Time.new
      p "辐射计算用时： #{t3 - t2}s"
    end

    latitude = (weather.station_info["lat"] * Math::PI / 180).round(2).to_s
    altitude = (weather.station_info["ele"]).to_f.round(2).to_s
    # lines=[weather_path + "," + latitude + "," + altitude + ","]
    lines = []
    totalOutsideArea, totalVolumn = 0, 0
    spacefloorarea = []
    for i in 0..model.spaces.length - 1 do
      s = model.spaces[i]
      spacefloorarea.push(s.area_m.round(2))
      line = s.height_m.round(2).to_s + "," + s.area_m.round(2).to_s + ","
      totalVolumn += s.area_m * s.height_m
      outsideArea, facadeArea, windowArea = 0, 0, 0
      summerSolar, winterSolar = 0.0, 0.0
      s.bounds.each do |b|
        if not b.is_internal_edge
          totalOutsideArea += b.area_m
          outsideArea += self.non(b.get_length_in_m - 5.0) * 5.0
          facadeArea += b.area_m * (1 - b.wwr)
          windowArea += b.area_m * b.wwr
          o = self.calculate_orientation(b.normal) # W:0 S:90 E:180 N:270
          summerSolar += (@sr[o / 90] + ((o % 90).to_f / 90.0) * (@sr[o / 90 + 1] - @sr[o / 90])) * b.area_m * b.wwr
          winterSolar += (@wr[o / 90] + ((o % 90).to_f / 90.0) * (@wr[o / 90 + 1] - @wr[o / 90])) * b.area_m * b.wwr
        end
      end
      if not require_radiation
        summerSolar, winterSolar = s.settings['zone_summerrad'] * 60, s.settings['zone_winterrad'] * 60 # kWh to KJ
      end
      line += outsideArea.round(2).to_s + "," + facadeArea.round(2).to_s + "," + windowArea.round(2).to_s + ","
      roofArea, skylightArea = 0, 0
      s.ceils.each do |c|
        if c.type == MoosasConstant::ENTITY_ROOF
          totalOutsideArea += c.area_m
          roofArea += c.area_m
        elsif c.type == MoosasConstant::ENTITY_SKY_GLAZING
          totalOutsideArea += c.area_m
          skylightArea += c.area_m
        end
      end
      line += roofArea.round(2).to_s + "," + skylightArea.round(2).to_s + ","
      floorArea = 0
      s.floor.each { |fl|
        if fl.type == MoosasConstant::ENTITY_GROUND_FLOOR
          floorArea += fl.area_m
        end }

      line += floorArea.round(2).to_s + "," + summerSolar.round(2).to_s + "," + winterSolar.round(2).to_s + ","
      # 每个space的参数设置
      if s.settings["zone_inflitration"] == nil
        s.settings["zone_inflitration"] = '0.5'
      end
      line += s.settings["zone_wallU"] + "," + s.settings["zone_winU"] + "," + s.settings["zone_win_SHGC"] + "," + s.settings["zone_c_temp"] + "," + s.settings["zone_c_hum"] + "," + s.settings["zone_h_temp"] + "," + s.settings["zone_collingEER"] + "," + s.settings["zone_HeatingEER"] + "," + s.settings["zone_work_start"] + "," + s.settings["zone_work_end"] + "," + s.settings["zone_ppsm"] + "," + s.settings["zone_pfav"] + "," + s.settings["zone_popheat"] + "," + s.settings["zone_equipment"] + "," + s.settings["zone_lighting"] + "," + s.settings["zone_inflitration"] + "," + s.settings["zone_nightACH"].chomp
      lines.push(line)
    end
    # lines[0] += (totalOutsideArea / totalVolumn).round(2).to_s
    energy_i = MPath::DATA + "energy/Energy.i"
    energy_o = MPath::DATA + "energy/Energy.o"
    args = " -w \"#{weather_path}\" -l #{latitude} -a #{altitude} -o \"#{energy_o}\"" +
      " -s " + (totalOutsideArea / totalVolumn).round(2).to_s +
      " \"#{energy_i}\""

    # 生成输入文件,调用exe生成输出文件
    File.write(energy_i, lines.join("\n"))
    if $language == 'Chinese'
      prm = "居住建筑"
    else
      prm = "Residence"
    end
    if building_type == prm
      system("\"#{MPath::ENERGY_RES}\"" + args)
      # p "\"#{MPath::ENERGY_RES}\""+args
    else
      system("\"#{MPath::ENERGY_PUBLIC}\"" + args)
    end

    output = []
    File.open(energy_o, "r") do |file|
      while line = file.gets
        if line[0] != "!" and line[0] != ";"
          list = line.split(",")
          c = list[0].to_f
          h = list[1].to_f
          l = list[2].to_f
          output.push([c, h, l])
        end
      end
    end

    spacefloorarea = spacefloorarea.map { |area| (area *spacefloorarea.length / spacefloorarea.sum()) ** 0.2 }

    total, spaces, months = output[0], [], []
    for i in 1..model.spaces.length do
      # 制冷能耗、供暖能耗、照明能耗、总能耗、房间面积、房间名称
      spaces.push([
                    output[i][0],
                    output[i][1],
                    output[i][2],
                    output[i].sum(),
                    spacefloorarea[i - 1],
                    model.spaces[i - 1].settings['zone_name']])
      # spaces[i-1].push()
      # spaces[i-1].push(spacefloorarea[i-1])
      # spaces[i-1].push(model.spaces[i-1].settings['zone_name'])
    end

    for i in model.spaces.length + 1..output.length - 1 do
      months.push(output[i])
    end

    # p spacefloorarea
    e_data = { "total" => total, "spaces" => spaces.sort_by { |k| k[3] }, "months" => months, "area" => spacefloorarea }

    return e_data
  end

  def self.calculate_orientation(n)
    # """
    # Function
    # --------
    # calculate_orientation
    # 
    # Calculate the orientation angle in degrees from a 2D vector.
    # 
    # This method computes the clockwise angle from the negative x-axis to the given 2D vector `n`,
    # measured in degrees and normalized to the range [0, 360). The angle is calculated using
    # the arccosine of the x-component divided by the magnitude of the vector, then adjusted
    # based on the y-component to determine the correct quadrant.
    # 
    # Parameters
    # ----------
    # n : Array<Numeric>
    # A two-element array representing a 2D vector, where `n[0]` is the x-component
    # and `n[1]` is the y-component. The vector should not be zero.
    # 
    # Returns
    # -------
    # Integer
    # The orientation angle in degrees, as an integer in the range [0, 360).
    # Returns 0 if the computed angle is exactly 360.
    # """
    o = (Math.acos((-1) * (n[0]) / Math.sqrt((n[0]) ** 2 + (n[1]) ** 2)) * 180 / Math::PI).to_i
    if n[1] > 0
      o = 360 - o
    end
    if o == 360
      o = 0
    end
    return o
  end

  def self.non(x)
    # Function:
    # Returns the input value if it is positive, otherwise returns zero.
    # 
    # Parameters:
    # x : numeric
    # The input number to be evaluated. Can be an integer or float.
    # 
    # Returns:
    # numeric
    # Returns `x` if `x` is greater than 0; otherwise, returns 0.
    return x > 0 ? x : 0
  end

end
