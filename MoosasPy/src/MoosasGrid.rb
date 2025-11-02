class MoosasGrid
  Ver = '0.6.3'

  class << self
    attr_reader :color_setting
  end

  # 传入参数params=[网格大小，网格距离平面距离，网格边沿缩进值]
  def self.fit_grids(params = [1.0, 0.1, 0.01])
    # Function:
    # Generates adaptive grids on selected faces in a SketchUp model based on user-defined parameters.
    # If no faces are selected, prompts the user to select faces. Otherwise, prompts for grid parameters
    # (grid size and offset/reference height) via a dialog box, then creates and returns the generated grid entities.
    # 
    # Parameters:
    # params : Array<Float>, optional
    # An array containing default grid parameters.
    # - params[0] : Float, default 1.0 - Grid cell size.
    # - params[1] : Float, default 0.1 - Offset or reference height for grid placement.
    # - params[2] : Float, default 0.01 - Additional parameter (currently unused in logic).
    # These values may be overridden by user input from the dialog box.
    # 
    # Returns:
    # Array<Sketchup::DrawingElement> or nil
    # Returns an array of successfully created and non-deleted grid entities (edges or other geometry).
    # If no faces are selected, displays an error message and returns nil.
    # If grid creation fails due to invalid parameters (e.g., inappropriate grid size),
    # error messages are shown, but only successfully created entities up to that point are returned.
    model = Sketchup.active_model
    entities = model.active_entities
    selection = []
    MMR.traverse_faces(model.selection) { |e, path| selection.push(e) }
    # Filter faces
    faces = selection.to_a.select { |ent| ent.is_a? Sketchup::Face }

    if faces.empty?
      if $language == 'Chinese'
        UI.messagebox("请选择分析的面！")
      else
        UI.messagebox("Please select a face")
      end
      return nil
    else
      if $language == 'Chinese'
        prompts = ["网格大小：", "网格偏移距离："]
        defaults = ["1.0", "0.1"]
        input = UI.inputbox(prompts, defaults, "请输入网格参数！")
      else
        prompts = ["Gird size:", "Reference height:"]
        defaults = ["1.0", "0.1"]
        input = UI.inputbox(prompts, defaults, "Please enter required gridding parameters")
      end
      params[0] = input[0].to_f()
      params[1] = input[1].to_f()
      grid = self.fit_selection(model, entities, faces, params)
      grid_output = []
      grid.each { |ent|
        if not ent.deleted?
          grid_output << ent
        else
          UI.messagebox("**Error: Fail to create Grids because of the inappropriated grid size.")
          p "**Error: Fail to create Grids because of the inappropriated grid size."
        end
      }
      return grid_output
    end
  end

  # 为选中的面生成自适应的网格
  def self.fit_selection(model, entities, faces, params, auto_mode = false, ts = nil)
    # """
    # Function
    # --------
    # fit_selection : class method
    # Fits grid patterns to selected faces in a SketchUp model, distinguishing between curved surfaces and planar face groups.
    # For curved surfaces, grids are fitted per surface; for planar faces, co-planar groups are identified and each group is fitted with a single grid.
    # The method handles both isolated flat faces and those belonging to larger surfaces, applies transformations as needed, and manages model operations safely.
    # 
    # Parameters
    # ----------
    # model : Sketchup::Model
    # The SketchUp model in which the operation is performed. Used to manage transactions (start/commit/abort operations) and access model state.
    # 
    # entities : Sketchup::Entities
    # The entities collection where new geometry (grids) will be created. Typically belongs to the active context within the model.
    # 
    # faces : Array<Sketchup::Face>
    # An array of face objects selected for grid fitting. Modified in place during processing as faces are grouped and removed from consideration.
    # 
    # params : Hash
    # A dictionary containing user-defined parameters or settings used during grid creation (e.g., spacing, alignment, projection behavior).
    # 
    # auto_mode : bool, optional, default=False
    # If True, enables automated behavior during grid fitting (e.g., automatic parameter selection). Influences how `fit_grid_params` behaves.
    # 
    # ts : Sketchup::Transformation, optional, default=None
    # An optional transformation applied during the fitting process. May be used to align coordinate systems or apply offsets.
    # 
    # Returns
    # -------
    # Array<Sketchup::Group or Sketchup::ComponentInstance>
    # A list of newly created grid elements (typically groups or components) that have been fitted to the input faces.
    # These represent the generated grid geometry and can be selected or manipulated afterward.
    # """
    model.start_operation("生成网格", true)
    begin
      # Stored so that they can be selected afterwards
      grids = []
      ### Find curved surfaces, fit them, and note the remaining faces
      flatFaces = []
      # Go through all the faces in the selection
      while faces.length > 0
        face = faces.pop
        surface = self.get_surface(face)
        if surface.empty?
          # If this face is isolated, i.e. not part of a surface, note it as flat
          flatFaces << face
        else
          # Otherwise, remove all the faces from the array of the faces to be fitted
          i = 0
          while i < faces.length
            if surface.key?(faces[i])
              faces[i, 1] = []
            else
              i += 1
            end
          end
          # Then fit a grid to the surface
          grids << self.fit_grid_params(surface.keys, model, entities, params, true, auto_mode, ts)
        end
      end
      faces = flatFaces
      ### Find groups of faces in the same plane and fit them each with a single grid
      # Iterate through all faces
      while faces.length > 0
        # Take a single face and put it in an array, which will be all the faces in that plane
        face = faces.pop
        plane = face.plane
        facesToFit = [face]
        # Find all faces in the same plane
        i = 0
        while i < faces.length
          # if faces[i].plane ~= plane
          if (0...4).collect { |j| (faces[i].plane[j] - plane[j]).abs < 1e-10 }.all?
            facesToFit << faces[i]
            faces[i, 1] = []
          else
            i += 1
          end
        end
        # Fit the array of faces
        grids << self.fit_grid_params(facesToFit, model, entities, params, false, auto_mode, ts)
      end
      # Select all fitted grids
      # Sketchup.send_action "selectSelectionTool:"
      # model.selection.clear
      # model.selection.add(grids)
      # 初始化整个模型的网格参数设置
      self.get_initialised_model_dict()
    rescue Exception => e
      model.abort_operation
      if $language == 'Chinese'
        UI.messagebox("生成网格失败！")
      else
        UI.messagebox("Failed to create the gird.")
      end
      MoosasUtils.rescue_log(e)
    end
    model.commit_operation
    return grids
  end

  # Called (possibly repeatedly) by fit_selection
  # Takes an array of faces, either all in one plane or forming a surface (hopefully) and fits a single grid to them, which it returns.
  # facesToFit is the array of faces
  # params contains the user settings
  # How it works: rotate a copy of the faces so that they're parallel to the XY plane
  # Create a grid of nodes by iterating linearly over x and y within the bounding rectangle of the faces, with constant z
  # Leave out nodes that aren't within any of the faces
  # Draw rectangular faces  throughout the grid where all four corner nodes are present
  # Apply the inverse rotation to the grid
  # For curved surfaces, there are two main differences:
  # The nodes are projected onto the surface
  # The faces in the grid are triangles, since four corners might not be planar
  def self.fit_grid_params(facesToFit, model, entities, params, is_surface, auto_mode = false, ts = nil)
    # Function
    # --------
    # Generates a grid fitted to specified faces or surfaces in a SketchUp model, with configurable parameters for spacing, height, and orientation.
    # The method handles both planar faces and curved surfaces, applying transformations to align the grid appropriately and projecting nodes
    # onto the target geometry. It supports automatic mode with additional transformation.
    # 
    # Parameters
    # ----------
    # facesToFit : Array<Sketchup::Face>
    # An array of SketchUp Face objects to which the grid will be fitted.
    # model : Sketchup::Model
    # The SketchUp model containing the geometry, used for ray testing and bounds calculation.
    # entities : Sketchup::Entities
    # The entities collection where new groups and geometry will be added.
    # params : Array<Numeric>
    # An array of three numeric parameters:
    # - params[0]: Desired width (in meters) between grid cells.
    # - params[1]: Height (in meters) by which to raise the final grid.
    # - params[2]: Offset distance (in meters) applied to faces before fitting (treated as 0.01m if zero).
    # is_surface : Boolean
    # If true, treats the input faces as part of a curved surface; uses raycasting to project grid nodes onto the surface.
    # If false, assumes planar faces and performs offsetting and classification in 2D after rotation.
    # auto_mode : Boolean, optional, default=False
    # If true, applies an additional transformation (`ts`) to the generated grid nodes before returning.
    # ts : Geom::Transformation, optional
    # A transformation matrix applied to the grid nodes when `auto_mode` is enabled.
    # 
    # Returns
    # -------
    # Sketchup::Group
    # A group object containing the generated grid faces. The group carries attribute metadata including:
    # - "nodes": 2D array of grid node positions (or `false` for invalid positions).
    # - "is_surface": Boolean indicating whether the grid was fitted to a surface.
    # - "norm": The unit normal vector of the fitted faces as a triplet [x, y, z].
    # - "stamp": A unique identifier (time + random number) linking the grid to its source faces for potential refitting.
    stamp = [Time.now, rand]
    # facesToFit.each{ |f| f.set_attribute("grid_fit_properties", "stamp", stamp) }

    # Calculating a translation that will used soon, before making groups
    bb = model.bounds
    minDist = [bb.max.x, bb.min.x, bb.max.y, bb.min.y, bb.max.z, bb.min.z].collect { |n| n.abs.ceil }.min
    safeDistance = 10000.m
    if bb.max.x.abs.ceil == minDist
      point = [bb.max.x + safeDistance, 0, 0]
    elsif bb.min.x.abs.ceil == minDist
      point = [bb.min.x - safeDistance, 0, 0]
    elsif bb.max.y.abs.ceil == minDist
      point = [0, 0, bb.max.y + safeDistance]
    elsif bb.min.y.abs.ceil == minDist
      point = [0, 0, bb.min.y - safeDistance]
    elsif bb.max.z.abs.ceil == minDist
      point = [0, bb.max.z + safeDistance, 0]
    elsif bb.min.z.abs.ceil == minDist
      point = [0, bb.min.z - safeDistance, 0]
    end
    point -= CustomBounds.new(facesToFit).center
    safetyMove = Geom::Transformation.translation(point)

    #### Making a copy of the faces (that is offset if appropriate) being fitted as a group
    offsetDist = params[2].m
    offsetDist = 0.01.m if offsetDist == 0

    # Create an array of groups called 'groups', where each group is actually a single face (this helps to avoid intersection problems)
    groupsOriginal = facesToFit.collect { |f| entities.add_group([f]) }
    groups = groupsOriginal.collect { |g| g.copy }
    groupsOriginal.each { |g| g.explode }

    # Prevent interference with the original faces by moving them far away
    entities.transform_entities(safetyMove, groups)

    # Reset facesToFit to be an array containing the new copied faces.
    # All the groups are placed inside a bigger group so because the faces might intersect after offsetting,
    # which causes deletions. This way they can be found again using entities

    # Offset each face if this is not part of a curved surface. This has to be done carefully.
    # In particular, if two faces to be fit are joined, erase the edge between them before offsetting
    if not is_surface

      faceGroup = entities.add_group(groups)
      groups.each { |g|
        g.explode
      }
      facesToFit = faceGroup.entities.to_a.select { |ent| ent.is_a? Sketchup::Face }

      edgesToErase = []

      faceGroup.entities.each { |ent|
        if ent.is_a? Sketchup::Edge
          connectedFaces = ent.faces
          edgesToErase << ent if connectedFaces.length > 1 and connectedFaces.collect { |f| facesToFit.include?(f) }.all?
        end
      }

      if not edgesToErase.empty?
        faceGroup.entities.erase_entities(edgesToErase)
      end

      groups = []
      facesToFit = faceGroup.explode.grep(Sketchup::Face)

      for face in facesToFit
        singleFaceGroup = entities.add_group([face])
        faces = singleFaceGroup.entities.to_a.select { |e| e.is_a? Sketchup::Face }
        raise "在偏移前发现一个群组包含多个面" if faces.length > 1
        face = faces[0]
        offsetFace = self.offset_face(face, -offsetDist)
        toErase = singleFaceGroup.entities.to_a.select { |e| not (e == offsetFace or offsetFace.edges.include? e) }
        singleFaceGroup.entities.erase_entities(toErase)
        groups << singleFaceGroup
      end
    end

    faceGroup = entities.add_group(groups)
    groups.each { |g|
      g.explode
    }
    facesToFit = faceGroup.explode.grep(Sketchup::Face)

    #### Rotating

    # Obtain the unit normal of the faces. For surfaces, this is the average normal of the component faces
    norm = Geom::Vector3d.new
    for face in facesToFit
      norm += face.normal
      break if not is_surface
    end

    begin
      norm.length = 1
    rescue
      norm = Geom::Vector3d.new(0, 0, 1)
    end

    # Make sure the normal is pointing upwards. 0 is not used to avoid precision errors for vertical faces
    # norm.reverse! if norm.z < -0.001

    # To rotate the faces so that they lie horizontally, imagine that the face was once horizontal (the normal being (0,0,1))
    # and then was rotated into its current orientation by two rotations: one rotation around the y-axis, then one about the x-axis.
    # If you multiply the two rotation matrices by the column vector (0,0,1) you get the current normal vector of the faces.
    # Solving for the angles of rotation gives the below. Since the normal is pointing upwards, the angles must be in the range of asin: [-90, 90] (degrees)
    yangle = Math.asin(norm.x)
    sin = [[-norm.y / Math.cos(yangle), -1].max, 1].min # Dealing with an issue of floating point precision and the domain of asin
    xangle = Math.asin(sin)

    # Create the full rotation transformation and apply it
    cent = CustomBounds.new(facesToFit).center
    y_rotation = Geom::Transformation.rotation(cent, Y_AXIS, yangle)
    x_rotation = Geom::Transformation.rotation(cent, X_AXIS, xangle)
    rotation = x_rotation * y_rotation # this is the rotation that turns the unit z vector into the faces' upward unit normal
    entities.transform_entities(rotation.inverse, facesToFit) # the faces should now be horizontal (for non-surfaces)

    ## Find information about the bounds and size of the array
    bbox = CustomBounds.new(facesToFit)
    width = bbox.maxx - bbox.minx
    height = bbox.maxy - bbox.miny

    if is_surface

      # Since the grid is projected onto the surface, we create the grid directly below it
      zpos = bbox.minz - 10

    else

      # We want a constant z. All the nodes should already have this, but this is what is used in case of precision errors, e.g. if the rotation was imperfect
      zpos = (bbox.minz + bbox.maxz) / 2.0
    end

    # Calculate number of cells on shorter side of grid (and extract the user settings)
    # The idea is to make the cells as close to squares as possible by making the proportions of the grid
    # in terms of number of cells approximately the same as the proportions of what's being fitted
    # nx and ny are the number of cells in the x and y direction

    desiredWidth = params[0].m
    if width > height
      nx = (width / desiredWidth).round
      ny = (height / width * nx).round
    else
      ny = (height / desiredWidth).round
      nx = (width / height * ny).round
    end
    raiseHeight = params[1].m

    # Sidelengths of cells
    cellWidth = width / nx
    cellHeight = height / ny

    #### Populate grid with nodes. Set a node to false if it is not on the face

    # This is a 2D array: each element is an array representing a row of the nodes in the grid, i.e. a horizontal line, with y constant
    nodes = []

    # Iterate through all possible nodes
    for y in 0..ny
      row = []
      for x in 0..nx

        # Position of the node in (x,y,z) coordinates: used as a Point3d
        pt = [bbox.minx + x * cellWidth, bbox.miny + y * cellHeight, zpos]

        # Boolean asking whether the node is valid, i.e. is it within any of the faces
        ptOnGroup = false

        # Testing if the node is valid, and projecting for surfaces
        if is_surface

          # Draw a ray from the node's current position below the grid directly upwards
          # If the ray intersects with anything, move the node to the point of intersection
          # Test if it's on the desired surface. Raytests can return either Faces or Edges: this is dealt with
          # If it's not, redo the raytest from the new position
          # The loop ends when either the ray no longer hits anything or it hits the surface. ptOnGroup is set appropriately
          while true
            item = model.raytest([pt, Z_AXIS])
            break if not item
            pt, ent = item
            ent = ent[0]
            if ent.is_a? Sketchup::Face and facesToFit.include?(ent)
              ptOnGroup = true
              break
            elsif ent.is_a? Sketchup::Edge
              for f in ent.faces
                if facesToFit.include?(f)
                  ptOnGroup = true
                  break
                end
              end
              break if ptOnGroup
            end
          end
        else

          # Classifying nodes (valid or not) for non-surfaces
          facesToFit.collect { |face|
            case face.classify_point(pt)
            when Sketchup::Face::PointInside, Sketchup::Face::PointOnVertex, Sketchup::Face::PointOnEdge
              ptOnGroup = true
              break
            when Sketchup::Face::PointOutside
              next
            when Sketchup::Face::PointUnkown
              puts "错误: 无法分类点"
            when Sketchup::Face::PointNotOnPlane

              # This implies that the rotation didn't make the face properly horizontal and is a serious problem
              # Fortunately this hasn't been encountered :P ...yet
              puts "错误: 点不在平面上"
            else
              puts "未知点分类错误"
            end
          }
        end
        pt = false if not ptOnGroup
        # Every element of the nodes array is therefore either a 'false' indicating invalidity, or a position
        row << pt
      end
      nodes << row
    end

    # Rotate the grid (the nodes) back to the original orientation
    nodes.each { |row| row.each { |node| node.transform!(rotation) if node } }

    # Delete the copy of the faces fitted
    faceGroup = entities.add_group(facesToFit)
    entities.erase_entities([faceGroup])

    # Move the grid by the raiseHeight amount provided by the user in the appropriate direction
    moveVector = norm.clone
    moveVector.length = raiseHeight.abs
    moveVector.reverse! if (moveVector.z * raiseHeight < 0) # the '*' tests if these have different signs
    translation = Geom::Transformation.translation(moveVector)
    translation *= safetyMove.inverse # bring the grid back to where the faces were, undoing the safety move
    nodes.each { |row| row.each { |node| node.transform!(translation) if node } }
    if auto_mode
      nodes.each { |row| row.each { |node| node.transform!(ts) if node } }
    end

    #### Add faces
    grid = entities.add_group

    for y in 0...ny
      for x in 0...nx

        # For surfaces, each cell is a pair of triangles
        if is_surface
          pts = [nodes[y][x], nodes[y + 1][x], nodes[y + 1][x + 1]]

          # A face is only fitted if all its corner nodes are valid
          if pts.all?
            grid.entities.add_face(pts)
          end
          pts = [nodes[y][x], nodes[y][x + 1], nodes[y + 1][x + 1]]

          if pts.all?
            grid.entities.add_face(pts)
          end
        else
          pts = [nodes[y][x], nodes[y + 1][x], nodes[y + 1][x + 1], nodes[y][x + 1]]
          if pts.all?
            grid.entities.add_face(pts)
          end
        end
      end
    end

    # Identify the grid as a grid and store important information about it
    grid.set_attribute("grid", "nodes", nodes)
    grid.set_attribute("grid", "is_surface", is_surface)
    grid.set_attribute("grid", "norm", norm.to_a)

    # Stamp to identify this grid with the faces it was fitted to for refitting purposes
    grid.set_attribute("grid", "stamp", stamp)

    return grid
  end

  def self.fit_grids_for_horizational_face(entities, faces, transformations, params, rendered = true)
    # Function:
    # Fits grids to horizontal faces in a SketchUp model based on specified parameters. For each face, a grid is generated with nodes projected onto the face plane and optionally raised by a given height. The resulting grids are grouped and added to the model, with options to render them as faces. Selected grids are highlighted in the UI, and metadata about the grid nodes is stored.
    # 
    # Parameters:
    # entities : Sketchup::Entities
    # The entities collection to which the grid groups will be added.
    # faces : Array<Sketchup::Face>
    # An array of face objects to fit grids onto. These should be approximately horizontal.
    # transformations : Array<Geom::Transformation>
    # An array of transformation matrices applied to the grid points after projection onto the face planes.
    # params : Array<Float>
    # A two-element array where:
    # - params[0] (Float): Desired cell width in inches, converted to model units.
    # - params[1] (Float): Height by which to raise the grid above the face (in inches).
    # rendered : Boolean, optional
    # If true (default), creates planar faces within the grid group to visualize the cells.
    # 
    # Returns:
    # Array<Sketchup::Group>
    # An array of SketchUp group objects, each representing a fitted grid. Each group contains:
    # - Stored attribute "nodes" containing the 2D array of grid node positions (or false for invalid points).
    # - Attribute "is_surface" set to false.
    # Additionally, all generated grids are selected in the active model upon completion.

    grids = []
    fn = faces.length
    for i in 0...fn
      face = faces[i]
      transformation = transformations[i]

      bs = face.bounds
      p_min = bs.min
      p_max = bs.max
      zpos = p_min.z

      minx = p_min.x
      miny = p_min.y
      maxx = p_max.x
      maxy = p_max.y

      plane = face.plane

      bias = 0.01 / 0.0254

      width = maxx - minx - bias * 2
      height = maxy - miny - bias * 2

      # p "width=#{width},height=#{height}"

      desiredWidth = params[0] / 0.0254
      if width > height
        nx = (width / desiredWidth).round
        ny = (height / width * nx).round
      else
        ny = (height / desiredWidth).round
        nx = (width / height * ny).round
      end
      raiseHeight = params[1] / 0.0254

      # p "desiredWidth=#{desiredWidth},raiseHeight=#{raiseHeight}"

      # p "nx=#{nx},ny=#{ny}"

      # Sidelengths of cells
      cellWidth = width / nx
      cellHeight = height / ny

      minx += bias
      miny += bias

      nodes = []
      # Iterate through all possible nodes
      for y in 0..ny
        row = []
        for x in 0..nx
          # Position of the node in (x,y,z) coordinates: used as a Point3d
          pt = [minx + x * cellWidth, miny + y * cellHeight, zpos]
          pt = pt.project_to_plane(plane)

          ptOnFace = false
          case face.classify_point(pt)
          when Sketchup::Face::PointInside
            ptOnFace = true
          else
          end
          # Every element of the nodes array is therefore either a 'false' indicating invalidity, or a position

          if not ptOnFace
            pt = false
          else
            pt[2] += raiseHeight
            pt.transform! transformation
          end
          # p pt
          row << pt
        end
        nodes << row
      end

      grid = entities.add_group

      # 是否绘制面
      if rendered == true
        for y in 0...ny
          for x in 0...nx
            pts = [nodes[y][x], nodes[y + 1][x], nodes[y + 1][x + 1], nodes[y][x + 1]]
            if pts.all?
              grid.entities.add_face(pts)
            end
          end
        end
      end

      # Identify the grid as a grid and store important information about it
      grid.set_attribute("grid", "nodes", nodes)
      grid.set_attribute("grid", "is_surface", false)

      grids.push grid
    end

    model = Sketchup.active_model

    selection = model.selection
    # Select all fitted grids
    Sketchup.send_action "selectSelectionTool:"
    model.selection.clear
    model.selection.add(grids)

    self.get_initialised_model_dict()

    return grids
  end

  # Thanks to thomthom from the Sketchucation forums for this function.
  # Returns the surface containing the given face by finding all faces connected (including indirectly) by soft edges
  def self.get_surface(face)
    # Function:
    # Traverse all faces connected by soft edges starting from a given face and return a collection of visited faces.
    # 
    # Parameters:
    # face : Sketchup::Face
    # The initial face from which the traversal begins. Only faces connected via soft edges will be included in the result.
    # 
    # Returns:
    # Hash
    # A hash where each key is a unique face object reachable through soft edges, and the corresponding value is the face itself. This structure ensures fast lookup and avoids duplication.
    surface = {} # Use hash for speedy lookup
    stack = [face]
    until stack.empty?
      face = stack.shift
      edges = face.edges.select { |e| e.soft? }
      for edge in edges
        for face in edge.faces
          next if surface.key?(face)
          stack << face
          surface[face] = face
        end
      end
    end
    return surface
  end

  # 缩放墙体边缘
  def self.offset_face(face, dist)
    # Function:
    # Offset a given face by a specified distance, creating a new face with vertices shifted outward or inward
    # based on the original face geometry. The method computes offset points for each vertex using vector math,
    # handles edge cases such as parallel edges, removes duplicate points, and creates a new face if possible.
    # 
    # Parameters:
    # face : Sketchup::Face
    # The face to be offset. Must be a valid Sketchup face entity.
    # dist : Fixnum, Float, or Length
    # The distance by which to offset the face. Positive values offset outward, negative values inward.
    # A value of zero or invalid type will result in no offset and return nil.
    # 
    # Returns:
    # Sketchup::Face or nil
    # Returns a new face created from the offset points if successful and more than two unique points exist.
    # Returns nil if the input is invalid, no valid offset can be computed, or fewer than three points remain
    # after deduplication.
    begin
      pi = Math::PI
      if (not ((dist.class == Fixnum || dist.class == Float || dist.class == Length) && dist != 0))
        return nil
      end
      verts = face.outer_loop.vertices
      pts = []

      # CREATE ARRAY pts OF OFFSET POINTS FROM FACE

      0.upto(verts.length - 1) do |a|
        vec1 = (verts[a].position - verts[a - (verts.length - 1)].position).normalize
        vec2 = (verts[a].position - verts[a - 1].position).normalize
        vec3 = (vec1 + vec2).normalize
        if vec3.valid?
          ang = vec1.angle_between(vec2) / 2
          ang = pi / 2 if vec1.parallel?(vec2)
          vec3.length = dist / Math::sin(ang)
          t = Geom::Transformation.new(vec3)
          if pts.length > 0
            vec4 = pts.last.vector_to(verts[a].position.transform(t))
            if vec4.valid?
              unless (vec2.parallel?(vec4))
                t = Geom::Transformation.new(vec3.reverse)
              end
            end
          end

          pts.push(verts[a].position.transform(t))
        end
      end

      # CHECK FOR DUPLICATE POINTS IN pts ARRAY

      duplicates = []
      pts.each_index do |a|
        pts.each_index do |b|
          next if b == a
          duplicates << b if pts[a] === pts[b]
        end
        break if a == pts.length - 1
      end
      duplicates.reverse.each { |a| pts.delete(pts[a]) }

      # CREATE FACE FROM POINTS IN pts ARRAY

      (pts.length > 2) ? (face.parent.entities.add_face(pts)) : (return nil)

    rescue
      puts "#{face} did not offset: #{pts}"
      raise
    end
  end

  @color_setting = {
    "sunhour" =>
      {
        "colorBasis" => "average",
        "numCols" => 5,
        "colours" => [Sketchup::Color.new(1, 76, 255), Sketchup::Color.new(1, 227, 225), Sketchup::Color.new(61, 255, 1), Sketchup::Color.new(255, 161, 1), Sketchup::Color.new("Red")],
        "maxCol" => Sketchup::Color.new("Red"),
        "maxColVal" => 100.0,
        "minCol" => Sketchup::Color.new(1, 76, 255),
        "minColVal" => 0.0,
        "unit" => "h",
        "suffix_length" => 0
      },
    "radiance" =>
      {
        "colorBasis" => "average",
        "numCols" => 3,
        "colours" => [Sketchup::Color.new("Blue"), Sketchup::Color.new("Red"), Sketchup::Color.new("Yellow")],
        "maxCol" => Sketchup::Color.new("Yellow"),
        "maxColVal" => 100.0,
        "minCol" => Sketchup::Color.new("Blue"),
        "minColVal" => 0.0,
        "unit" => "Wh/m2a",
        "suffix_length" => 0
      },
    "illuminance" =>
      {
        "colorBasis" => "average",
        "numCols" => 3,
        "colours" => [Sketchup::Color.new(75, 104, 160), Sketchup::Color.new(249, 236, 80), Sketchup::Color.new(230, 49, 6)],
        "maxCol" => Sketchup::Color.new(230, 49, 6),
        "maxColVal" => 100.0,
        "minCol" => Sketchup::Color.new(75, 104, 160),
        "minColVal" => 0.0,
        "unit" => "lux",
        "suffix_length" => 0
      }
  }

  # cs = color setting
  def self.color_cells(coords, grid, cs = @color_setting["sunhour"], textents = nil)
    # """
    # Function
    # --------
    # Color cells in a grid based on associated data values and specified color settings.
    # 
    # Given a list of coordinate pairs, this method retrieves the corresponding nodes and data values from a grid structure,
    # computes a representative weight (average, minimum, or maximum) of the cell's vertices, and applies a blended color
    # to the generated face based on a gradient scale. Optionally, it can label the cell with its computed weight.
    # 
    # Parameters
    # ----------
    # coords : Array<Array<Integer>>
    # List of [x, y] coordinate pairs indicating the positions of the cell's corners in the grid.
    # grid : Sketchup::Group or Sketchup::ComponentInstance
    # The grid object containing attribute dictionaries with node geometry and result data.
    # cs : Hash, optional
    # Color settings dictionary with keys:
    # - "colorBasis": string ("average", "minimum", "maximum") defining how to compute cell weight.
    # - "numCols": integer number of color bands in the gradient.
    # - "colours": array of color values (e.g., hex strings or Sketchup::Color objects) for gradient.
    # - "maxColVal", "minColVal": float upper and lower value bounds for color mapping.
    # - "maxCol", "minCol": fallback colors if value is outside range (not currently used).
    # Default is @color_setting["sunhour"].
    # textents : Sketchup::Entities, optional
    # Entities collection where text labels will be added. If provided, the computed weight is displayed at the centroid
    # of the face. Default is nil.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It modifies the grid entities by adding a colored face (and optionally a text label)
    # if the cell's vertices are valid.
    # """
    dict = grid.attribute_dictionaries["grid"]

    nodes = dict["nodes"]
    totalsGrid = dict["results"]
    valueRange = dict["valueRange"]
    colorBasis = cs["colorBasis"]
    numCols = cs["numCols"]
    colours = cs["colours"]
    maxColVal = cs["maxColVal"]
    minColVal = cs["minColVal"]
    maxCol = cs["maxCol"]
    minCol = cs["minCol"]

    pts = coords.collect { |c| nodes[c[1]][c[0]] } # the corners of the cell as points

    # If all the vertices are valid nodes (i.e. fitted within the face(s)
    if pts.all?
      # Add the face
      newFace = grid.entities.add_face(pts)
      ## Colour the face
      # Determine a weight depending on how the user has chosen to color cells
      vals = coords.collect { |c| totalsGrid[c[1]][c[0]] }
      case colorBasis
      when "average"
        weight = 0 # weight within the whole scale
        for i in 0...vals.length
          weight += vals[i]
        end
        weight = weight.to_f / (vals.length)
      when "minimum"
        weight = vals.min
      when "maximum"
        weight = vals.max
      end
      # p "weight=#{weight}"
      if textents != nil
        text_coor = [0, 0, 0]
        pts.each do |pt|
          text_coor[0] += pt[0]
          text_coor[1] += pt[1]
          text_coor[2] += pt[2]
        end
        text_coor[0] = text_coor[0] / pts.length
        text_coor[1] = text_coor[1] / pts.length
        text_coor[2] = text_coor[2] / pts.length + 1
        textents.add_text("#{weight.to_f.round(2)}", Geom::Point3d.new(text_coor))
      end
      weight = weight.to_f / valueRange

      # p "weight=#{weight}"
      # if weight > maxColVal/100
      #    colour = maxCol
      # elsif weight < minColVal/100
      #    colour = minCol
      # else
      weight = [[weight, 1].min, 0].max
      bands = (numCols - 1).to_f
      found = false
      # Identify the gradient band (e.g. between blue and yellow) that the overall weight, i.e. the face, falls under
      for i in 0...bands
        if weight >= i / bands && weight <= (i + 1) / bands
          w = (weight - i / bands) * bands # Blending weighting within the band
          colour = Sketchup::Color.new(colours[i + 1]).blend(Sketchup::Color.new(colours[i]), w)
          found = true
          break
        end
      end
      # end
      newFace.material = colour; newFace.back_material = colour;
    end
  end

  def self.color_grid(grid)
    # Function:
    # Recreates and colors grid faces in a SketchUp model based on stored attribute dictionary data.
    # Since SketchUp Face objects cannot be directly stored in attribute dictionaries, this method
    # removes existing faces from the grid's entities and recreates them with appropriate colors
    # according to predefined color settings. Supports both quadrilateral and triangular (surface) grids.
    # 
    # Parameters:
    # grid : Sketchup::Group
    # The group object representing the grid, which contains an attribute dictionary named "grid"
    # that stores node layout, grid type, and whether it is a surface grid. The group's entities
    # are modified by removing existing faces and adding new colored ones.
    # 
    # Returns:
    # None
    # This method does not return a value. It modifies the grid in place by erasing existing face
    # entities and creating new colored faces within a subgroup of the grid's entities.
    # Face objects (which the cells array contains) cannot be passed on via attribute dictionaries,
    # so in order to access faces in the grid in order by coordinates, they are removed and recreated
    # Find all faces and remove them
    toRemove = []
    grid.entities.each { |ent|
      if ent.is_a? Sketchup::Face
        toRemove << ent
      end
    }
    grid.entities.erase_entities(toRemove)
    textents = grid.entities.add_group.entities

    dict = grid.attribute_dictionaries["grid"]
    cs = @color_setting[dict["type"]]

    # p "color_setting=#{cs}"
    # Add the faces from scratch, colouring as you go
    nodes = dict["nodes"]
    # For each cell/face:
    for y in 0...nodes.length - 1
      for x in 0...nodes[0].length - 1
        # Surface grids are made up of triangular faces, so they're different
        if dict["is_surface"]
          self.color_cells([[x, y], [x + 1, y], [x + 1, y + 1]], grid, cs, textents)
          self.color_cells([[x, y], [x, y + 1], [x + 1, y + 1]], grid, cs, textents)
        else
          self.color_cells([[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1]], grid, cs, textents)
        end
      end
    end
  end

  def self.pack_grid_data(grid)
    # """
    # Function
    # --------
    # Converts grid data from a SketchUp attribute dictionary into a standardized hash format,
    # transforming 3D point coordinates from inches to meters and organizing associated result data.
    # 
    # Parameters
    # ----------
    # grid : Sketchup::Entity or Sketchup::ComponentInstance
    # A SketchUp entity or instance that contains an attribute dictionary named "grid".
    # This dictionary must include:
    # - "nodes": A 2D array of 3D points (or nil values), where each point has x, y, z attributes.
    # - "is_surface": A boolean indicating whether the grid represents a surface.
    # - "results": An array of numerical values associated with each node.
    # - "valueRange": A two-element array representing the [min, max] range of the results.
    # 
    # Returns
    # -------
    # Hash
    # A hash containing the processed grid data with the following keys:
    # - "is_surface" (Boolean): Indicates if the grid is a surface.
    # - "nodes" (Array of Array of Array of Float or Boolean):
    # A 2D grid where each element is either a 3-element array [x, y, z] in meters (converted from inches via *0.0254),
    # or `false` if the original node was nil.
    # - "values" (Array): The raw result values associated with each node.
    # - "value_range" (Array of Float): The minimum and maximum bounds of the result values.
    # """
    dict = grid.attribute_dictionaries["grid"]
    nodes = dict["nodes"]
    # 将坐标点转化为不带单位的数值
    nodes_values = []
    nodes.each do |row|
      row_values = []
      row.each do |node|
        if node
          row_values.push [node.x * 0.0254, node.y * 0.0254, node.z * 0.0254]
        else
          row_values.push false
        end
      end
      nodes_values.push row_values
    end

    return_data = {
      "is_surface" => dict["is_surface"],
      "nodes" => nodes_values,
      "values" => dict["results"],
      "value_range" => dict["valueRange"]
    }
    return return_data
  end

  def self.get_initialised_model_dict()
    # Function
    # --------
    # Get or initialize the model attribute dictionary for storing grid settings.
    # 
    # This method retrieves the 'Grids' attribute dictionary from the active SketchUp model.
    # If the dictionary does not exist, it creates a new one with default values, including
    # initializing the 'grid_id' to 1.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # Hash
    # The attribute dictionary named "Grids" associated with the active model.
    # If the dictionary does not exist, a new one is created and initialized before returning.
    # Create, if necessary, the model attribute dictionary with default settings, current grid ID, etc.
    model = Sketchup.active_model
    model_dict = model.attribute_dictionary("Grids", false)
    # For new models...
    if not model_dict
      model_dict = model.attribute_dictionary("Grids", true)
      model_dict["grid_id"] = 1
      # Moosas::GridAppObserver.onOpenModel(model)
    end
    return model_dict
  end
