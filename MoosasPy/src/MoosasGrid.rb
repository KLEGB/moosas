
class MoosasGrid
    Ver='0.6.3'

    class << self
        attr_reader :color_setting
    end


    #传入参数params=[网格大小，网格距离平面距离，网格边沿缩进值]
    def self.fit_grids(params=[1.0,0.1,0.01])
        model = Sketchup.active_model
        entities = model.active_entities
        selection =[]
        MMR.traverse_faces(model.selection){|e,path|selection.push(e)}
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
                prompts = ["网格大小：","网格偏移距离："]
                defaults = ["1.0","0.1"]
                input = UI.inputbox(prompts, defaults, "请输入网格参数！")
            else
                prompts = ["Gird size:","Reference height:"]
                defaults = ["1.0","0.1"]
                input = UI.inputbox(prompts, defaults, "Please enter required gridding parameters")
            end
            params[0] = input[0].to_f()
            params[1] = input[1].to_f()
            grid=self.fit_selection(model, entities, faces,params)
            grid_output=[]
            grid.each{ |ent| 
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

    #为选中的面生成自适应的网格
    def self.fit_selection(model,entities,faces,params,auto_mode=false,ts=nil)
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
                    while i<faces.length
                        if surface.key?(faces[i])
                            faces[i,1] = []
                        else
                            i+=1
                        end
                    end
                    # Then fit a grid to the surface
                    grids << self.fit_grid_params(surface.keys, model, entities, params, true,auto_mode,ts)
                end
            end
            faces = flatFaces
            ### Find groups of faces in the same plane and fit them each with a single grid
            # Iterate through all faces
            while faces.length>0
                # Take a single face and put it in an array, which will be all the faces in that plane
                face = faces.pop
                plane = face.plane
                facesToFit = [face]
                # Find all faces in the same plane
                i = 0
                while i<faces.length
                    # if faces[i].plane ~= plane
                    if (0...4).collect{ |j| (faces[i].plane[j] - plane[j]).abs < 1e-10 }.all?
                        facesToFit << faces[i]
                        faces[i,1] = []
                    else
                        i+=1
                    end
                end
                # Fit the array of faces
                grids << self.fit_grid_params(facesToFit, model, entities, params, false,auto_mode,ts)
            end
            # Select all fitted grids
            #Sketchup.send_action "selectSelectionTool:"
            #model.selection.clear
            #model.selection.add(grids)
            #初始化整个模型的网格参数设置
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
    def self.fit_grid_params(facesToFit, model, entities, params, is_surface,auto_mode=false,ts=nil)
        stamp = [Time.now, rand]
        #facesToFit.each{ |f| f.set_attribute("grid_fit_properties", "stamp", stamp) }

        # Calculating a translation that will used soon, before making groups
        bb = model.bounds
        minDist = [bb.max.x, bb.min.x, bb.max.y, bb.min.y, bb.max.z, bb.min.z].collect{|n| n.abs.ceil}.min
        safeDistance = 10000.m
        if bb.max.x.abs.ceil==minDist
            point = [bb.max.x + safeDistance, 0, 0]
        elsif bb.min.x.abs.ceil==minDist
            point = [bb.min.x - safeDistance, 0, 0]
        elsif bb.max.y.abs.ceil==minDist
            point = [0, 0, bb.max.y + safeDistance]
        elsif bb.min.y.abs.ceil==minDist
            point = [0, 0, bb.min.y - safeDistance]
        elsif bb.max.z.abs.ceil==minDist
            point = [0, bb.max.z + safeDistance, 0]
        elsif bb.min.z.abs.ceil==minDist
            point = [0, bb.min.z - safeDistance, 0]
        end
        point -= CustomBounds.new(facesToFit).center
        safetyMove = Geom::Transformation.translation(point)

        #### Making a copy of the faces (that is offset if appropriate) being fitted as a group
        offsetDist = params[2].m
        offsetDist = 0.01.m if offsetDist==0

        # Create an array of groups called 'groups', where each group is actually a single face (this helps to avoid intersection problems)
        groupsOriginal = facesToFit.collect{ |f| entities.add_group([f]) }
        groups = groupsOriginal.collect{ |g| g.copy }
        groupsOriginal.each{ |g| g.explode }

        # Prevent interference with the original faces by moving them far away
        entities.transform_entities(safetyMove, groups)

        # Reset facesToFit to be an array containing the new copied faces.
        # All the groups are placed inside a bigger group so because the faces might intersect after offsetting,
        # which causes deletions. This way they can be found again using entities

        # Offset each face if this is not part of a curved surface. This has to be done carefully.
        # In particular, if two faces to be fit are joined, erase the edge between them before offsetting
        if not is_surface

            faceGroup = entities.add_group(groups)
            groups.each{|g|
                g.explode
            }
            facesToFit = faceGroup.entities.to_a.select{ |ent| ent.is_a? Sketchup::Face }

            edgesToErase = []

            faceGroup.entities.each { |ent|
                if ent.is_a? Sketchup::Edge
                    connectedFaces = ent.faces
                    edgesToErase << ent if connectedFaces.length>1 and connectedFaces.collect{ |f| facesToFit.include?(f) }.all?
                end
            }

            if not edgesToErase.empty?
                faceGroup.entities.erase_entities(edgesToErase)
            end

            groups = []
            facesToFit = faceGroup.explode.grep(Sketchup::Face)

            for face in facesToFit
                singleFaceGroup = entities.add_group([face])
                faces = singleFaceGroup.entities.to_a.select{ |e| e.is_a? Sketchup::Face }
                raise "在偏移前发现一个群组包含多个面" if faces.length>1
                face = faces[0]
                offsetFace = self.offset_face(face, -offsetDist)
                toErase = singleFaceGroup.entities.to_a.select{ |e| not (e==offsetFace or offsetFace.edges.include? e) }
                singleFaceGroup.entities.erase_entities(toErase)
                groups << singleFaceGroup
            end
        end

        faceGroup = entities.add_group(groups)
        groups.each{|g|
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
            norm = Geom::Vector3d.new(0,0,1)
        end

        # Make sure the normal is pointing upwards. 0 is not used to avoid precision errors for vertical faces
        #norm.reverse! if norm.z < -0.001

        # To rotate the faces so that they lie horizontally, imagine that the face was once horizontal (the normal being (0,0,1))
        # and then was rotated into its current orientation by two rotations: one rotation around the y-axis, then one about the x-axis.
        # If you multiply the two rotation matrices by the column vector (0,0,1) you get the current normal vector of the faces.
        # Solving for the angles of rotation gives the below. Since the normal is pointing upwards, the angles must be in the range of asin: [-90, 90] (degrees)
        yangle = Math.asin(norm.x)
        sin = [[-norm.y/Math.cos(yangle), -1].max, 1].min # Dealing with an issue of floating point precision and the domain of asin
        xangle = Math.asin(sin)

        # Create the full rotation transformation and apply it
        cent = CustomBounds.new(facesToFit).center
        y_rotation = Geom::Transformation.rotation(cent,Y_AXIS,yangle)
        x_rotation = Geom::Transformation.rotation(cent,X_AXIS,xangle)
        rotation = x_rotation * y_rotation # this is the rotation that turns the unit z vector into the faces' upward unit normal
        entities.transform_entities(rotation.inverse, facesToFit) # the faces should now be horizontal (for non-surfaces)

        ## Find information about the bounds and size of the array
        bbox = CustomBounds.new(facesToFit)
        width = bbox.maxx - bbox.minx
        height = bbox.maxy - bbox.miny

        if is_surface

            # Since the grid is projected onto the surface, we create the grid directly below it
            zpos = bbox.minz-10

        else

            # We want a constant z. All the nodes should already have this, but this is what is used in case of precision errors, e.g. if the rotation was imperfect
            zpos=(bbox.minz+bbox.maxz)/2.0
        end


        # Calculate number of cells on shorter side of grid (and extract the user settings)
        # The idea is to make the cells as close to squares as possible by making the proportions of the grid
        # in terms of number of cells approximately the same as the proportions of what's being fitted
        # nx and ny are the number of cells in the x and y direction

        
        desiredWidth = params[0].m
        if width > height
            nx = (width/desiredWidth).round
            ny = (height/width*nx).round
        else
            ny = (height/desiredWidth).round
            nx = (width/height*ny).round
        end
        raiseHeight = params[1].m


        #Sidelengths of cells
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
                pt = [bbox.minx+x*cellWidth, bbox.miny+y*cellHeight, zpos]

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
        moveVector.reverse! if ( moveVector.z * raiseHeight < 0 ) # the '*' tests if these have different signs
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
                    pts = [ nodes[y][x], nodes[y+1][x], nodes[y+1][x+1] ]

                    # A face is only fitted if all its corner nodes are valid
                    if pts.all?
                        grid.entities.add_face(pts) 
                    end
                    pts = [ nodes[y][x], nodes[y][x+1], nodes[y+1][x+1] ]

                    if pts.all?
                        grid.entities.add_face(pts)  
                    end
                else
                    pts = [ nodes[y][x], nodes[y+1][x], nodes[y+1][x+1], nodes[y][x+1] ]
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


    def self.fit_grids_for_horizational_face(entities,faces,transformations,params,rendered=true)

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

            
            #p "width=#{width},height=#{height}"


            desiredWidth = params[0] / 0.0254
            if width > height
                nx = (width/desiredWidth).round
                ny = (height/width*nx).round
            else
                ny = (height/desiredWidth).round
                nx = (width/height*ny).round
            end
            raiseHeight = params[1] / 0.0254

            #p "desiredWidth=#{desiredWidth},raiseHeight=#{raiseHeight}"

            #p "nx=#{nx},ny=#{ny}"

            #Sidelengths of cells
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
                    pt = [minx+x*cellWidth, miny+y*cellHeight, zpos]
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
                    #p pt
                    row << pt
                end
                nodes << row
            end


            grid = entities.add_group

            #是否绘制面
            if rendered == true
                for y in 0...ny
                    for x in 0...nx
                        pts = [ nodes[y][x], nodes[y+1][x], nodes[y+1][x+1], nodes[y][x+1] ]
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
        surface = {} # Use hash for speedy lookup
        stack = [ face ]
        until stack.empty?
            face = stack.shift
            edges = face.edges.select { |e| e.soft? }
            for edge in edges
                for face in edge.faces
                    next if surface.key?( face )
                    stack << face
                    surface[ face ] = face
                end
            end
        end
        return surface
    end

    #缩放墙体边缘
    def self.offset_face(face, dist)
      begin
              pi = Math::PI
              if (not ((dist.class==Fixnum || dist.class==Float || dist.class==Length) && dist!=0))
                  return nil
              end
              verts=face.outer_loop.vertices
              pts = []

              # CREATE ARRAY pts OF OFFSET POINTS FROM FACE

              0.upto(verts.length-1) do |a|
                  vec1 = (verts[a].position-verts[a-(verts.length-1)].position).normalize
                  vec2 = (verts[a].position-verts[a-1].position).normalize
                  vec3 = (vec1+vec2).normalize
                  if vec3.valid?
                      ang = vec1.angle_between(vec2)/2
                      ang = pi/2 if vec1.parallel?(vec2)
                      vec3.length = dist/Math::sin(ang) 
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
                      next if b==a
                      duplicates<<b if pts[a]===pts[b]
                  end
                  break if a==pts.length-1
              end
              duplicates.reverse.each{|a| pts.delete(pts[a])}

              # CREATE FACE FROM POINTS IN pts ARRAY

              (pts.length > 2) ? (face.parent.entities.add_face(pts)) : (return nil)

      rescue
          puts "#{face} did not offset: #{pts}"
          raise
      end
    end



    @color_setting ={
        "sunhour" => 
        {
            "colorBasis" => "average",
            "numCols" => 5,
            "colours" => [Sketchup::Color.new(1,76,255),Sketchup::Color.new(1,227,225), Sketchup::Color.new(61,255,1),Sketchup::Color.new(255,161,1), Sketchup::Color.new("Red") ],
            "maxCol" => Sketchup::Color.new("Red"),
            "maxColVal" => 100.0,
            "minCol" => Sketchup::Color.new(1,76,255),
            "minColVal" => 0.0,
            "unit"=>"h",
            "suffix_length"=>0
        },
        "radiance" =>
        {
            "colorBasis" => "average",
            "numCols" => 3,
            "colours" => [Sketchup::Color.new("Blue"), Sketchup::Color.new("Red"), Sketchup::Color.new("Yellow") ],
            "maxCol" => Sketchup::Color.new("Yellow"),
            "maxColVal" => 100.0,
            "minCol" => Sketchup::Color.new("Blue"),
            "minColVal" => 0.0,
            "unit"=>"Wh/m2a",
            "suffix_length"=>0
        },
        "illuminance" =>
        {
            "colorBasis" => "average",
            "numCols" => 3,
            "colours" => [Sketchup::Color.new(75,104,160),  Sketchup::Color.new(249,236,80),  Sketchup::Color.new(230,49,6) ],
            "maxCol" => Sketchup::Color.new(230,49,6),
            "maxColVal" => 100.0,
            "minCol" => Sketchup::Color.new(75,104,160),
            "minColVal" => 0.0,
            "unit"=>"lux",
            "suffix_length"=>0
        }
    }

    #cs = color setting
    def self.color_cells(coords, grid,cs=@color_setting["sunhour"],textents=nil)
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

        pts = coords.collect{ |c| nodes[c[1]][c[0]] } # the corners of the cell as points

        # If all the vertices are valid nodes (i.e. fitted within the face(s)
        if pts.all?
            # Add the face
            newFace = grid.entities.add_face(pts)
            ## Colour the face
            # Determine a weight depending on how the user has chosen to color cells
            vals = coords.collect{ |c| totalsGrid[c[1]][c[0]] }
            case colorBasis
            when "average"
                weight = 0 # weight within the whole scale
                for i in 0...vals.length
                    weight += vals[i]
                end 
                weight = weight.to_f/(vals.length)
            when "minimum"
                weight = vals.min
            when "maximum"
                weight = vals.max
            end
            #p "weight=#{weight}"
            if textents != nil
                text_coor=[0,0,0]
                pts.each do |pt|
                    text_coor[0]+=pt[0]
                    text_coor[1]+=pt[1]
                    text_coor[2]+=pt[2]
                end
                text_coor[0]=text_coor[0]/pts.length
                text_coor[1]=text_coor[1]/pts.length
                text_coor[2]=text_coor[2]/pts.length+1
                textents.add_text("#{weight.to_f.round(2)}",Geom::Point3d.new(text_coor))
            end
            weight = weight.to_f/valueRange


            #p "weight=#{weight}"
            #if weight > maxColVal/100
            #    colour = maxCol
            #elsif weight < minColVal/100
            #    colour = minCol
            #else
                weight = [[weight, 1].min, 0].max
                bands = (numCols-1).to_f
                found = false
                # Identify the gradient band (e.g. between blue and yellow) that the overall weight, i.e. the face, falls under
                for i in 0...bands
                    if weight >= i/bands && weight <= (i+1)/bands
                        w = (weight-i/bands)*bands # Blending weighting within the band
                        colour = Sketchup::Color.new(colours[i+1]).blend(Sketchup::Color.new(colours[i]),w)
                        found = true
                        break
                    end
                end
            #end
            newFace.material = colour; newFace.back_material = colour; 
        end
    end

    def self.color_grid(grid)
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

        #p "color_setting=#{cs}"
        # Add the faces from scratch, colouring as you go
        nodes = dict["nodes"]
        # For each cell/face:
        for y in 0...nodes.length-1
            for x in 0...nodes[0].length-1
                # Surface grids are made up of triangular faces, so they're different
                if dict["is_surface"]
                    self.color_cells([[x,y],[x+1,y],[x+1,y+1]], grid,cs,textents)
                    self.color_cells([[x,y],[x,y+1],[x+1,y+1]], grid,cs,textents)
                else
                    self.color_cells([[x,y],[x+1,y],[x+1,y+1],[x,y+1]], grid,cs,textents)
                end
            end
        end
    end

    def self.pack_grid_data(grid)
        dict = grid.attribute_dictionaries["grid"]
        nodes = dict["nodes"]  
        #将坐标点转化为不带单位的数值
        nodes_values = []
        nodes.each do |row|
            row_values = []
            row.each do |node|
                if node 
                    row_values.push [node.x * 0.0254,node.y * 0.0254,node.z * 0.0254]
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
        # Create, if necessary, the model attribute dictionary with default settings, current grid ID, etc.
        model = Sketchup.active_model
        model_dict = model.attribute_dictionary("Grids", false)
        # For new models...
        if not model_dict
            model_dict = model.attribute_dictionary("Grids", true)
            model_dict["grid_id"] = 1
            #Moosas::GridAppObserver.onOpenModel(model)
        end        
        return model_dict
    end
end

class CustomBounds
    def initialize(entityArray)
        inf = 1.0/0
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
        return [(@maxx+@minx)/2, (@maxy+@miny)/2, (@maxz+@minz)/2]
    end

    attr_reader :maxx, :minx, :maxy, :miny, :maxz, :minz 
end
# 渲染型legend
class MoosasGridScaleRender
    attr_reader :bounds, :colors, :unit, :description,:seg_count
    def initialize(min,max,description="Point in time illuminance",unit='lux',colors=[Sketchup::Color.new(75,104,160),  Sketchup::Color.new(249,236,80),  Sketchup::Color.new(230,49,6)],seg_count=10,decimals=2)
        #colors=colors.map{|c| c.to_a}
        seg_count+=1
        @colors=[]
        @bounds=[]
        for i in 0..seg_count-1
            c=((colors.length-1).to_f*i.to_f/(seg_count-1).to_f).to_f
            @colors.push(colors[c.floor].blend(colors[c.ceil],c.ceil-c))
            @bounds.push((i.to_f/(seg_count-1).to_f*(max-min).to_f+min.to_f).round(decimals))
        end
        @unit=unit
        @description=description+"\nunits:"+@unit
        @seg_count=seg_count
    end
    def get_color(data)

        if data<@bounds[0]
            return @colors[0]
        end
        for i in 1..@bounds.length-1
            if @bounds[i]>data
                col=@colors[i-1].blend(@colors[i],(data-@bounds[i-1])/(@bounds[i]-@bounds[i-1]))
                
                return col
            end
        end
        return @colors[-1]
    end
    def draw_panel(references_selection=nil,origin=nil,scale=1.0)
        
        box=[]
        if references_selection==nil
            box=Sketchup.active_model.bounds
        else
            domain = [[], [], []]
            MMR.traverse_faces(references_selection) do |e,path|
                e.vertices.each{ |ver|
                    [0,1,2].each{ |i| domain[i] << ver.position[i] }
                }
            end 
            box=Geom::BoundingBox.new()
            box.add([
                Geom::Point3d.new(domain[0].min,domain[1].min,domain[2].min),
                Geom::Point3d.new(domain[0].max,domain[1].max,domain[2].max)
            ])
        end
        group=Sketchup.active_model.active_entities.add_group
        entities=group.entities
        '''
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
        '''
        
        # 确认box的尺寸
        x=box.max[0]-box.min[0]
        y=box.max[1]-box.min[1]
        z=box.max[2]-box.min[2]
        x_axis, y_axis, z_axis = Geom::Vector3d.new(x+0.1,0,0),Geom::Vector3d.new(0,y+0.1,0),Geom::Vector3d.new(0,0,z+0.1)

        if [x,y,z].min == z
            #if x<=y
                axis = [x_axis,y_axis,z_axis] 
                position_legend = box.corner(1)
            #else
            #    axis = [y_axis,x_axis,z_axis] 
            #    position_legend = box.corner(3)
            #end
        elsif [x,y,z].min == x
            axis = [y_axis,z_axis,x_axis]
            position_legend = box.corner(3)
        elsif [x,y,z].min == y    
            axis = [x_axis,z_axis,y_axis]
            position_legend = box.corner(1)
        end


        #确认相对原点
        if origin == nil
            origin=Geom::Point3d.new([0,0,0])
        end

        transfrom=Geom::Vector3d.new(axis[0])
        transfrom.length=transfrom.length*0.1*scale
        poi = position_legend+transfrom
        origin = Geom::Point3d.new([poi[0]*(1+origin[0]),poi[1]*(1+origin[1]),poi[2]*(1+origin[2])])
        

        # 按照1的比例绘制legend
        for i in 0..@seg_count-1
            pts=[Geom::Point3d.new([0,i,0])]
            pts.push(Geom::Point3d.new([0.9,i,0]))
            pts.push(Geom::Point3d.new([0.9,i+0.9,0]))
            pts.push(Geom::Point3d.new([0,i+0.9,0]))
            pts.push(Geom::Point3d.new([0,i,0]))
            lgface=entities.add_face(pts)
            lgface.material=@colors[i]
            lgface.back_material=@colors[i]
            lgtext=entities.add_group
            lgtext.entities.add_3d_text(@bounds[i].to_s,TextAlignLeft,"Arial",letter_height=0.5.inch)

            lgtext.move!(Geom::Transformation.new(Geom::Point3d.new([1.0,i+0.2,0])))
            lgtext.transform!(Geom::Transformation.scaling(Geom::Point3d.new([1.0,i+0.2,0]), 0.5))
            lgtext.material= Sketchup::Color.new ("Black")
        end
        descrip=entities.add_group
        descrip.entities.add_3d_text(@description,TextAlignLeft,"Arial",letter_height=0.5.inch)
        descrip.move!(Geom::Transformation.new(Geom::Point3d.new([0,@seg_count,0])))
        descrip.transform!(Geom::Transformation.scaling(Geom::Point3d.new([0,@seg_count,0]), 0.5))
        descrip.material = Sketchup::Color.new ("Black")

        # legend放大，移动到指定位置,旋转
        #print(axis)
        
        #group.move!(Geom::Transformation.new(origin))
        scale_size=axis[1].length/(group.bounds.max[1]-group.bounds.min[1])
        group.transform!(Geom::Transformation.axes(origin,axis[0],axis[1],axis[2]))
        group.transform!(Geom::Transformation.scaling(origin, scale_size))
        #group.transform!(Geom::Transformation.scaling(origin, y.length/@seg_count))
        
    end
end
# 互动型legend
class MoosasGridScaleSelectionObserver < Sketchup::SelectionObserver

    OSX = Object::RUBY_PLATFORM =~ /(darwin)/i

    def sendScaleScripts
        return if not (@scaleLoaded and @shouldShowScale)
        sel = Sketchup.active_model.selection
        if sel.all? { |g| populate_script(g)[0...-2] == populate_script(sel[0])[0...-2] }
            #p "using makeGradient()"
            makeGradient(sel[0])
        else
            #p "using grayGradient()"
            @dialog.execute_script("grayGradient();")
        end
        if OSX
            @dialog.execute_script("window.blur();")
        end
    end

    def initialize()
        @width = 215; @height = 200;
        @scaleLoaded = false; @shouldShowScale = false;
        @dialog = UI::WebDialog.new("图示", false, "Color scale", @width, @height, 5, 100, true)
        @dialog.set_size(@width, @height)
        @dialog.add_action_callback("pop") { |wd, p|
            @scaleLoaded = true;
            sendScaleScripts
        }
        path = MPath::UI+"scale.html"
        @dialog.set_file(path)
        @dialog.add_action_callback("edit_scale") { |web_dialog, p|
            grids = Sketchup.active_model.selection.to_a.select{ |g| g.attribute_dictionaries and g.attribute_dictionaries["grid"] and g.attribute_dictionaries["grid"]["id"]}
            width = 480; height = 390;
            scale_dialog = UI::WebDialog.new("Edit color scale", true, "Edit color scale", width, height,300, 100, true)
            path = MPath::UI+"scale.html"
            scale_dialog.set_file(path)
            scale_dialog.show
            scale_dialog.add_action_callback("pop") { |sd, p|
                scale_dialog.execute_script(populate_script(grids[0]))
                scale_dialog.set_size(width, height+1)
            }
        }
        @prevSelection = nil
    end

    def onSelectionBulkChange(sel)
        sel = sel.to_a
        if Moosas.selectionShouldHaveScale(sel)
            if not sel.collect{ |e| e.attribute_dictionaries["grid"]["results"] }.all?
                return
            end
            if not sel==@prevSelection
                showScale
                showGridStasticsInfo   #显示网格统计信息
            end
        else
            closeScale
            clearGridStasticsInfo
        end
        @prevSelection = sel
    end

    def showScale
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
        a = []
        sels = Sketchup.active_model.selection
        sels.each do |sel|
            dic = sel.attribute_dictionaries["grid"]
            res = dic["results"]
            a.push(res)
        end
        #MoosasWebDialog.send("update_sunhour_result",a)
    end

    def clearGridStasticsInfo
        #MoosasWebDialog.send("update_sunhour_result",[])
    end


    def onSelectionCleared(sel)
        @prevSelection = sel.to_a
        closeScale
        clearGridStasticsInfo
    end

    def colToStr(col)
        str=''
        for part in [col.red, col.green, col.blue]
            hexpart = part.to_s(16).upcase
            hexpart = '0' + hexpart if hexpart.length==1
            str += hexpart
        end
        return str
    end

    def quote(str)
        return '"' + str + '"'
    end

    def makeGradient(grid)

        # Legacy code for makeGradientDeprecated in scale.html, which took in an array of RGB arrays
        dict = grid.attribute_dictionaries["grid"]
        cs = MoosasGrid.color_setting[dict["type"]]


        if false
            cols = "["    
            colours = cs["colours"]
            for c in 0...colours.length
                col = colours[c]
                cols += "[#{col.red}, #{col.green}, #{col.blue}]"
                if c < colours.length-1
                    cols += ","
                end
            end
            cols += "]"
        end

        cols = quote(cs["colours"].collect { |col| colToStr(col) }.join("-"))
        maxCol = quote(colToStr(cs["maxCol"]))
        minCol = quote(colToStr(cs["minCol"]))
        script = "makeGradient(#{cols}, #{cs['maxColVal']}, #{cs['minColVal']}, #{dict['valueRange']}, '#{cs['unit']}',#{cs['suffix_length']},#{maxCol}, #{minCol})"
        #p "script=#{script}"
        @dialog.execute_script(script)
    end

    def populate_script(grid)
        dict = grid.attribute_dictionaries["grid"]
        cs = MoosasGrid.color_setting[dict["type"]]
        numCols = cs["colours"].length
        script = 'populate(' + numCols.to_s + ','
        n = 0
        for col in ([cs["maxCol"]]+[cs["minCol"]] + cs["colours"].reverse)

            script += quote(colToStr(col))

            n+=1

            if n<numCols+2
                script += ','
            else
                script += '],'
            end

            script += '[' if n==2

        end
        script += Integer(cs["maxColVal"]).to_s + ',' + Integer(cs["minColVal"]).to_s + ',' + ["average", "maximum", "minimum"].index(cs["colorBasis"]).to_s + ')'
        return script
    end

    def closeScale()
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

#class MoosasGridAppObserver < Sketchup::AppObserver

#    def onOpenModel(model)
#        if model.attribute_dictionary("Grids", false)
#            # Add a selection observer to show the scale when appropriate
#            scaleObserver = MoosasGridScaleSelectionObserver.new
#            model.selection.add_observer(scaleObserver)
#            Moosas::GridScaleObservers[model] = scaleObserver
#        end
#    end
#end

#module Moosas
#    GridScaleObservers = Hash.new
#    GridAppObserver = MoosasGridAppObserver.new
#    Sketchup.add_observer(GridAppObserver)
#    GridAppObserver.onOpenModel(Sketchup.active_model)

#     def Moosas.selectionShouldHaveScale(sel)
#        sel.collect{ |e| e.is_a? Sketchup::Group and e.attribute_dictionaries and e.attribute_dictionaries["grid"] and e.attribute_dictionaries["grid"]["id"]}.all? and sel.length>0
#    end
#end