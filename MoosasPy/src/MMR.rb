# 模型识别模块
module MMR
  require 'rexml/document'
  require 'set'
  include REXML
  require 'matrix'
  Ver = '0.6.3'

  INCH_METER_MULTIPLIER = 0.0254
  INCH_METER_MULTIPLIER_SQR = 0.0254 * 0.0254
  IDENTITY_TRANSFORMATION = Geom::Transformation.new
  MATERIAL_ALPHA_THRESHOLD = 0.99
  @geometries = []
  $current_model = nil
  $ontologies = nil
  @all_recognized_faces = []
  NJTD = 0.05 / 0.0254 # 法向量判断平移距离

  HIDDEN_STATUS = false

  def self.recognize_floor(remodel = false)
    "" "
    Recognizes floors and constructs spaces from the SketchUp model.

    Function:
      Exports model geometry, runs transformation processing, identifies spaces (including ground floor),
      assigns face types, attaches shading, and updates the model with recognized elements.

    Parameters:
      remodel (bool, optional): Whether to remodel the model (solve duplicates/redundancies). Defaults to false.

    Returns:
      MoosasModel: The constructed model containing recognized spaces, faces, and shading elements.
    " ""
    begin
      MoosasRender.disable_visualize_entity_type($current_model) if $current_model != nil
    rescue
      0
    end

    model = Sketchup.active_model
    model.start_operation("Extract Floor:", true)
    t2 = Time.new

    # 构建MoosasFace并导出.geo或.xml
    # p "recognize_floor v0.601.5"
    # p "working dictionary: "+File.dirname(__FILE__)
    # p File.dirname(__FILE__)+"/../python/geo/model.xml"
    zip_command = self.model_to_text
    @geometries = zip_command['geometries']
    p "model export to: #{zip_command['input_file']}"
    # show_id(geometries)

    # 运行MoosasPy.transform
    if self.exec_transform(zip_command['input_file'], zip_command['output_file'], zip_command['geo_file'], remodel)
      p "successfully get:", zip_command['output_file']
      @geometries = self.geo_to_lib(zip_command['geo_file'], true)
      $ontologies = zip_command['owl_file']
      p "update geometries"
      spaces = self.read_xml(zip_command['output_file'])

    else
      p "Failed to run MoosasMain.exe. please check:"
      p MPath::DATA
      return false
    end
    # 确定groundfloor并赋予基本面属性
    groundHeight = 1000
    for i in 0..spaces.length - 1
      if spaces[i].floor[0].height < groundHeight
        groundHeight = spaces[i].floor[0].height
      end
    end

    space_sort = []
    # 确定各个面的具体属性,对space进行排序
    for i in 0..spaces.length - 1
      spaces[i].assign_type_directly(groundHeight)
      # entities = model.active_entities
      # entities=spaces[i].visualize_orientation(entities)
      # show_space_info(spaces[i])
      space_sort.push([spaces[i]] + spaces[i].get_quick_location)
    end
    space_sort = space_sort.sort { |x, y| [x[3], x[2], x[1]] <=> [y[3], y[2], y[1]] }
    spaces = space_sort.map { |sp| sp[0] }

    @spaces = spaces
    p "Space Number=#{@spaces.size}"
    if @spaces.size == 0
      p '***Error: no spaces were constrcuted'
      return
    end
    model.commit_operation
    mm = MoosasModel.new(spaces)

    # 定义shading
    all_id = mm.get_all_face.map { |face| face.id }
    shading = @geometries.map { |face| face if not (all_id.include?(face.id)) }
    shading.each { |moface| attach_shading(mm, moface) }

    $current_model = mm
    $model_updated_number += 1
    MoosasUtils.retrive_setting_data
    MoosasUtils.backup_setting_data
    # self.visualize_factor

    t3 = Time.new
    p "识别用时： #{t3 - t2}s"
    model_data = mm.pack_data
    MoosasWebDialog.send("update_model_data", model_data)
    @all_recognized_faces = mm.get_all_face
    # 更新面的默认类型表格
    @all_recognized_faces.each do |mf|
      MoosasRender.update_define_materials(mf.face, mf.type)
    end

    return mm
  end

  def self.all_recognized_faces
    "" "
    Retrieves all non-deleted recognized faces.

    Function:
      Filters the stored recognized faces to exclude those that have been deleted from the model.

    Parameters:
      None

    Returns:
      Array[MoosasFace]: List of non-deleted MoosasFace objects.
    " ""
    moosas_faces = []
    @all_recognized_faces.each do |mf|
      unless mf.face.deleted?
        moosas_faces.push(mf)
      end
    end
    return moosas_faces
  end

  def self.attach_shading(model, shdingface)
    "" "
    Attaches shading properties to a face and adds it to the model's shading list.

    Function:
      Sets the face type to surrounding shading, adds it to the model's shading collection,
      and assigns the appropriate material.

    Parameters:
      model (MoosasModel): The model to which the shading face is added.
      shdingface (MoosasFace): The face to be marked as shading.

    Returns:
      None
    " ""
    begin
      shdingface.type = MoosasConstant::ENTITY_SURROUNDING
      model.shading.push(shdingface)
      shdingface.assign_material($rad_lib)
    rescue
    end
  end

  def self.update_model
    "" "
    Updates the model if changes in recognized faces are detected.

    Function:
      Checks if the current model exists and if the number of recognized faces has changed;
      triggers re-recognition (remodel) if updates are needed.

    Parameters:
      None

    Returns:
      None
    " ""
    if $current_model == nil
      p 'no_model'
      self.recognize_floor(remodel = true)
      return
    end
    if @all_recognized_faces.length != self.all_recognized_faces.length
      p 'update_model'
      self.recognize_floor(remodel = true)
      return
    end
  end

  def self.is_glazing(face)
    "" "
    Determines if a face is glazing based on material transparency.

    Function:
      Checks if the face has a material with alpha value below the threshold (semi-transparent).

    Parameters:
      face (Sketchup::Face): The face to check.

    Returns:
      bool: True if the face is glazing, False otherwise.
    " ""
    if face.material && face.material.alpha < MoosasConstant::MATERIAL_ALPHA_THRESHOLD
      return true
    else
      return false
    end
  end

  def self.get_category(face)
    "" "
    Retrieves the category code of a face.

    Function:
      Maps the face's defined material type (or glazing status) to a standardized category code.

    Parameters:
      face (Sketchup::Face): The face to categorize.

    Returns:
      Integer: Category code (e.g., 3 for wall, 5 for glazing, 0 for default).
    " ""

    mat_translate = {
      MoosasConstant::ENTITY_WALL => 3,
      MoosasConstant::ENTITY_INTERNAL_WALL => 3,
      MoosasConstant::ENTITY_GLAZING => 5,
      MoosasConstant::ENTITY_INTERNAL_GLAZING => 5,
      MoosasConstant::ENTITY_SKY_GLAZING => 6,
      MoosasConstant::ENTITY_ROOF => 4,
      MoosasConstant::ENTITY_FLOOR => 4,
      MoosasConstant::ENTITY_GROUND_FLOOR => 4,
      MoosasConstant::ENTITY_SHADING => -1,
      MoosasConstant::ENTITY_PARTY_WALL => 3,
      MoosasConstant::ENTITY_DOOR => 5,
      MoosasConstant::ENTITY_AIRWALL => 2,
      MoosasConstant::ENTITY_SURROUNDING => -1,
      MoosasConstant::ENTITY_IGNORE => -2
    }
    if $define_materials.has_key?(face.persistent_id)
      return mat_translate[$define_materials[face.persistent_id]]
    else
      if self.is_glazing(face)
        return 1
      else
        return 0
      end
    end

  end

  def self.model_to_text()
    "" "
    Exports model geometry to text-based .geo files.

    Function:
      Traverses selected faces/groups, applies world transformations, converts coordinates to meters,
      and writes face data (vertices, normals, categories) to .geo files.

    Parameters:
      None

    Returns:
      Hash: Contains geometries (MoosasFace list), input_file (geo paths), output_file (xml paths),
            geo_file (processed geo paths), and owl_file (ontology paths).
    " ""
    input_file, output_file, geo_file, owl_file = [], [], [], []
    model = Sketchup.active_model
    model.start_operation("Export model to geo", true)
    group_entities = model.selection.grep(Sketchup::Group).map { |group| group.entities }
    set_group, set_select = Set.new(), Set.new()
    self.traverse_faces(group_entities) { |e, path| set_group.add(e) }
    self.traverse_faces(model.selection) { |e, path| set_select.add(e) }
    set_remain = set_select.difference(set_group)
    if set_remain.size != 0
      group_entities.push(set_remain.to_a)
    end
    p "Selection include groups: " + group_entities.length.to_s
    geometries = []
    total_face_number = 0
    id = -1
    for i in 0..group_entities.length - 1
      geometries[i] = []
      model_text = ""
      self.traverse_faces(group_entities[i]) do |e, path|
        if user_visible?(e) && path.all? { |p| user_visible? p }
          geo_text = ""
          transformation = path.inject(IDENTITY_TRANSFORMATION) { |t, f| t * f.transformation }
          id += 1
          cat = self.get_category(e)
          normal = e.normal
          # cat=1 if self.is_glazing(e)

          pts_outer = e.outer_loop.vertices.map { |v|
            pt = transformation * v.position
            [pt.x * INCH_METER_MULTIPLIER, pt.y * INCH_METER_MULTIPLIER, pt.z * INCH_METER_MULTIPLIER]
          }

          pts_loops = []
          e.loops.each { |loop|
            if loop != e.outer_loop
              lpts = loop.vertices.map { |v|
                pt = transformation * v.position
                [pt.x * INCH_METER_MULTIPLIER, pt.y * INCH_METER_MULTIPLIER, pt.z * INCH_METER_MULTIPLIER]
              }
              pts_loops.push(lpts)
            end
          }

          pts_outer.each { |pt| geo_text += "fv,#{pt[0].round(3)},#{pt[1].round(3)},#{pt[2].round(3)}\n" }
          for ix in 0..pts_loops.length - 1
            pts_loops[ix].each { |pt| geo_text += "fh,#{ix},#{pt[0].round(3)},#{pt[1].round(3)},#{pt[2].round(3)}\n" }
          end

          model_text += "f,#{cat},#{i}_#{id}\n"
          model_text += "fn,#{normal.x},#{normal.y},#{normal.z}\n"
          model_text += geo_text
          model_text += ";\n"
          geometries[i].push(MoosasFace.new(e, transformation, e.area, e.normal, "#{i}_#{id}"))
        end
      end
      input_file.push(MPath::DATA + "geometry/selection" + i.to_s + '.geo')
      output_file.push(MPath::DATA + "geometry/selection" + i.to_s + '.xml')
      owl_file.push(MPath::DATA + "geometry/selection" + i.to_s + '.owl')
      geo_file.push(MPath::DATA + "geometry/selection" + i.to_s + '_out.geo')
      File.write(MPath::DATA + "geometry/selection" + i.to_s + '.geo', model_text)
    end
    return { 'geometries' => geometries, 'input_file' => input_file, 'output_file' => output_file, 'geo_file' => geo_file, 'owl_file' => owl_file }
  end

  def self.geo_to_lib(geo_file, reform = true)
    "" "
    Imports processed .geo files and reconstructs faces in the SketchUp model.

    Function:
      Reads .geo data, projects vertices to coplanar positions, creates faces with materials,
      and updates the geometries list with new MoosasFace objects.

    Parameters:
      geo_file (Array[String]): Paths to processed .geo files.
      reform (bool, optional): Whether to reconstruct faces. Defaults to true.

    Returns:
      Array[MoosasFace]: Updated list of reconstructed MoosasFace objects.
    " ""
    valid_id, geo_pts, cats, geo_normals = [], [], [], []
    offset = Sketchup.active_model.bounds.depth * 1.1

    for file_i in 0..geo_file.length - 1
      gfile = geo_file[file_i]
      File.open(gfile, "r") do |f|
        geostr = []
        while line = f.gets
          if line[0] == ";"
            cats.push(geostr[0][1])
            valid_id.push(geostr[0][2])
            pts = []
            for stri in 0..geostr.length - 1
              if geostr[stri][0] == "fv"
                pts.push([geostr[stri][1].to_f() / 0.0254, geostr[stri][2].to_f() / 0.0254, geostr[stri][3].to_f() / 0.0254])
              end
              if geostr[stri][0] == "fn"
                geo_normals.push([geostr[stri][1].to_f(), geostr[stri][2].to_f(), geostr[stri][3].to_f()])
              end
            end
            geo_pts.push(pts)
            geostr = []
          else
            line = line.strip().split(",")
            geostr.push(line)
          end
        end
      end

      valid_id.each { |geo_id|
        if geo_id[0] == "n"
          reform = true
        end }

      if reform
        model = Sketchup.active_model
        materials = model.materials
        materialWll = materials.add('wall')
        materialWll.color = 'White'
        materialWll.alpha = 1.0
        materialGls = materials.add('glass')
        materialGls.color = 'Blue'
        materialGls.alpha = 0.7
        materialAir = materials.add('air')
        materialAir.color = 'Gray'
        materialAir.alpha = 0.1
        # group = model.entities.add_group
        new_geometries = []

        for geoI in 0..valid_id.length - 1
          gid = valid_id[geoI]
          pts = geo_pts[geoI]
          ent = model.entities
          ent = model.entities.add_group.entities

          pts = self.simplified(pts, offset)
          if pts.length < 3
            next
          end
          if geo_normals[geoI][2] == 0 or geo_normals[geoI][0] + geo_normals[geoI][1] == 0
            e = ent.add_face(pts)
          else
            # e = self.add_2d_face(ent,pts,geo_normals[geoI])
            e = self.draw_coplanar_face(ent, pts, geo_normals[geoI])

          end

          if cats[geoI] == "0"
            e.material = materialWll
            e.back_material = materialWll
          end
          if cats[geoI] == "1"
            e.material = materialGls
            e.back_material = materialGls
          end
          if cats[geoI] == "2"
            e.material = materialAir
            e.back_material = materialAir
          end
          transformation = self.get_world_transformation(e)
          new_geometries.push(MoosasFace.new(e, transformation, e.area, e.normal, gid))
        end
        @geometries[file_i] = new_geometries
      end

    end
    new_geometries = []
    @geometries.each { |geoseries| geoseries.each { |geo| new_geometries.push(geo) } }
    @geometries = new_geometries
    return @geometries
  end

  def self.exec_transform(input_file, output_file, geo_file, remodel = false)
    "" "
    Executes Python transformation script to process .geo files.

    Function:
      Generates Python code to run MoosasPy.transform, handles model processing (duplicate removal, etc.),
      and executes the script with appropriate Python interpreter.

    Parameters:
      input_file (Array[String]): Paths to input .geo files.
      output_file (Array[String]): Paths to output .xml files.
      geo_file (Array[String]): Paths to processed .geo files.
      remodel (bool, optional): Whether to enable advanced processing. Defaults to false.

    Returns:
      bool: True if the Python script executed successfully, False otherwise.
    " ""
    code = ["from MoosasPy import transform,saveModel"]
    console = remodel
    for i in 0..input_file.length - 1
      if remodel
        remodel = "True"
      else
        remodel = "False"
      end
      code.push("model = transform('#{input_file[i]}','#{output_file[i]}',geo_path='#{geo_file[i]}',solve_duplicated=True,solve_redundant=#{remodel},solve_contains=#{remodel},break_wall_vertical=#{remodel},break_wall_horizontal=#{remodel},attach_shading=False)")
      code.push("saveModel(model,'#{output_file[i][0..-4] + 'owl'}')")
    end
    if @geometries.length > 1000
      return MoosasUtils.exec_python("transform.py", code, console = console)
    else
      return MoosasUtils.exec_python("transform.pyw", code, console = console)
    end
  end

  def self.read_xml(files)
    "" "
    Reads .xml files and constructs space objects from processed geometry data.

    Function:
      Parses wall, face, glazing, and space data from .xml, constructs MoosasEdge and MoosasSpace objects,
      and maps geometry to spaces.

    Parameters:
      files (Array[String]): Paths to .xml files containing space data.

    Returns:
      Array[MoosasSpace]: List of constructed space objects, or nil if files are missing.
    " ""
    spaces = []
    for xml_file in files
      if !FileTest::exists?(xml_file)
        p "File not exist. check:"
        p xml_file
        return nil
      end

      # initialize
      walls = {}
      faces = {}
      glazings = {}
      spc_xml = File.new(xml_file)
      spc_doc = Document.new(spc_xml)
      root = spc_doc.root
      model = Sketchup.active_model
      entities = model.active_entities

      root.each_element('wall') do |w_element|
        face_uid = w_element.get_elements('Uid')[0].text
        walls[face_uid] = w_element
      end
      root.each_element('face') do |f_element|
        face_uid = f_element.get_elements('Uid')[0].text
        faces[face_uid] = f_element
      end
      root.each_element('glazing') do |g_element|
        face_uid = g_element.get_elements('Uid')[0].text
        glazings[face_uid] = g_element
      end
      root.each_element('skylight') do |s_element|
        face_uid = s_element.get_elements('Uid')[0].text
        glazings[face_uid] = s_element
      end

      root.each_element('space') do |spc|
        _floor, _ceiling, _edge, _bounds = [], [], [], []
        topology = spc.get_elements('topology')[0]

        topology.each_element('floor') { |fl_element|
          fl_element.each_element('face') { |fid|
            f = faces[fid.text]
            floorface = self.construct_face(f, glazings)
            if floorface == nil
              next
            end
            _floor += floorface
          }
        }

        topology.each_element('ceiling') { |ci_element|
          ci_element.each_element('face') { |fid|
            f = faces[fid.text]
            ceilface = self.construct_face(f, glazings)
            if ceilface == nil
              next
            end
            _ceiling += ceilface
          }
        }

        spc.each_element('boundary') { |bd_element|
          pts = []
          bd_element.each_element('pt') { |pt|
            pts.push(pt.text.split(" ").map { |dim| dim.to_f })
          }
          for i in 0..pts.length - 2
            _bounds.push([pts[i], pts[i + 1]])
          end
          _bounds.push([pts[-1], pts[0]])
        }
        _height = spc.get_elements('height')[0].text.to_f()
        topology.each_element('edge') { |ed_element|
          _walls = ed_element.get_elements('wall').map { |wl| walls[wl.get_elements('Uid')[0].text] }
          norms = ed_element.get_elements('wall').map { |wl|
            wl.get_elements('normal')[0].text.split(" ").map { |num|
              num.to_f()
            }
          }

          for i in 0.._walls.length - 1
            if _walls[i].get_elements('external')[0].text == "True"
              internal = false
            else
              internal = true
            end
            _normal = norms[i]

            _length = _walls[i].get_elements('length')[0].text.to_f()
            distance = (_bounds[i][0][0] - _bounds[i][1][0]) * (_bounds[i][0][0] - _bounds[i][1][0]) +
              (_bounds[i][0][1] - _bounds[i][1][1]) * (_bounds[i][0][1] - _bounds[i][1][1])
            distance = Math.sqrt(distance)
            _wall = MoosasEdge.new(_bounds[i], _height, require_infer = false)
            _wall.set_len(_length)

            e = construct_face(_walls[i], glazings)
            if e == nil
              next
            end
            _wall.walls = e
            _wall.glazings = e[0].glazings

            g_area = 0.0
            for g in _wall.glazings
              g_area += g.face.area * MoosasConstant::INCH_METER_MULTIPLIER_SQR
            end
            e_area = 0.0
            for e in _wall.walls
              e_area += e.face.area * MoosasConstant::INCH_METER_MULTIPLIER_SQR
            end
            begin
              _wwr = g_area / (distance * _height)
              _wall.area_m = distance * _height
            rescue
              _wwr = g_area / e_area
              _wall.area_m = e_area
            end
            # p "wwr:#{_wwr}",g_area,distance,_height
            _wall.wwr = _wwr
            # _wall.area_m = (g_area+e_area)*MoosasConstant::INCH_METER_MULTIPLIER_SQR
            _wall.is_internal_edge = internal
            for g in _wall.glazings
              g.normal = Geom::Vector3d.new(_normal)
            end
            _wall.normal = Geom::Vector3d.new(_normal)
            _wall.normal.length = 1
            _edge.push(_wall)
          end

        }
        spaces.push(self.construct_space(spc, _floor, _ceiling, _edge))
      end

      # shading_elements=root.get_elements('shading')[0].get_elements('face')
      # shading_elements.each{|sd_element|
      #     moface=self.find_geometry(sd_element.text.to_i())
      #     glazing=sd_element.attribute('glazingId').value()
      #     self.find_geometry(glazing).shading.push(moface)
      # }

    end
    return spaces
  end

  def self.find_geometry(idd)
    "" "
    Finds a MoosasFace by its ID.

    Function:
      Searches the stored geometries list to find a MoosasFace matching the given ID.

    Parameters:
      idd (String/Integer): ID of the MoosasFace to find.

    Returns:
      MoosasFace or nil: The matching MoosasFace if found, nil otherwise.
    " ""
    rf = nil
    @geometries.each do |moface|
      if moface.id == idd
        return moface
      end
    end
    return rf
  end

  def self.construct_by_boundary(_element, entities, offset_height = 0)
    "" "
    Constructs a face from boundary points in the model.

    Function:
      Reads boundary points from an XML element, adjusts z-coordinate with offset, creates a face in a group,
      and returns a MoosasFace with world transformation.

    Parameters:
      _element (REXML::Element): XML element containing boundary points.
      entities (Sketchup::Entities): Entities container to create the face in.
      offset_height (Float, optional): Z-axis offset for the face. Defaults to 0.

    Returns:
      MoosasFace: The constructed face with calculated height and transformation.
    " ""
    pts = []
    _element.each_element('pt') { |pt|
      pts.push(pt.text.split(" "))
    }
    for i in 0..pts.length - 1
      pts[i] = [pts[i][0].to_f(), pts[i][1].to_f(), pts[i][2].to_f() + offset_height]
    end
    group = entities.add_group
    entities2 = group.entities
    e = entities2.add_face(pts)
    transformation = self.get_world_transformation(e)
    fl = MoosasFace.new(e, transformation, e.area, e.normal, generate_plane_id())
    fl.calculate_height
    return fl
  end

  def self.construct_face(_element, glazings)
    "" "
    Constructs a MoosasFace from XML element data and glazing mappings.

    Function:
      Retrieves face IDs, glazing IDs, and height from XML, finds corresponding geometries,
      attaches glazing data to the face, and returns the face list.

    Parameters:
      _element (REXML::Element): XML element containing face data.
      glazings (Hash): Hash mapping glazing UIDs to their XML elements.

    Returns:
      Array[MoosasFace] or nil: List of constructed MoosasFace objects, nil if face is not found.
    " ""
    _height = _element.get_elements('height')[0].text.to_f
    _id = _element.get_elements('faceId')[0].text.split(" ")
    _uid = _element.get_elements('Uid')[0].text
    _face = _id.map { |g| self.find_geometry(g) }
    if _face[0] == nil
      p _id
      return nil
    end
    fl_glazing = []
    _glazing = _element.get_elements('glazingId')[0].text
    if _glazing == nil
      fl_glazing = []
    else
      _glazing.split(" ") do |glazingUid|
        gls = glazings[glazingUid]
        gls_ids = gls.get_elements('faceId')[0].text.split(" ")
        gls_ids.each do |g|
          g_moface = self.find_geometry(g)
          g_moface.uid = glazingUid
          fl_glazing.push(g_moface)
        end
      end
    end
    for f in _face
      f.glazings = fl_glazing
      f.height = _height
      f.uid = _uid
    end
    return _face
  end

  def self.construct_space(_element, _floor, _ceil, _bound)
    "" "
    Constructs a MoosasSpace from floor, ceiling, boundary, and XML data.

    Function:
      Initializes a space with floor/ceiling faces, boundary edges, height, and ID;
      marks space as outer/inner based on boundary walls.

    Parameters:
      _element (REXML::Element): XML element containing space metadata (height, ID, etc.).
      _floor (Array[MoosasFace]): List of floor faces for the space.
      _ceil (Array[MoosasFace]): List of ceiling faces for the space.
      _bound (Array[MoosasEdge]): List of boundary edges for the space.

    Returns:
      MoosasSpace or nil: The constructed space object, nil if required components are missing.
    " ""
    if _floor == [] or _ceil == [] or _bound == []
      p "_floorNil" if _floor == []
      p "_ceilNil" if _ceil == []
      p "_boundNil" if _bound == []
      return nil
    end
    _height = _element.get_elements('height')[0].text.to_f() / MoosasConstant::INCH_METER_MULTIPLIER
    space_id = _element.get_elements('id')[0].text
    neighbor = _element.get_elements('neighbor')
    s = MoosasSpace.new(_floor, _height, _ceil, _bound, id = space_id)
    # s.set_id("s_0x"+space_id)
    s.is_outer = false
    # neighbor.each{|nei| s.neighbor[nei.text]=self.find_geometry(nei.attribute('Faceid').value()).id}
    internal_wall = _element.each_element('internal_wall') { |e|
      if e.text != nil
        e.text.split(' ').each { |w|
          s.internal_wall.append(self.find_geometry(w))
        }
      end
    }

    for wall in _bound
      # s.bounds.push(wall)
      if !wall.is_internal_edge
        s.is_outer = true
      end
    end
    # p "Create Space #{space_id} at the Height #{_floor.height*MMR::INCH_METER_MULTIPLIER}m"
    return s
  end

  def self.generate_plane_id()
    "" "
    Generates a unique ID for a plane/face.

    Function:
      Creates a random 8-character alphanumeric code prefixed with p_0x for unique identification.

    Parameters:
      None

    Returns:
      String: Unique plane ID (e.g., p_0xa3f2d4e5).
    " ""

    code = [*'a'..'f', *'0'..'9'].sample(8).join
    # return "p_"+rand(10000).to_s+"_"+Time.now.to_f.to_s
    return "p_0x" + code
  end

  def self.user_visible?(e)
    "" "
    Checks if an entity is visible to the user.

    Function:
      Verifies if the entity itself and its parent layer are both visible in the SketchUp model.

    Parameters:
      e (Sketchup::Entity): The entity to check (face, group, etc.).

    Returns:
      bool: True if the entity is visible, False otherwise.
    " ""
    e.visible? && e.layer.visible?
  end

  def self.traverse_faces(entity, path = [], &func)
    "" "
    Recursively traverses entities to find all faces.

    Function:
      Iterates through groups, components, entities collections, and selections to find faces;
      executes a callback function with each face and its parent path.

    Parameters:
      entity (Sketchup::Entity/Enumerable): Entity to traverse (face, group, entities, etc.).
      path (Array[Sketchup::Group/ComponentInstance], optional): Parent path of the current entity. Defaults to empty array.
      &func (Proc): Callback function to execute for each face (accepts 1 or 2 arguments: face, path).

    Returns:
      None
    " ""
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

  # find the transformation of a existing face
  def self.get_world_transformation(entity)
    "" "
    Calculates the world transformation matrix for an entity.

    Function:
      Traverses the entity's parent hierarchy (groups/components), collects transformation matrices,
      and computes the total transformation from local to world coordinates.

    Parameters:
      entity (Sketchup::Entity): The entity to compute the transformation for (face, edge, etc.).

    Returns:
      Geom::Transformation: Total transformation matrix from local to world coordinates.
    " ""
    # 收集实体所在的层级路径（从实体的直接父到顶层容器）
    path = []
    current = entity.parent

    # 遍历父容器，收集组或组件实例（与traverse_faces的path逻辑对应）
    while current.is_a?(Sketchup::Group) || current.is_a?(Sketchup::ComponentInstance)
      path << current # 路径按“直接父 -> 祖父 -> ... -> 顶层”顺序存储
      current = current.parent
    end

    # 计算总变换矩阵：路径中所有容器的变换依次相乘（从顶层到直接父）
    # 注：path的顺序是“直接父在前、顶层在后”，因此需要reverse后再计算
    return path.reverse.inject(IDENTITY_TRANSFORMATION) { |total, container| total * container.transformation }
  end

  def self.show_space_info(space)
    "" "
    Adds text labels to the model showing space and face details.

    Function:
      Creates text entities at face centroids displaying space ID, face ID, area, material, WWR, and radiation data.

    Parameters:
      space (MoosasSpace): The space to display information for.

    Returns:
      None
    " ""
    model = Sketchup.active_model
    entities = model.entities
    space.floor.each { |f|
      t = entities.add_text("#{space.id}_floor\nId:#{f.id}\nArea:#{f.area_m.round(2)}\nMaterial:#{$rad_lib[f.material].category + "_" + $rad_lib[f.material].name}\n", f.centroid)
    }

    space.ceils.each { |f|
      t = entities.add_text("#{space.id}_ceiling\nId:#{f.id}\nArea:#{f.area_m.round(2)}\nMaterial:#{$rad_lib[f.material].category + "_" + $rad_lib[f.material].name}\n", f.centroid)
    }

    for w in space.bounds
      str = "#{space.id}_wall\n"
      position = nil
      for f in w.walls
        # t = entities.add_text("#{space.id}_wall_#{w.wwr}", f.centroid)
        str += "Id:#{f.id}\nArea:#{f.area_m.round(2)}\nMaterial:#{$rad_lib[f.material].category + "_" + $rad_lib[f.material].name}\nWwr:#{w.wwr.round(2)}\n"
        position = f.centroid
        # allentities.add_line(f.centroid,f.centroid+w.normal.to_a())
      end
      for g in w.glazings
        str += "_glazing_Id:#{g.id}\nArea:#{g.area_m.round(2)}\nMaterial:#{$rad_lib[g.material].category + "_" + $rad_lib[g.material].name}\n"
      end
      str += "summer_rad:#{w.settings['summer_rad']}\nwinter_rad:#{w.settings['winter_rad']}\n"
      t = entities.add_text(str, position)
    end
    for w in space.internal_wall
      t = entities.add_text("#{space.id}_internal_wall_\nId:#{w.id}\nArea:%.2f" % w.area_m, w.centroid)
    end
  end

  def self.select_space_walls(i)
    "" "
    Highlights walls of a specific space by hiding other faces.

    Function:
      Hides all faces except those belonging to the specified space, and deletes existing text labels.

    Parameters:
      i (Integer): Index of the target space in the @spaces list.

    Returns:
      String: ID of the selected space.
    " ""
    model = Sketchup.active_model
    entities = model.active_entities
    texts = entities.grep(Sketchup::Text)
    entities.erase_entities(texts)
    model.start_operation("select_space_walls #{i}", true)

    '' '
        j = 0
        while j < @spaces.length
            if i != j
                s = @spaces[j]
                s.walls.each do |w|
                    w.face.hidden = true
                end
                s.ceils.each do |w|
                    w.face.hidden = true
                end
            end
            j += 1
        end
        ' ''

    self.hide_all_face()
    s = @spaces[i]
    mofaces = s.get_all_face
    mofaces.each { |mf| mf.face.hidden = false }
    s.floor.each { |f| p f.area_m }
    # p 'space'
    # p s.area_m
    # show_space_info(s)

    model.commit_operation
    return s.id
  end

  def self.show_all_face
    "" "
    Shows all hidden faces in the model.

    Function:
      Traverses all model entities, unhides all faces, and deletes existing text labels.

    Parameters:
      None

    Returns:
      None
    " ""
    Sketchup.active_model.start_operation("显示所有的面", true)
    model = Sketchup.active_model
    entities = model.active_entities
    texts = entities.grep(Sketchup::Text)
    entities.erase_entities(texts)
    self.traverse_faces(Sketchup.active_model.entities) do |e, path|
      e.hidden = false
    end
    Sketchup.active_model.commit_operation
  end

  def self.hide_all_face
    "" "
    Hides all faces in the model.

    Function:
      Traverses all model entities and hides all faces.

    Parameters:
      None

    Returns:
      None
    " ""
    Sketchup.active_model.start_operation("隐藏所有的面", true)
    self.traverse_faces(Sketchup.active_model.entities) do |e, path|
      e.hidden = true
    end
    Sketchup.active_model.commit_operation
  end

  def self.visualize_factor()
    "" "
    Visualizes factor data for space boundaries.

    Function:
      Creates a group and adds visualization elements for boundary factors (e.g., radiation) of all spaces.

    Parameters:
      None

    Returns:
      None
    " ""
    group = Sketchup.active_model.active_entities.add_group
    entities = group.entities
    $current_model.spaces.each { |space|
      space.bounds.each { |b|
        entities = b.visualize_factor(entities)
      }
    }
  end

  def self.simplified(pts, offset)
    "" "
    Simplifies a list of vertices by removing duplicate points.

    Function:
      Applies a z-axis offset, removes vertices that form zero-length edges, and converts vectors back to arrays.

    Parameters:
      pts (Array[Array[Float]]): List of vertices (x, y, z) to simplify.
      offset (Float): Z-axis offset to apply to all vertices.

    Returns:
      Array[Array[Float]]: Simplified list of vertices.
    " ""
    pts = pts.map { |pt| Geom::Vector3d.new([pt[0], pt[1], pt[2] + offset]) }
    # pts.unshift(pts[-1])
    # pts.push(pts[0])

    pts_temp = pts
    pts = []
    for i in 0..pts_temp.length - 1
      edge1 = pts_temp[i] - pts_temp[i - 1]
      unless edge1.length == 0
        pts.push(pts_temp[i])
      end
    end
    pts_new = pts
    # pts_new = []
    # for i in 1..pts.length-2
    #     pts_new.push(pts[i])
    #     # edge1 = pts[i]-pts[i-1]
    #     # edge2 = pts[i+1]-pts[i]
    #     # edge1.length = 1
    #     # edge2.length = 1
    #     # dot =edge1.dot(edge2)
    #     # unless dot >= 0.999 or dot <=-0.999
    #     #     pts_new.push(pts[i])
    #     # end
    # end

    pts_new = pts_new.map { |pt| pt.to_a }
    return pts_new
  end

  def self.draw_coplanar_face(entities, pts, normal)
    "" "
    Draws a coplanar face by projecting vertices to a target plane (corrects minor errors).

    Function:
      Normalizes the input normal, calculates the target plane equation, projects all vertices to the plane,
      creates a face, and ensures the face normal matches the input.

    Parameters:
      entities (Sketchup::Entities): Entities container to create the face in.
      pts (Array[Geom::Point3d/Array[Float]]): List of vertices (may have coplanarity errors).
      normal (Geom::Vector3d/Array[Float]): Target normal vector for the coplanar face.

    Returns:
      Sketchup::Face or nil: The created coplanar face, nil if input is invalid.
    " ""
    # 输入验证
    return nil unless entities.is_a?(Sketchup::Entities)
    return nil if pts.size < 3 # 至少需要3个点才能创建面
    return nil if normal.length == 0 # 法向量不能为零向量

    # 规范化法向量（确保方向一致，不影响长度）
    normal = normal.normalize

    # 以第一个点为基准点，计算平面方程：ax + by + cz + d = 0
    p0 = pts.first
    a = normal.x
    b = normal.y
    c = normal.z
    d = -(a * p0.x + b * p0.y + c * p0.z) # 确保p0在平面上

    # 计算平面法向量的模长平方（用于投影计算）
    norm_sq = a ** 2 + b ** 2 + c ** 2

    # 将所有点投影到目标平面上（消除共面误差）
    projected_pts = pts.map do |pt|
      # 计算点到平面的距离参数 t
      t = (a * pt.x + b * pt.y + c * pt.z + d) / norm_sq
      # 沿法向量反方向投影到平面上
      x = pt.x - a * t
      y = pt.y - b * t
      z = pt.z - c * t
      Geom::Point3d.new(x, y, z)
    end

    # 在容器中创建面（使用投影后的共面点）
    face = entities.add_face(projected_pts)

    # 确保面的法向量与输入一致（若方向相反则反转面）
    if face.normal.dot(normal) < 0
      face.reverse!
    end

    return face
  end

  def self.add_2d_face(entities, pts, normal)
    "" "
    Creates a 2D face by rotating vertices to align with a target normal.

    Function:
      Calculates center and axes from vertices and normal, rotates vertices to 2D (z=0), creates a face,
      applies inverse rotation, and explodes the temporary group to get the final face.

    Parameters:
      entities (Sketchup::Entities): Entities container to create the face in.
      pts (Array[Array[Float]]): List of 3D vertices to convert to 2D.
      normal (Geom::Vector3d/Array[Float]): Target normal vector for the 2D face.

    Returns:
      Sketchup::Face or nil: The created 2D-aligned face, nil if creation fails.
    " ""
    center = [0, 0, 0]
    pts.each do |pt|
      center[0] += pt[0]
      center[1] += pt[1]
      center[2] += pt[2]
    end
    center = center.map { |c| c / pts.length }
    axisZ = Geom::Vector3d.new(normal)
    axisX = Geom::Vector3d.new(pts[0]) - Geom::Vector3d.new(center)
    axisY = normal.cross(axisX)
    axisX.length = 1
    axisY.length = 1
    axisZ.length = 1
    rotateMatrix = (Matrix[axisX.to_a, axisY.to_a, axisZ.to_a]).transpose
    pts_new = pts.map { |pt| [pt[0] - center[0], pt[1] - center[1], pt[2] - center[2]] }
    pts_new = pts_new.map { |pt| (Matrix[pt] * rotateMatrix).to_a[0] }
    pts_new = pts_new.map { |pt| [pt[0], pt[1], 0] }

    e = entities.add_face(pts_new)

    # using a new group for transformation
    temp_group = entities.add_group(e)
    transformation = Geom::Transformation.new(Geom::Point3d.new(center), axisX, axisY)
    temp_group.transform! transformation
    temp_group.explode
    exploded_entities = temp_group.explode
    # 从爆炸后的实体中筛选出新的面（原面的副本）
    e = exploded_entities.grep(Sketchup::Face).first

    return e
  end

end