end

class CustomBounds
  def initialize(entityArray)
    # """
    # Function
    # --------
    # Initializes a bounding box by computing the minimum and maximum coordinates from a collection of entities.
    # 
    # Parameters
    # ----------
    # entityArray : Array<Sketchup::Entity>
    # An array of SketchUp entities (e.g., edges or faces) used to compute the spatial bounds. Only entities of type
    # Sketchup::Edge or Sketchup::Face are processed. Each entity must have a `vertices` collection with `position`
    # attributes for coordinate extraction.
    # 
    # Returns
    # -------
    # None
    # This method is a constructor and does not return a value. It initializes instance variables representing
    # the bounding box limits: @maxx, @minx, @maxy, @miny, @maxz, @minz.
    # """
    inf = 1.0 / 0
    @maxx = -inf
    @minx = inf
    @maxy = -inf
    @miny = inf
    @maxz = -inf
    @minz = inf
    for ent in entityArray
      if ent.is_a? Sketchup::Edge or ent.is_a? Sketchup::Face
        for vert in ent.vertices
          v = vert.position
          @maxx = [@maxx, v.x].max
          @minx = [@minx, v.x].min
          @maxy = [@maxy, v.y].max
          @miny = [@miny, v.y].min
          @maxz = [@maxz, v.z].max
          @minz = [@minz, v.z].min
        end
      end
    end
  end

  def center
    # Function
    # --------
    # Calculate and return the center point of a 3D bounding box defined by extreme coordinate values.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters. It uses instance variables @maxx, @minx, @maxy, @miny, @maxz, and @minz to compute the center.
    # 
    # Returns
    # -------
    # Array<Number>
    # A three-element array representing the (x, y, z) coordinates of the center point, where:
    # - x = (@maxx + @minx) / 2
    # - y = (@maxy + @miny) / 2
    # - z = (@maxz + @minz) / 2
    return [(@maxx + @minx) / 2, (@maxy + @miny) / 2, (@maxz + @minz) / 2]
  end

  attr_reader :maxx, :minx, :maxy, :miny, :maxz, :minz
