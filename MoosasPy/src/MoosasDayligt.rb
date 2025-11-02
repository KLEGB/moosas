class MoosasDaylight
  Ver = '0.6.3'

  class << self
    attr_accessor :current_grids, :ssg # sourrouding_shading_geometry
  end

  def self.local_analysis_daylight(space_id)
    # Function:
    # Perform a daylight analysis for specified spaces in a SketchUp model using Radiance simulation.
    # The method supports both full-model and single-space analysis, collects user-defined simulation parameters via UI input,
    # generates analysis grids on horizontal faces, exports geometry and grid data for Radiance, executes the simulation,
    # assigns results back to grids, and visualizes the outcome either within SketchUp or via an external HTML interface.
    # 
    # Parameters:
    # space_id : Integer
    # Identifier of the space to be analyzed when not analyzing all spaces. This value is used to index into the model's
    # collection of spaces (`$current_model.spaces`). It will be converted to an integer if provided as a string.
    # 
    # Returns:
    # None
    # This method does not return a value explicitly. However, it modifies global state by updating `MoosasDaylight.current_grids`
    # with the resulting grid objects containing simulation data. It also triggers visualization either in SketchUp (via colored
    # grids and a scale observer) or in an external web dialog using WebGL rendering.

    rendered = true
    if $language == 'Chinese'
      result = UI.messagebox('需要分析全部空间吗?', MB_YESNO)
    else
      result = UI.messagebox('Analizing all spaces?', MB_YESNO)
    end
    analysis_faces = []
    transformations = []
    if result == IDYES
      $current_model.spaces.each do |s|
        s.floor.each { |f|
          analysis_faces.push(f.face)
          transformations.push (f.transformation)
        }
      end
    else
      # 选择分析的房间编号
      # prompts = ["空间编号："]
      # defaults = ["0"]
      # input = UI.inputbox(prompts, defaults, "请输入待分析的空间编号！")
      # space_id = input[0].to_i()
      p "Analize the space No.#{space_id}"
      $current_model.spaces[space_id.to_i].floor.each { |fl|
        analysis_faces.push(fl.face)
        transformations.push(fl.transformation)
      }
    end

    model = Sketchup.active_model
    entities = model.active_entities
    selection = model.selection
    if $language == 'Chinese'
      prompts = ["网格大小：", "网格高度：", "模拟时间：", "天空模型"]
      defaults = ["0.5", "0.72", "01-20-14:00", "晴朗天空，清澄大气"]
      params = defaults
      params.push(15000)
      lists = ["", "", "", "晴朗天空，清澄大气|晴朗天空，浑浊大气|多云天空，太阳的周边亮|多云天空，看不见太阳|全阴天"]
      input = UI.inputbox(prompts, defaults, lists, "请输入采光计算参数")
      params[0] = input[0].to_f()
      params[1] = input[1].to_f()
      params[2] = input[2]
      params[3] = input[3]

      if input[3] == "全阴天"
        uni_diff = UI.inputbox(["全阴天照度"], ["15000"], "全阴天模拟设定")
        params[4] = uni_diff[0].to_f()
      end
    else
      prompts = ["Grid size", "Reference height", "Date and time", "Sky model"]
      defaults = ["0.5", "0.72", "01-20-14:00", "clear sky"]
      params = defaults
      params.push(15000)
      lists = ["", "", "", "clear sky|clear sky without sun|cloudy sky|cloudy sky without sun|uniform sky"]
      input = UI.inputbox(prompts, defaults, lists, "Please enter required simulation parameters")
      params[0] = input[0].to_f()
      params[1] = input[1].to_f()
      params[2] = input[2]
      params[3] = input[3]

      if input[3] == "uniform sky"
        uni_diff = UI.inputbox(["sky illuminance(lux)"], ["15000"], "uniform sky illuminance")
        params[4] = uni_diff[0].to_f()
      end
    end
    # p params[4]
    # rendered=(input[4]=="Y")
    rendered = true

    # 导出rad文件
    # if $exported_model_updated_number != $model_updated_number
    self.export_radiance_geometry(params)
    # p "成功导出几何文件"
    #    $exported_model_updated_number = $model_updated_number
    # end

    # grids = MoosasGrid.fit_selection(selection, model, entities, faces,params,true,global_transformation)
    grids = MoosasGrid.fit_grids_for_horizational_face(entities, analysis_faces, transformations, params, rendered)

    # p grids
    self.export_grid_file(grids)
    # p "成功导出分析网格"
    p "RADIANCE export successfully. Executing *.bat......"
    # if rendered == true
    #    scaleObserver = Moosas::GridScaleObservers[model]
    #    scaleObserver.closeScale() if scaleObserver
    #    scaleObserver.clearGridStasticsInfo() if scaleObserver
    # end

    # 调用radiance文件进行计算
    if self.execute_radiance_bat_script()
      # 读取结果,并将结果赋予grid
      valuerange = self.assign_result_to_grid(grids)
      params.push(valuerange)
    end

    # 采光模拟结果数据备份
    MoosasDaylight.current_grids = grids
    # p grids

    if rendered == true
      MoosasDaylight.render_daylight_in_skp(params)
      # #可视化方式一：在SketchUp模型中渲染网格
      # grids.each do |grid|
      #     MoosasGrid.color_grid(grid)
      # end
      # selection.clear
      # selection.add(grids)
      # Moosas::GridScaleObservers[model].showScale
      # Moosas::GridScaleObservers[model].showGridStasticsInfo
    else
      # 可视化方式二：在html上绘制结果
      daylight_gird_data = []
      grids.each do |grid|
        daylight_gird_data.push MoosasGrid.pack_grid_data(grid)
      end
      daylight_result = {
        "grids" => daylight_gird_data
      }
      # p daylight_result
      MoosasWebDialog.send("update_daylight_webgl", daylight_result)
    end

  rescue => e
    MoosasUtils.rescue_log(e)
  end

  def self.render_daylight_in_skp(params)
    # """
    # Function
    # --------
    # Renders daylight analysis results in the SketchUp model by coloring grids and displaying a scale panel.
    # 
    # Parameters
    # ----------
    # params : Array
    # An array containing rendering parameters. Expected structure:
    # - params[2] : String
    # The time period for the simulation.
    # - params[3] : String
    # The sky model type (e.g., "uniform sky" or localized equivalent).
    # - params[4] : Numeric or String
    # Illuminance value, included in description if sky model is overcast/uniform.
    # - params[5] : Numeric
    # Maximum value for the color scale used in rendering.
    # 
    # Returns
    # -------
    # None
    # This method performs side effects: it modifies the SketchUp model by coloring grid entities,
    # updates the selection, and draws a scale panel. No value is returned.
    # """
    Sketchup.active_model.start_operation("采光渲染", true)
    # 可视化方式一：在SketchUp模型中渲染网格
    MoosasDaylight.current_grids.each do |grid|
      MoosasGrid.color_grid(grid)
    end
    model = Sketchup.active_model
    entities = model.active_entities
    selection = model.selection
    selection.clear
    selection.add(MoosasDaylight.current_grids)
    description = "Point in Time Simulation\nLocation:#{MoosasWeather.singleton.station_info["city"]}\nPriod:#{params[2]}\nSky model:#{params[3]}"
    if $language == 'Chinese'
      prm = "全阴天"
    else
      prm = "uniform sky"
    end
    if params[3] == prm
      description += "\nIlluminance:#{params[4]}"
    end
    scaleRender = MoosasGridScaleRender.new(0, params[5], description = description)
    scaleRender.draw_panel()
    # Moosas::GridScaleObservers[model].showScale
    # Moosas::GridScaleObservers[model].showGridStasticsInfo
    Sketchup.active_model.commit_operation
  end

  def self.execute_radiance_bat_script
    # Function:
    # Executes a Radiance batch script and manages directory context and error logging.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # Boolean: Returns true if the batch script executes successfully, false otherwise.

    pwd = MPath::RAD
    Dir.chdir pwd

    t1 = Time.new
    begin
      system("run_moosas.bat")
      return true
    rescue => e
      MoosasUtils.rescue_log(e)
      return false
    ensure
      Dir.chdir File.dirname(__FILE__)
    end

    t2 = Time.new

    p "Simulation duration#{t2 - t1}s"
  end

  def self.assign_result_to_grid(grids)
    # Function
    # --------
    # Assigns simulation results from a radiance output file to corresponding grid cells in a 3D model, calculates illuminance metrics such as daylight satisfaction and uniformity for outer zones, and updates grid attributes accordingly.
    # 
    # Parameters
    # ----------
    # grids : Array of Grid objects
    # A collection of grid objects, each containing attribute dictionaries with node layout information. The method reads radiant flux values (in lux) and assigns them to the respective nodes within each grid. Each grid is expected to have an attribute dictionary named "grid" that includes a "nodes" key representing a 2D array indicating active or inactive nodes.
    # 
    # Returns
    # -------
    # Integer
    # The computed value range for illuminance visualization, derived from the 80th percentile of all radiant values, rounded up to the nearest multiple of 500. This value is used for consistent scaling across visualizations.
    rads = []

    output_file = MPath::RAD + "ill_moosas.output"
    File.open(output_file, "r").each_line do |line|
      if line != nil
        rads.push line.to_f()
      end
    end
    all_satis = 0.0
    all_i = 0
    i = 0
    valuerange = (rads.sort[(rads.length * 0.8).to_i] / 500).ceil() * 500
    # p valuerange

    grids.each do |grid|
      dict = grid.attribute_dictionaries["grid"]
      nodes = dict["nodes"]
      results = []
      nodes.each do |row|
        rad_row = []
        row.each do |node|
          if node
            rad_row.push rads[i]
            i += 1
          else
            rad_row.push 0.0
          end
        end
        results.push rad_row
      end
      dict["results"] = results
      dict["type"] = "illuminance"
      dict["valueRange"] = valuerange

      # 统计外区参数
      satis = 0.0 # 统计采光满足率 > 300 lux
      sum = 0.0
      min = 9999999.0
      n = 0 # 外区网格数
      ny = nodes.length
      iy = 0
      j = 0
      nodes.each do |row|
        nx = row.length
        ix = 0
        row.each do |node|
          if node
            lux = rads[j]
            if (iy < 6 or (ny -iy) <= 6) and (ix < 6 or (nx -ix) <= 6) # 属于外区
              n += 1
              if lux > 300
                satis += 1
              end
              if lux < min
                min = lux
              end
              sum += lux
            end
            j += 1
          end
          ix += 1
        end
        iy += 1
      end
      if n != 0
        all_satis = all_satis + satis
        satis = satis / n * 100

        all_i = all_i + n
        ave = sum / n
        sameness = min / ave # 统计采光均匀度 一个值
        p "Daylighting satifaction of outer zone(>300lux) = #{format("%04.2f", satis)}%"
        p "Daylighting uniformity = #{format("%03.2f", sameness)}"
      end

    end
    all_satis = all_satis / all_i
    p "Average satification(>300lux) = #{format("%04.2f", all_satis)}%"
    return valuerange
  end

  IDENTITY_TRANSFORMATION = Geom::Transformation.new

  # 可进一步优化，只获取待分析建筑周围的几何体
  def self.export_radiance_geometry(params)
    # """
    # Function
    # --------
    # export_radiance_geometry
    # 
    # Export geometry data from the current model to a Radiance-compatible file format,
    # transforming SketchUp entity coordinates into Radiance input format with unit
    # conversion and material assignment.
    # 
    # Parameters
    # ----------
    # params : Hash
    # A dictionary of parameters used to configure the Radiance export, including
    # settings for sky conditions and other environmental parameters. Passed directly
    # to `get_sky` method for generating the sky portion of the Radiance scene.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It performs side effects by writing a `.rad`
    # file to the filesystem at the location specified by `MPath::RAD + 'model.rad'`.
    # 
    # Notes
    # -----
    # - The method retrieves all faces from the current model using `get_all_face`.
    # - Faces marked with type `ENTITY_IGNORE` or those that are deleted are skipped.
    # - Vertex positions are transformed using the face's transformation matrix and
    # converted from inches to meters (via multiplication by 0.0254).
    # - Geometry text is generated via `format_face_text`, incorporating face ID,
    # transformed vertices, and associated material.
    # - The final Radiance file includes sky configuration, material library (from
    # `get_material_lib`), and the formatted geometry.
    # - Output is written to `model.rad` in the directory defined by `MPath::RAD`.
    # """

    geo_text = ""

    mofaces = $current_model.get_all_face

    mofaces.each { |mf|
      if mf.type != MoosasConstant::ENTITY_IGNORE and not mf.face.deleted?
        e = mf.face
        pts = e.vertices.map { |v|
          pt = mf.transformation * v.position
          [pt.x * 0.0254, pt.y * 0.0254, pt.z * 0.0254]
        }
        geo_text += self.format_face_text(mf.id, pts, mf.material) + "\n"
      end
    }

    rad_text = self.get_sky(params) + "\n" + get_material_lib() + "\n" + geo_text
    rad_file = MPath::RAD + "model.rad"
    File.open(rad_file, "w+") do |f|
      f.puts rad_text
    end
  end

  def self.get_mesh_polygons(mesh, transformation)
    # """
    # Function
    # --------
    # Transforms and converts mesh polygons into a list of 3D point coordinates after applying a transformation matrix and unit scaling.
    # 
    # Parameters
    # ----------
    # mesh : Mesh
    # A mesh object containing `points` (list of 3D points) and `polygons` (list of polygon indices).
    # Each polygon is assumed to be a triplet of indices referring to the points array.
    # transformation : Geom::Transformation
    # A transformation matrix applied to each point in the mesh to transform their coordinates.
    # 
    # Returns
    # -------
    # Array<Array<Array<Float>>>
    # A nested array structure representing transformed and scaled polygons:
    # - Outer array: one element per polygon.
    # - Middle array: three elements per triangle (assumes triangular polygons).
    # - Inner array: three floats representing the [x, y, z] coordinates in meters,
    # converted from inches using a scale factor of 0.0254.
    # """
    tpts = mesh.points.map { |x| transformation * x }
    polys = []
    # p "tpts=#{tpts}"
    for pol in mesh.polygons
      pts = []
      # p "pol=#{pol}"
      for i in 0..2
        pi = tpts[pol[i].abs - 1]
        pt = [pi.x * 0.0254, pi.y * 0.0254, pi.z * 0.0254]
        pts.push(pt)
      end
      polys.push(pts)
    end
    return polys
  end

  def self.is_glazing(face)
    # """
    # Function
    # --------
    # Determines whether a given face is considered glazed based on its material's alpha value.
    # 
    # Parameters
    # ----------
    # face : object
    # A face object that is expected to have a `material` attribute. The material should
    # support an `alpha` property representing its transparency or opacity level.
    # 
    # Returns
    # -------
    # bool
    # True if the face has a material and the material's alpha value is less than
    # the defined threshold (MATERIAL_ALPHA_THRESHOLD); otherwise, False.
    # """
    if face.material && face.material.alpha < MoosasConstant::MATERIAL_ALPHA_THRESHOLD
      return true
    else
      return false
    end
  end

  def self.format_face_text(poly_name, pts, idx)
    # """
    # Function
    # --------
    # Formats a polygon face description text for Radiance simulation using given points and material information.
    # 
    # Parameters
    # ----------
    # poly_name : str
    # Name of the polygon, used to identify the specific face in the output text.
    # pts : list of lists or array-like
    # List of 3D points defining the polygon vertices. Each point is an array with x, y, z coordinates.
    # idx : int
    # Index referencing an entry in the global `$rad_lib` array to retrieve category and name for material.
    # 
    # Returns
    # -------
    # str
    # Formatted string representing the Radiance polygon definition, including material name,
    # polygon name, number of coordinates, and vertex positions, each on a new line.
    # """
    material_name = $rad_lib[idx].category + "_" + $rad_lib[idx].name
    text = material_name + " polygon #{poly_name} 0 0 #{pts.length * 3}\n"
    pts.each do |pt|
      text += "   #{pt[0]} #{pt[1]} #{pt[2]}\n"
    end
    return text
  end

  def self.get_material_lib()
    # Function:
    # Generates a formatted string representation of material definitions for Radiance simulation,
    # based on the visible light transmittance (VLT) and other optical properties. The method
    # computes adjusted transmittance values for glass materials using an empirical formula
    # and formats all materials according to Radiance syntax.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: A newline-separated string containing Radiance-formatted material definitions,
    # including headers, material types (plastic, glass, trans), their optical properties,
    # and proper formatting as required by Radiance. The output is structured with
    # category and material name joined by an underscore, and includes computed tn
    # values for glass based on VLT input.
    '' '
        sketch_win：根据用户设定的可见光透过率来设定
        Visible Light Transmittance (VLT) : Tn
        =>    void glass sketch_win 0 0 3 tn tn tn 
        =>    tn =  (Math.sqrt(0.8402528435+0.0072522239*Tn*Tn)-0.9166530661)/0.0036261119/Tn
        => VLT : 0.737, tn = 0.803
        => VLT : 0.803, tn = 0.874
        => VLT : 0.915, tn = 0.996
        ' ''
    lines = ["####Materials"]
    rad_lab = $current_model.get_all_rad_material
    rad_str = rad_lab.keys.each { |idx|
      material = $rad_lib[idx]
      lines.push(["void", material.rad_mat["type"], material.category + "_" + material.name].join(" "))
      lines.push("0")
      lines.push("0")
      if material.rad_mat["type"] == "plastic"
        lines.push(["5", material.rad_mat["R"], material.rad_mat["G"], material.rad_mat["B"], material.rad_mat["spec"], material.rad_mat["rough"]].join(" "))
      elsif material.rad_mat["type"] == "glass"
        tn = [material.rad_mat["R"], material.rad_mat["G"], material.rad_mat["B"]].each { |trans| (Math.sqrt(0.8402528435 + 0.0072522239 * trans.to_f * trans.to_f) - 0.9166530661) / 0.0036261119 / trans.to_f }
        lines.push(["3", tn[0].to_s, tn[1].to_s, tn[2].to_s].join(" "))
      elsif material.rad_mat["type"] == "trans"
        lines.push(["7", material.rad_mat["R"], material.rad_mat["G"], material.rad_mat["B"], material.rad_mat["spec"], material.rad_mat["rough"], 0, 0].join(" "))
      end
    }
    lines.push("")
    lines.push("####Materials")
    return lines.join("\n")
  end

  def self.get_sky(params)
    # """
    # Function
    # --------
    # Generate a sky description string based on input parameters and date-time information using the MoosasCIESky model.
    # 
    # Parameters
    # ----------
    # params : Array
    # An array containing configuration parameters where:
    # - params[2] : String
    # A date-time string in the format 'YYYY-MM-DD HH:MM:SS'.
    # - params[3] : Integer or Key
    # Index or key used to select a sky type from MoosasCIESky::SKY_TYPE.
    # - params[4] : Float or Numeric
    # A numeric parameter (e.g., luminance or solar angle) used to initialize the sky model.
    # 
    # Returns
    # -------
    # String
    # A generated sky description string produced by the MoosasCIESky model based on the given date and parameters.
    # """
    date = params[2].split('-')
    date[2] = date[2].split(':')[0]
    sky = MoosasCIESky.new(MoosasCIESky::SKY_TYPE[params[3]], params[4])
    # sky=MoosasCIESky.new()
    sky_str = sky.gen_sky_from_date(datetime = date)
    return sky_str
  end

  def self.export_grid_file(grids)
    # """
    # Function
    # --------
    # Export grid data to a formatted text file.
    # 
    # Converts a collection of grid objects into a text file where each line represents
    # a 3D point (node) in the grid, scaled from inches to meters (using factor 0.0254),
    # rounded to 5 decimal places, and appended with constant values for additional fields.
    # The output is saved to a predefined path under the name 'grid.input'.
    # 
    # Parameters
    # ----------
    # grids : Array
    # An array of grid objects. Each grid must support the `get_attribute` method
    # to retrieve node data under the key "grid" with attribute name "nodes".
    # The nodes are expected to be a nested structure (Array of Arrays) where
    # each node is an array containing at least three numeric values [x, y, z] in inches.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It performs a side effect by writing
    # the processed grid data to a file on disk.
    # """
    lines = []
    grids.each do |grid|
      nodes = grid.get_attribute("grid", "nodes")
      # t_nodes = []
      nodes.each do |row|
        # t_row = []
        row.each do |node|
          if node
            x = (node[0] * 0.0254).round(5)
            y = (node[1] * 0.0254).round(5)
            z = (node[2] * 0.0254).round(5)
            lines.push "#{x} #{y} #{z} 0 0 1"
          end
          # t_row.push(node)
        end
        # t_nodes.push(t_row)
      end
      # grid.set_attribute("grid", "nodes",t_nodes)
    end
    text = lines.join("\n")
    grid_file = MPath::RAD + "grid.input"
    File.open(grid_file, "w+") do |f|
      f.puts text
    end
  end

  def self.get_ent_global_transformantion(ent)
    # """
    # Function
    # --------
    # Computes the global transformation of a given entity by collecting its occurrence paths and determining the corresponding transformation.
    # 
    # Parameters
    # ----------
    # ent : Sketchup::Entity
    # The entity for which the global transformation is to be computed. Must be a valid SketchUp model entity.
    # 
    # Returns
    # -------
    # Geom::Transformation
    # The global transformation matrix representing the cumulative transformation of the entity in the model context.
    # Returns nil if no instance path is found or if transformation computation fails.
    # """
    instance_paths = self.collect_occurences(ent)
    p "instance_paths=#{instance_paths}"
    global_transformation = self.get_transformation_for_instance_path(instance_paths)
    return global_transformation
  end

  def self.get_transformation_for_instance_path(instance_path)
    # """
    # Function
    # --------
    # Computes the cumulative transformation matrix for a given instance path by multiplying
    # transformations of all valid instances in the path.
    # 
    # Parameters
    # ----------
    # instance_path : Array<Object>
    # An array representing a path of objects, typically from a component hierarchy.
    # Only objects that respond to the `transformation` method (e.g., ComponentInstance)
    # are considered in the transformation calculation. Objects like Model or DrawingElement,
    # which do not have transformations, are filtered out.
    # 
    # Returns
    # -------
    # Geom::Transformation
    # The combined transformation obtained by successively applying the transformation
    # of each instance in the filtered path. If no valid transformations are found,
    # returns an identity transformation.
    # """
    transformation = Geom::Transformation.new()
    instance_path.reject { |noninstance| # Model or DrawingElement do not have a transformation.
      !noninstance.respond_to?(:transformation)
    }.each { |instance|
      transformation *= instance.transformation
    }
    p "get_transformation_for_instance_path=#{transformation}"
    return transformation
  end

  def self.collect_occurences(instance)
    # """
    # Function
    # ----------
    # collect_occurences
    # Collects all instance occurrence paths from the given component instance
    # up to the top-level model in a SketchUp model hierarchy. Traverses upward
    # through parent instances using a breadth-first search approach.
    # 
    # Parameters
    # ----------
    # instance : Sketchup::ComponentInstance
    # The starting component instance from which to collect all occurrence paths.
    # This instance is expected to be part of a component hierarchy within a SketchUp model.
    # 
    # Returns
    # -------
    # Array<Array<Sketchup::ComponentInstance>>
    # An array of paths, where each path is an array of component instances
    # representing the hierarchical chain from the top-level model down to the
    # target instance. Each path starts with an instance at the root level
    # (immediate child of the model) and ends with the input instance.
    # """
    instance_paths = []
    queue = [[instance]]
    until queue.empty?
      path = *(queue.shift)
      outer = path.first
      if outer.parent.is_a?(Sketchup::Model)
        instance_paths << path
      else
        outer.parent.instances.each { |uncle|
          queue << [uncle] + path
        }
      end
    end
    return instance_paths
  end

  def self.traverse_faces(entity, path = [], &func)
    # """
    # Function
    # --------
    # Recursively traverses a hierarchy of SketchUp entities to find and process all Face objects.
    # 
    # This method walks through groups, component instances, and collections of entities, applying
    # a given function to each Face encountered. The traversal maintains the ancestral path to each
    # face, which can be passed to the provided function for context.
    # 
    # Parameters
    # ----------
    # entity : Sketchup::Face or Sketchup::Group or Sketchup::ComponentInstance or Sketchup::Entities or Sketchup::Selection or Enumerable
    # The entity to traverse. Can be a single face, group, component instance, or a collection
    # of entities (such as an Entities container, Selection, or any Enumerable object).
    # 
    # path : Array, optional, default: []
    # A list representing the ancestral path from the root to the current container.
    # Used internally during recursion to track the nesting of groups and components.
    # 
    # func : Proc or lambda
    # A callable object (block) that will be invoked for each Sketchup::Face found.
    # The block may accept either one argument (the face) or two arguments (the face and the path).
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It is used for side effects via the provided block.
    # """
    case entity
    when Sketchup::Face
      func.arity == 1 ? func.call(entity) : func.call(entity, path)
    when Sketchup::Group
      traverse_faces(entity.entities, path + [entity], &func)
    when Sketchup::ComponentInstance
      traverse_faces(entity.definition.entities, path + [entity], &func)
    when Sketchup::Entities, Sketchup::Selection, Enumerable
      entity.each { |e| traverse_faces(e, path, &func) }
    end
  end

  def self.user_visible?(e)
    e.visible? && e.layer.visible?
  end

  # 快速估算采光系数值
  def self.quick_analysis_ave_daylight_factor(model)
    # Function
    # --------
    # Calculate the average daylight factor for each space in a building model using a simplified quick analysis method.
    # The daylight factor is calculated based on window area, window-to-wall ratio (WWR), light transmittance,
    # and floor area. A maximum cap of 100% is applied to the resulting daylight factor.
    # 
    # Parameters
    # ----------
    # model : OpenStudio::Model::Model
    # The OpenStudio building model containing spaces and their associated geometry and envelope properties.
    # 
    # Returns
    # -------
    # Array<Array<Numeric, Numeric>>
    # An array of arrays, where each sub-array contains two elements:
    # - df (Numeric): The calculated daylight factor (%) for the space, capped at 100%.
    # - floor_area (Numeric): The floor area (m²) of the corresponding space.
    spaces = model.spaces
    sn = spaces.length
    dfs = []
    light_transmittance = 0.6 # 采光透过率
    for i in 0..sn - 1
      s = spaces[i]
      floor_area = s.area_m
      window_area = 0.0
      s.bounds.each do |b|
        if not b.is_internal_edge
          window_area += b.area_m * b.wwr
        end
      end
      df = 45 * window_area * light_transmittance / floor_area / 0.76
      if df > 100
        df = 100
      end
      dfs.push [df, floor_area]
    end
    return dfs
  end

  # 旧版本backup
  def self.format_wall_text(poly_name, pts)
    # """
    # Function
    # --------
    # Formats a wall sketch description as a string in a custom text format for a given polygon name and list of 3D points.
    # 
    # Parameters
    # ----------
    # poly_name : str
    # The name of the polygon, used to identify the sketch_wall command (note: appears unused in current implementation).
    # pts : list of lists or array-like
    # A list of 3D points, where each point is an array or list containing three numeric values [x, y, z].
    # 
    # Returns
    # -------
    # str
    # A formatted string representing the wall sketch, starting with a header line specifying the polygon type,
    # identifier, zero offsets, and total number of coordinates (3 per point), followed by indented lines for each point's x, y, z values.
    # """
    text = "sketch_wall polygon #{id} 0 0 #{pts.length * 3}\n"
    pts.each do |pt|
      text += "   #{pt[0]} #{pt[1]} #{pt[2]}\n"
    end
    return text
  end

  def self.format_glazing_text(id, pts)
    # """
    # Function
    # --------
    # Formats glazing geometry data into a text representation for use in simulation input.
    # 
    # Parameters
    # ----------
    # id : int or string
    # Identifier for the glazing element, used to label the polygon in the output text.
    # pts : array_like of shape (N, 3)
    # List of 3D points defining the vertices of the glazing polygon. Each point is an array/tuple containing x, y, z coordinates.
    # 
    # Returns
    # -------
    # string
    # Formatted string representing the glazing polygon in 'sketch_win' format, including:
    # - Header line with keyword, ID, two zero fields, and total number of coordinate values (3 per point).
    # - Subsequent lines listing each vertex's x, y, z coordinates indented by three spaces.
    # """
    text = "sketch_win polygon #{id} 0 0 #{pts.length * 3}\n"
    pts.each do |pt|
      text += "   #{pt[0]} #{pt[1]} #{pt[2]}\n"
    end
    return text
  end

  # 标注周围遮挡的面，纳入计算
  def self.label_sourrouding_shading
    # Function:
    # Placeholder method intended for defining or processing label surrounding shading logic within a class context. Currently contains no implementation.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
  end
end

$exported_model_updated_number = nil