end

# 渲染型legend
class MoosasGridScaleRender
  attr_reader :bounds, :colors, :unit, :description, :seg_count

  def initialize(min, max, description = "Point in time illuminance", unit = 'lux', colors = [Sketchup::Color.new(75, 104, 160), Sketchup::Color.new(249, 236, 80), Sketchup::Color.new(230, 49, 6)], seg_count = 10, decimals = 2)
    # """
    # Function
    # --------
    # Initialize a color gradient and value bounds mapping for illuminance visualization.
    # 
    # Parameters
    # ----------
    # min : Float
    # The minimum value of the illuminance range.
    # max : Float
    # The maximum value of the illuminance range.
    # description : String, optional
    # Description of the data being represented (default is "Point in time illuminance").
    # unit : String, optional
    # Unit of measurement for the values (default is 'lux').
    # colors : Array of Sketchup::Color, optional
    # Array of SketchUp Color objects defining the gradient spectrum (default is blue, yellow, red).
    # seg_count : Integer, optional
    # Number of segments or steps in the gradient (default is 10).
    # decimals : Integer, optional
    # Number of decimal places to round the bound values (default is 2).
    # 
    # Returns
    # -------
    # None
    # This constructor initializes internal state but does not return a value.
    # 
    # Notes
    # -----
    # - The method generates interpolated colors between the provided color stops.
    # - `seg_count` is incremented by 1 internally to include both endpoints.
    # - Value bounds are linearly distributed between `min` and `max`, rounded to `decimals`.
    # - The description is updated to include the unit information.
    # - Internal attributes `@colors`, `@bounds`, `@unit`, `@description`, and `@seg_count` are set.
    # """
    # colors=colors.map{|c| c.to_a}
    seg_count += 1
    @colors = []
    @bounds = []
    for i in 0..seg_count - 1
      c = ((colors.length - 1).to_f * i.to_f / (seg_count - 1).to_f).to_f
      @colors.push(colors[c.floor].blend(colors[c.ceil], c.ceil - c))
      @bounds.push((i.to_f / (seg_count - 1).to_f * (max - min).to_f + min.to_f).round(decimals))
    end
    @unit = unit
    @description = description + "\nunits:" + @unit
    @seg_count = seg_count
  end

  def get_color(data)
    # """
    # Function
    # --------
    # Interpolates and returns a color based on the input data value by blending between predefined color stops.
    # 
    # Parameters
    # ----------
    # data : Numeric
    # The input value used to determine the corresponding color. It is compared against the bounds defined in `@bounds`.
    # 
    # Returns
    # -------
    # Color
    # A color object representing the interpolated color. If `data` is less than the first bound, the first color is returned.
    # If `data` is greater than or equal to the last bound, the last color is returned. Otherwise, the color is linearly blended
    # between the two surrounding colors in `@colors` based on the relative position of `data` within the corresponding bounds.
    # """

    if data < @bounds[0]
      return @colors[0]
    end
    for i in 1..@bounds.length - 1
      if @bounds[i] > data
        col = @colors[i - 1].blend(@colors[i], (data - @bounds[i - 1]) / (@bounds[i] - @bounds[i - 1]))

        return col
      end
    end
    return @colors[-1]
  end

  def draw_panel(references_selection = nil, origin = nil, scale = 1.0)
    # Function
    # --------
    # Draws a legend panel in the active SketchUp model based on a given selection of references or the entire model bounds.
    # The panel consists of colored segments with labels and a description, positioned according to the spatial dimensions
    # of the input geometry. The orientation and placement of the legend are determined by the smallest and largest axes
    # of the bounding box. The legend is scaled and transformed to fit appropriately within the 3D space.
    # 
    # Parameters
    # ----------
    # references_selection : Array<Sketchup::Entity>, optional
    # A collection of SketchUp entities (e.g., faces) used to compute the bounding box for legend positioning.
    # If not provided, the bounding box of the entire active model is used. Default is nil.
    # 
    # origin : Geom::Point3d, optional
    # A point that defines the relative offset for placing the legend panel. If not provided, the origin is set to [0,0,0].
    # The final position is calculated relative to the computed anchor point on the bounding box. Default is nil.
    # 
    # scale : Float, optional
    # A scaling factor applied to the size of the legend panel. This adjusts the overall dimensions of the drawn elements.
    # Default is 1.0.
    # 
    # Returns
    # -------
    # Sketchup::Group
    # A group object added to the active entities of the model, containing the visual representation of the legend,
    # including colored faces, text labels, and descriptive text. The group is transformed to align with the determined
    # axis directions and scaled appropriately based on the context geometry.

    box = []
    if references_selection == nil
      box = Sketchup.active_model.bounds
    else
      domain = [[], [], []]
      MMR.traverse_faces(references_selection) do |e, path|
        e.vertices.each { |ver|
          [0, 1, 2].each { |i| domain[i] << ver.position[i] }
        }
      end
      box = Geom::BoundingBox.new()
      box.add([
                Geom::Point3d.new(domain[0].min, domain[1].min, domain[2].min),
                Geom::Point3d.new(domain[0].max, domain[1].max, domain[2].max)
              ])
    end
    group = Sketchup.active_model.active_entities.add_group
    entities = group.entities
    '' '
        - 0 = [0, 0, 0] (left front bottom)
        - 1 = [1, 0, 0] (right front bottom)
        - 2 = [0, 1, 0] (left back bottom)
        - 3 = [1, 1, 0] (right back bottom)
        - 4 = [0, 0, 1] (left front top)
        - 5 = [1, 0, 1] (right front top)
        - 6 = [0, 1, 1] (left back top)
        - 7 = [1, 1, 1] (right back top)
        legend摆放原则：xyz三尺寸最短方向作为法向，最长方向或者z轴作为径向，原点位于径向右下角
        yx = 1
        xy = 3
        yz = 3
        xz = 1
        ' ''

    # 确认box的尺寸
    x = box.max[0] - box.min[0]
    y = box.max[1] - box.min[1]
    z = box.max[2] - box.min[2]
    x_axis, y_axis, z_axis = Geom::Vector3d.new(x + 0.1, 0, 0), Geom::Vector3d.new(0, y + 0.1, 0), Geom::Vector3d.new(0, 0, z + 0.1)

    if [x, y, z].min == z
      # if x<=y
      axis = [x_axis, y_axis, z_axis]
      position_legend = box.corner(1)
      # else
      #    axis = [y_axis,x_axis,z_axis]
      #    position_legend = box.corner(3)
      # end
    elsif [x, y, z].min == x
      axis = [y_axis, z_axis, x_axis]
      position_legend = box.corner(3)
    elsif [x, y, z].min == y
      axis = [x_axis, z_axis, y_axis]
      position_legend = box.corner(1)
    end

    # 确认相对原点
    if origin == nil
      origin = Geom::Point3d.new([0, 0, 0])
    end

    transfrom = Geom::Vector3d.new(axis[0])
    transfrom.length = transfrom.length * 0.1 * scale
    poi = position_legend + transfrom
    origin = Geom::Point3d.new([poi[0] * (1 + origin[0]), poi[1] * (1 + origin[1]), poi[2] * (1 + origin[2])])

    # 按照1的比例绘制legend
    for i in 0..@seg_count - 1
      pts = [Geom::Point3d.new([0, i, 0])]
      pts.push(Geom::Point3d.new([0.9, i, 0]))
      pts.push(Geom::Point3d.new([0.9, i + 0.9, 0]))
      pts.push(Geom::Point3d.new([0, i + 0.9, 0]))
      pts.push(Geom::Point3d.new([0, i, 0]))
      lgface = entities.add_face(pts)
      lgface.material = @colors[i]
      lgface.back_material = @colors[i]
      lgtext = entities.add_group
      lgtext.entities.add_3d_text(@bounds[i].to_s, TextAlignLeft, "Arial", letter_height = 0.5.inch)

      lgtext.move!(Geom::Transformation.new(Geom::Point3d.new([1.0, i + 0.2, 0])))
      lgtext.transform!(Geom::Transformation.scaling(Geom::Point3d.new([1.0, i + 0.2, 0]), 0.5))
      lgtext.material = Sketchup::Color.new ("Black")
    end
    descrip = entities.add_group
    descrip.entities.add_3d_text(@description, TextAlignLeft, "Arial", letter_height = 0.5.inch)
    descrip.move!(Geom::Transformation.new(Geom::Point3d.new([0, @seg_count, 0])))
    descrip.transform!(Geom::Transformation.scaling(Geom::Point3d.new([0, @seg_count, 0]), 0.5))
    descrip.material = Sketchup::Color.new ("Black")

    # legend放大，移动到指定位置,旋转
    # print(axis)

    # group.move!(Geom::Transformation.new(origin))
    scale_size = axis[1].length / (group.bounds.max[1] - group.bounds.min[1])
    group.transform!(Geom::Transformation.axes(origin, axis[0], axis[1], axis[2]))
    group.transform!(Geom::Transformation.scaling(origin, scale_size))
    # group.transform!(Geom::Transformation.scaling(origin, y.length/@seg_count))

  end
end

# 互动型legend
class MoosasGridScaleSelectionObserver < Sketchup::SelectionObserver

  OSX = Object::RUBY_PLATFORM =~ /(darwin)/i

  def sendScaleScripts
    # """
    # Function
    # --------
    # Executes scale-related scripts based on selection consistency and system platform.
    # 
    # Determines whether to apply a gradient script based on the uniformity of scale data across selected entities.
    # If all selected entities produce matching scale scripts (excluding the last two characters), a gradient is applied
    # using the first selection. Otherwise, a gray gradient script is executed. Additionally, on macOS (OSX), it blurs
    # the dialog window to prevent UI focus issues.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on instance variables and the current selection
    # in the SketchUp model.
    # 
    # Returns
    # -------
    # nil
    # This method returns nil if the scale has not been loaded or should not be shown, based on the
    # `@scaleLoaded` and `@shouldShowScale` instance variables. Otherwise, it performs side effects via
    # script execution in the dialog and returns implicitly nil after completion.
    # """
    return if not (@scaleLoaded and @shouldShowScale)
    sel = Sketchup.active_model.selection
    if sel.all? { |g| populate_script(g)[0...-2] == populate_script(sel[0])[0...-2] }
      # p "using makeGradient()"
      makeGradient(sel[0])
    else
      # p "using grayGradient()"
      @dialog.execute_script("grayGradient();")
    end
    if OSX
      @dialog.execute_script("window.blur();")
    end
  end

  def initialize()
    # Function:
    # Initializes a new instance of the class, setting up a web dialog for displaying and editing color scales, along with associated callbacks and default state variables.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    @width = 215; @height = 200;
    @scaleLoaded = false; @shouldShowScale = false;
    @dialog = UI::WebDialog.new("图示", false, "Color scale", @width, @height, 5, 100, true)
    @dialog.set_size(@width, @height)
    @dialog.add_action_callback("pop") { |wd, p|
      @scaleLoaded = true;
      sendScaleScripts
    }
    path = MPath::UI + "scale.html"
    @dialog.set_file(path)
    @dialog.add_action_callback("edit_scale") { |web_dialog, p|
      grids = Sketchup.active_model.selection.to_a.select { |g| g.attribute_dictionaries and g.attribute_dictionaries["grid"] and g.attribute_dictionaries["grid"]["id"] }
      width = 480; height = 390;
      scale_dialog = UI::WebDialog.new("Edit color scale", true, "Edit color scale", width, height, 300, 100, true)
      path = MPath::UI + "scale.html"
      scale_dialog.set_file(path)
      scale_dialog.show
      scale_dialog.add_action_callback("pop") { |sd, p|
        scale_dialog.execute_script(populate_script(grids[0]))
        scale_dialog.set_size(width, height + 1)
      }
    }
    @prevSelection = nil
  end

  def onSelectionBulkChange(sel)
    # """
    # Function
    # --------
    # Handles bulk selection changes by evaluating the selected elements and updating UI components
    # such as scale display and grid statistics information based on the current selection state.
    # 
    # Parameters
    # ----------
    # sel : Enumerable
    # A collection of selected elements. It will be converted to an array for processing.
    # Each element is expected to have attribute dictionaries, specifically a "grid" dictionary
    # containing a "results" key.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a meaningful value. It returns nil explicitly in certain cases
    # when the selection does not meet the required conditions (e.g., missing results in grid attributes).
    # """
    sel = sel.to_a
    if Moosas.selectionShouldHaveScale(sel)
      if not sel.collect { |e| e.attribute_dictionaries["grid"]["results"] }.all?
        return
      end
      if not sel == @prevSelection
        showScale
        showGridStasticsInfo # 显示网格统计信息
      end
    else
      closeScale
      clearGridStasticsInfo
    end
    @prevSelection = sel
  end

  def showScale
    # Function:
    # Displays the scale dialog and initializes necessary components for scaling operation.
    # On macOS, it shows the dialog modally; on other platforms, it reinitializes the dialog before showing.
    # It also records the current selection state and triggers the sending of scale-related scripts.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
    if OSX
      @dialog.show_modal
    else
      closeScale
      initialize
      @dialog.show
    end
    sel = Sketchup.active_model.selection
    @prevSelection = sel.to_a
    @shouldShowScale = true
    sendScaleScripts
  end

  def showGridStasticsInfo
    # """
    # Function
    # ----------
    # showGridStasticsInfo
    # Displays grid statistics information by collecting result data from selected entities' attribute dictionaries.
    # 
    # Parameters
    # ----------
    # None
    # This method does not take any parameters. It operates on the current selection in the active SketchUp model.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value. It collects data internally but does not output or return it directly.
    # """
    a = []
    sels = Sketchup.active_model.selection
    sels.each do |sel|
      dic = sel.attribute_dictionaries["grid"]
      res = dic["results"]
      a.push(res)
    end
    # MoosasWebDialog.send("update_sunhour_result",a)
  end

  def clearGridStasticsInfo
    # """
    # Function
    # ----------
    # clearGridStasticsInfo
    # Clears grid statistics information. Currently, this method is a placeholder
    # and does not perform any operations. It may be intended to reset or update
    # grid-related statistical data through a dialog interface.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # None
    # """
    # MoosasWebDialog.send("update_sunhour_result",[])
  end

  def onSelectionCleared(sel)
    # """
    # Function
    # ----------
    # onSelectionCleared
    # Called when the current selection is cleared. Stores the previous selection,
    # closes any active scale, and clears grid statistics information.
    # 
    # Parameters
    # ----------
    # sel : object
    # The selection object to be processed. It is expected to have a `to_a` method
    # that converts the selection into an array, which is then stored as the previous selection.
    # 
    # Returns
    # -------
    # None
    # This method does not return any value.
    # """
    @prevSelection = sel.to_a
    closeScale
    clearGridStasticsInfo
  end

  def colToStr(col)
    # """
    # Function:
    # Converts the RGB components of a color object into a hexadecimal string representation.
    # 
    # Parameters:
    # col : object
    # A color object with accessible `red`, `green`, and `blue` attributes, each representing
    # the intensity of the respective color channel as an integer in the range 0-255.
    # 
    # Returns:
    # str : string
    # A 6-character uppercase hexadecimal string representing the color in RGB format.
    # Each pair of characters corresponds to the red, green, and blue components,
    # padded with a leading zero if necessary to ensure two digits per channel.
    # """
    str = ''
    for part in [col.red, col.green, col.blue]
      hexpart = part.to_s(16).upcase
      hexpart = '0' + hexpart if hexpart.length == 1
      str += hexpart
    end
    return str
  end

  def quote(str)
    # Function:
    # Wraps the input string with double quotation marks.
    # 
    # Parameters:
    # str : String
    # The input string to be quoted.
    # 
    # Returns:
    # String
    # A new string with the original content enclosed in double quotes.
    return '"' + str + '"'
  end

  def makeGradient(grid)
    # Function:
    # Generates and executes a JavaScript script to create a gradient based on color settings from a grid attribute dictionary.
    # This method is intended for compatibility with legacy code that expects a specific format for color gradient generation.
    # 
    # Parameters:
    # grid : object
    # A grid object that contains attribute dictionaries, specifically expected to have a "grid" dictionary with a "type" field.
    # The grid is used to retrieve color configuration and value ranges for gradient generation.
    # 
    # Returns:
    # None
    # This method does not return a value. It instead triggers the execution of a JavaScript function within a dialog
    # via `@dialog.execute_script` to render the gradient in a web context.

    # Legacy code for makeGradientDeprecated in scale.html, which took in an array of RGB arrays
    dict = grid.attribute_dictionaries["grid"]
    cs = MoosasGrid.color_setting[dict["type"]]

    if false
      cols = "["
      colours = cs["colours"]
      for c in 0...colours.length
        col = colours[c]
        cols += "[#{col.red}, #{col.green}, #{col.blue}]"
        if c < colours.length - 1
          cols += ","
        end
      end
      cols += "]"
    end

    cols = quote(cs["colours"].collect { |col| colToStr(col) }.join("-"))
    maxCol = quote(colToStr(cs["maxCol"]))
    minCol = quote(colToStr(cs["minCol"]))
    script = "makeGradient(#{cols}, #{cs['maxColVal']}, #{cs['minColVal']}, #{dict['valueRange']}, '#{cs['unit']}',#{cs['suffix_length']},#{maxCol}, #{minCol})"
    # p "script=#{script}"
    @dialog.execute_script(script)
  end

  def populate_script(grid)
    # """
    # Function
    # --------
    # Generates a JavaScript function call string for populating a grid visualization based on color settings and attribute dictionary.
    # 
    # Parameters
    # ----------
    # grid : object
    # A grid object that contains an `attribute_dictionaries` hash; specifically expects a sub-hash under the key "grid"
    # containing at least a "type" field used to look up color configuration.
    # 
    # Returns
    # -------
    # str
    # A formatted string representing a JavaScript function call `populate(...)`, which includes:
    # - Number of colors (as integer)
    # - Color values in order: maximum column color, minimum column color, followed by reversed list of other colors
    # - Maximum color value (converted to integer)
    # - Minimum color value (converted to integer)
    # - Index of the color basis mode ("average", "maximum", or "minimum") based on configuration
    # The returned string is ready to be executed or embedded in a JavaScript context.
    # """
    dict = grid.attribute_dictionaries["grid"]
    cs = MoosasGrid.color_setting[dict["type"]]
    numCols = cs["colours"].length
    script = 'populate(' + numCols.to_s + ','
    n = 0
    for col in ([cs["maxCol"]] + [cs["minCol"]] + cs["colours"].reverse)

      script += quote(colToStr(col))

      n += 1

      if n < numCols + 2
        script += ','
      else
        script += '],'
      end

      script += '[' if n == 2

    end
    script += Integer(cs["maxColVal"]).to_s + ',' + Integer(cs["minColVal"]).to_s + ',' + ["average", "maximum", "minimum"].index(cs["colorBasis"]).to_s + ')'
    return script
  end

  def closeScale()
    # Function:
    # Closes the dialog associated with the instance if it is currently visible. Handles cases where the dialog may not be showing by catching exceptions and logging a message.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # nil : Returns nil after attempting to close the dialog or handling the exception.
    return
    begin
      if @dialog.visible?
        @dialog.close
      end
    rescue
      puts "Can't close: Dialog not showing. No big deal."
    end
  end
end

# class MoosasGridAppObserver < Sketchup::AppObserver

#    def onOpenModel(model)
#        if model.attribute_dictionary("Grids", false)
#            # Add a selection observer to show the scale when appropriate
#            scaleObserver = MoosasGridScaleSelectionObserver.new
#            model.selection.add_observer(scaleObserver)
#            Moosas::GridScaleObservers[model] = scaleObserver
#        end
#    end
# end

# module Moosas
#    GridScaleObservers = Hash.new
#    GridAppObserver = MoosasGridAppObserver.new
#    Sketchup.add_observer(GridAppObserver)
#    GridAppObserver.onOpenModel(Sketchup.active_model)

#     def Moosas.selectionShouldHaveScale(sel)
#        sel.collect{ |e| e.is_a? Sketchup::Group and e.attribute_dictionaries and e.attribute_dictionaries["grid"] and e.attribute_dictionaries["grid"]["id"]}.all? and sel.length>0
#    end
# end