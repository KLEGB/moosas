class MoosasShapeGenerator

    '''
        params = []
        L1:底层南向长度
        L2:底层西向长度
        n: 层数
        h: 层高
        s：顶层与首层边长比例
        t：顶层与首层偏转角度
        wwri：[],东、南、西、北窗墙比
    '''
    def self.generate_parametric_building(params)
    # Function:
    # Generates a parametric building based on the provided parameters. The type of building is determined by the first parameter, which specifies the shape (e.g., rectangle, triangle, L-shape, etc.). Depending on the type, the appropriate generator method is called to construct the building.
    # 
    # Parameters:
    # params : Array
    # An array of parameters used to define the building's properties. The first element (params[0]) is a numeric value that determines the building type (rounded to the nearest integer). Remaining elements are passed to the specific building generation method and may include dimensions, positions, or other shape-specific attributes.
    # 
    # Returns:
    # building : Object or nil
    # An instance of the generated building object corresponding to the specified type. If the type is not recognized or supported, returns nil.

        p "generate_parametric_building #{params}"

        type = params[0].to_f
        type = type.round()
        case type
        when 0  #矩形
            building = self.generate_rectangle_building(params)
        when 1  #三角形
            building = self.generate_triangle_building(params)
        when 2  #L形
            building = self.generate_l_shape_building(params)
        when 3  #凹形
            building = self.generate_spill_shape_building(params)
        when 4 #paper 定制的形状
            building = self.generate_paper_shape_building(params)
        else
            building = nil
        end

        return building
    end


    def self.generate_rectangle_building(params)
    # Function
    # --------
    # Generates a 3D rectangular building model in SketchUp with multiple floors and specified window-to-wall ratios (WWR) on each facade. The building is created as a group entity and optionally rotated around a vertical axis.
    # 
    # Parameters
    # ----------
    # params : Array
    # An array containing the following elements:
    # - [1] : Float
    # Length of the building along the x-axis (l1).
    # - [2] : Float
    # Width of the building along the y-axis (l2).
    # - [3] : Numeric
    # Number of floors (n), rounded to the nearest integer.
    # - [4] : Float
    # Height of each floor (h).
    # - [5] : Float
    # Rotation angle of the building in degrees (t).
    # - [6] : Float
    # Window-to-wall ratio for the east-facing facade (wwr_east).
    # - [7] : Float
    # Window-to-wall ratio for the south-facing facade (wwr_south).
    # - [8] : Float
    # Window-to-wall ratio for the west-facing facade (wwr_west).
    # - [9] : Float
    # Window-to-wall ratio for the north-facing facade (wwr_north).
    # 
    # Returns
    # -------
    # Sketchup::Group
    # A SketchUp group entity representing the generated building, containing all faces (walls, windows, roof, and floor) organized within the model's entities collection. The group is tagged with a custom attribute indicating it is an 'optimizer' type 'building'.
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1 / 2.0
            il2 = l2 / 2.0

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m

            pts = []
            pts.push Geom::Point3d.new(0.0 - il1, 0 - il2 ,h1)
            pts.push Geom::Point3d.new(0.0 + il1, 0 - il2 ,h1)
            pts.push Geom::Point3d.new(0.0 + il1, 0 + il2 ,h1)
            pts.push Geom::Point3d.new(0.0 - il1, 0 + il2 ,h1)
            pts.push Geom::Point3d.new(0.0 - il1, 0 - il2 ,h2)
            pts.push Geom::Point3d.new(0.0 + il1, 0 - il2 ,h2)
            pts.push Geom::Point3d.new(0.0 + il1, 0 + il2 ,h2)
            pts.push Geom::Point3d.new(0.0 - il1, 0 + il2 ,h2)

            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[3],pts[2],pts[1],pts[0]]
            front,w1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[5],pts[4]],wwr_south)
            right,w2 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[6],pts[5]],wwr_east)
            back,w3 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[7],pts[6]],wwr_north)
            left,w4 = self.generate_face_wwr(entities,[pts[3],pts[0],pts[4],pts[7]],wwr_west)
            top = entities.add_face [pts[4],pts[5],pts[6],pts[7]]
        end

        return group
    end

    def self.generate_triangle_building(params)
    # Function
    # --------
    # Generates a parametric triangular building mass with multiple floors, rotated by a specified angle, and adds it to the active SketchUp model. Each floor is constructed with defined wall dimensions and window-to-wall ratios (WWRs) for each facade.
    # 
    # Parameters
    # ----------
    # params : Array<Numeric>
    # An array containing the following parameters in order:
    # - [1] l1 : Numeric
    # Length of the base side of the triangular footprint (in meters).
    # - [2] l2 : Numeric
    # Length of the height side of the triangular footprint (in meters).
    # - [3] n : Numeric
    # Number of floors; will be rounded to the nearest integer.
    # - [4] h : Numeric
    # Height of each floor (in meters).
    # - [5] t : Numeric
    # Rotation angle around the Z-axis (in degrees).
    # - [6] wwr_east : Numeric
    # Window-to-wall ratio for the east-facing facade (0.0 to 1.0).
    # - [7] wwr_south : Numeric
    # Window-to-wall ratio for the south-facing facade (0.0 to 1.0).
    # - [8] wwr_west : Numeric
    # Window-to-wall ratio for the west-facing facade (0.0 to 1.0).
    # - [9] wwr_north : Numeric
    # Window-to-wall ratio for the north-facing facade (0.0 to 1.0).
    # 
    # Returns
    # -------
    # Sketchup::Group
    # A group object representing the generated triangular building, containing all geometry (faces, windows) organized under a single entity. The group is tagged with a dictionary attribute indicating it is an "optimizer" type "building".
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1
            il2 = l2

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m

            pts = []
            pts.push Geom::Point3d.new(0.0, 0, h1)
            pts.push Geom::Point3d.new(il1, 0, h1)
            pts.push Geom::Point3d.new(0.0, il2, h1)
            pts.push Geom::Point3d.new(0.0, 0, h2)
            pts.push Geom::Point3d.new(il1, 0, h2)
            pts.push Geom::Point3d.new(0.0, il2, h2)

            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[2],pts[1],pts[0]]
            front,w1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[4],pts[3]],wwr_south)
            right,w2 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[5],pts[4]],wwr_east)
            left,w3 = self.generate_face_wwr(entities,[pts[2],pts[0],pts[3],pts[5]],wwr_west)
            top = entities.add_face [pts[3],pts[4],pts[5]]
        end

        return group
    end

    def self.generate_l_shape_building(params)
    # Function
    # --------
    # Generates an L-shaped building model in SketchUp based on provided parameters, including dimensions, number of floors, height, rotation angle, wall thickness, and window-to-wall ratios (WWRs) for each facade.
    # 
    # Parameters
    # ----------
    # params : Array<Numeric>
    # An array containing the following elements:
    # - params[1] : float
    # Length of the first leg of the L-shape along the x-axis (l1).
    # - params[2] : float
    # Length of the second leg of the L-shape along the y-axis (l2).
    # - params[3] : float
    # Number of floors (n), rounded to the nearest integer.
    # - params[4] : float
    # Height of each floor (h) in meters.
    # - params[5] : float
    # Rotation angle (t) in degrees around the z-axis.
    # - params[6] : float
    # Window-to-wall ratio (WWR) for the east-facing walls.
    # - params[7] : float
    # Window-to-wall ratio (WWR) for the south-facing walls.
    # - params[8] : float
    # Window-to-wall ratio (WWR) for the west-facing walls.
    # - params[9] : float
    # Window-to-wall ratio (WWR) for the north-facing walls.
    # 
    # Returns
    # -------
    # Sketchup::Group
    # A SketchUp group object representing the generated L-shaped building, with faces for each floor level and appropriate WWR-applied facades. The group is tagged with a custom attribute indicating it is an 'building' created by the 'optimizer'.
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1
            il2 = l2

            il3 = l1 * 0.4
            il4 = l2 * 0.4

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m
            il3 = il3.m
            il4 = il4.m

            pts = []
            pts.push Geom::Point3d.new(0.0, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, il4 ,h1)
            pts.push Geom::Point3d.new(il1, il4 ,h1)
            pts.push Geom::Point3d.new(il1, il2 ,h1)
            pts.push Geom::Point3d.new(0, il2 ,h1)

            pts.push Geom::Point3d.new(0.0, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, il4 ,h2)
            pts.push Geom::Point3d.new(il1, il4 ,h2)
            pts.push Geom::Point3d.new(il1, il2 ,h2)
            pts.push Geom::Point3d.new(0, il2 ,h2)


            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]

            s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[7],pts[6]],wwr_south)
            e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[8],pts[7]],wwr_east)
            s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[9],pts[8]],wwr_south)
            e2,we2 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[10],pts[9]],wwr_east)
            n1,wn1 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[11],pts[10]],wwr_north)
            w1,ww1 = self.generate_face_wwr(entities,[pts[5],pts[0],pts[6],pts[11]],wwr_west)

            top = entities.add_face [pts[6],pts[7],pts[8],pts[9],pts[10],pts[11]]
        end

        return group
    end

    def self.generate_spill_shape_building(params)
    # Function:
    # Generates a 3D building geometry with multiple levels (spill shape) based on given parameters, including dimensions, number of floors, rotation angle, and window-to-wall ratios (WWR) for each facade direction. The building is constructed using SketchUp's entity system within a grouped component.
    # 
    # Parameters:
    # params : Array<Numeric>
    # An array containing the following elements:
    # - [0]: Unused parameter (index 0).
    # - [1] (l1): Length of the building in the x-direction (in meters).
    # - [2] (l2): Length of the building in the y-direction (in meters).
    # - [3] (n): Number of stories/floors (will be rounded to nearest integer).
    # - [4] (h): Height of each floor (in meters).
    # - [5] (t): Rotation angle around the z-axis (in degrees).
    # - [6] (wwr_east): Window-to-wall ratio for the east-facing facades.
    # - [7] (wwr_south): Window-to-wall ratio for the south-facing facades.
    # - [8] (wwr_west): Window-to-wall ratio for the west-facing facades.
    # - [9] (wwr_north): Window-to-wall ratio for the north-facing facades.
    # 
    # Returns:
    # Sketchup::Group
    # A SketchUp group object representing the generated building, containing all faces (including bottom, top, and vertical walls with optional windows), transformed according to the specified rotation. The group is tagged with a custom attribute indicating it is an "optimizer" type "building".
        l1 = params[1]
        l2 = params[2]
        n = params[3].round()
        h = params[4]
        t = params[5]
        wwr_east = params[6]
        wwr_south = params[7]
        wwr_west = params[8]
        wwr_north = params[9]

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        origin = Geom::Point3d.new(l1/2.0, l2/2.0, 0)
        z_axis = Geom::Vector3d.new(0, 0, 1)
        angle = t.degrees

        for i in 0..n-1

            h1 = i * h
            h2 = h1 + h

            il1 = l1
            il2 = l2

            il3 = l1 * 0.3
            il4 = l2 * 0.4
            il5 = l1 * 0.7

            h1 = h1.m
            h2 = h2.m
            il1 = il1.m
            il2 = il2.m
            il3 = il3.m
            il4 = il4.m
            il5 = il5.m

            pts = []
            pts.push Geom::Point3d.new(0.0, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, 0.0 ,h1)
            pts.push Geom::Point3d.new(il3, il4 ,h1)
            pts.push Geom::Point3d.new(il5, il4 ,h1)
            pts.push Geom::Point3d.new(il5, 0 ,h1)
            pts.push Geom::Point3d.new(il1, 0 ,h1)
            pts.push Geom::Point3d.new(il1, il2 ,h1)
            pts.push Geom::Point3d.new(0, il2 ,h1)

            pts.push Geom::Point3d.new(0.0, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, 0.0 ,h2)
            pts.push Geom::Point3d.new(il3, il4 ,h2)
            pts.push Geom::Point3d.new(il5, il4 ,h2)
            pts.push Geom::Point3d.new(il5, 0 ,h2)
            pts.push Geom::Point3d.new(il1, 0 ,h2)
            pts.push Geom::Point3d.new(il1, il2 ,h2)
            pts.push Geom::Point3d.new(0, il2 ,h2)


            transformation = Geom::Transformation.rotation(origin, z_axis, angle)
            pts.each do |p|
                p.transform!(transformation)
            end

            bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
            s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_south)
            e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_east)
            s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_south)
            w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_west)
            s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_south)
            e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_east)
            n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_north)
            w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_west)
            top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
        end

        return group
    end

    '''
        生成文章所有的建筑形体
    '''
    def self.generate_paper_shape_building(params)
    # Function:
    # Generates a 3D building model with a paper-like shape using specified parameters, creating multiple floor segments and applying structural details via repeated component addition. The building is organized within a group entity and assigned a custom attribute for identification.
    # 
    # Parameters:
    # params : Array<Numeric>
    # An array of numeric values representing dimensional parameters for the building components.
    # Expected to contain at least 9 elements:
    # - params[1] : Width (w1) of the first building segment.
    # - params[2] : Common width (w3) used across all floor spills.
    # - params[3] : Depth dimension (d21) for the second floor spill.
    # - params[4] : Depth dimension (d31) for the third floor spill.
    # - params[5] : Depth dimension (d41) for the fourth floor spill.
    # - params[6] : Inner depth offset (d22) for the second floor spill.
    # - params[7] : Inner depth offset (d32) for the third floor spill.
    # - params[8] : Inner depth offset (d42) for the fourth floor spill.
    # Note: d11 and d12 are hardcoded as 40 and 32 respectively.
    # 
    # Returns:
    # Sketchup::Group
    # A group entity containing the generated building geometry, including all floor spill components.
    # The group is tagged with a dictionary attribute under MoosasConstant::KEY_DICTIONARY
    # with key "optimizer" set to "building" for later reference or processing.
        w1 = params[1]
        w3 = params[2]
        d11 = 40
        d21 = params[3]
        d31 = params[4]
        d41 = params[5]
        d12 = 32
        d22 = params[6]
        d32 = params[7]
        d42 = params[8] 


        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities


        self.add_single_floor_spill(entities,60,d11,w3,d11-d12,60-w1,0,6,40-d11)
        self.add_single_floor_spill(entities,60,d21,w3,d21-d22,60-w1,6.05,12.05,40-d21)
        self.add_single_floor_spill(entities,60,d31,w3,d31-d32,60-w1,12.1,18.1,40-d31)
        self.add_single_floor_spill(entities,60,d41,w3,d41-d42,60-w1,18.15,24.15,40-d41)

        return group
    end


    @roof_material = Sketchup.active_model.materials.add('Roof_M')
    @roof_material.color =  Sketchup::Color.new(102, 204, 0)
    def self.add_single_floor_spill(entities,il1,il2,il3,il4,il5,h1,h2,y_offset=0,with_window=true)
    # Function:
    # Creates a single floor slab with surrounding faces and windows in a 3D modeling environment,
    # typically used in building geometry generation. The method defines a horizontal floor/ceiling
    # slab at two heights (h1 and h2), constructs the perimeter faces between them, and applies
    # window-to-wall ratios (WWRs) on each vertical face based on orientation. Optional window
    # insertion is supported via a flag.
    # 
    # Parameters:
    # entities : Sketchup::Entities
    # The entities collection to which the geometry will be added.
    # il1 : Numeric
    # Length value for a segment along the x-axis (in model units), converted to meters.
    # il2 : Numeric
    # Length value for a segment along the y-axis (in model units), converted to meters.
    # il3 : Numeric
    # Length value defining an intermediate x-axis dimension (in model units), converted to meters.
    # il4 : Numeric
    # Length value defining an intermediate y-axis dimension (in model units), converted to meters.
    # il5 : Numeric
    # Length value extending further along the x-axis (in model units), converted to meters.
    # h1 : Numeric
    # Bottom height of the floor slab (in model units), converted to meters.
    # h2 : Numeric
    # Top height of the floor slab (in model units), converted to meters.
    # y_offset : Numeric, optional
    # Vertical offset along the y-axis for positioning the entire structure (default is 0).
    # with_window : Boolean, optional
    # Flag indicating whether windows should be generated based on WWR values (default is true).
    # 
    # Returns:
    # Array containing:
    # - The bottom face (Sketchup::Face) created at height h1.
    # - Eight pairs of vertical faces and their corresponding window groups or faces,
    # resulting from `generate_face_wwr` calls for each wall segment.
    # - The top face (Sketchup::Face) created at height h2.
    # Note: The exact return structure depends on the implementation of `generate_face_wwr`,
    # but generally returns face/window components for each wall section.
        wwr_east = 0.4
        wwr_south = 0.4
        wwr_west = 0.5
        wwr_north = 0.3

        h1 = h1.m
        h2 = h2.m
        il1 = il1.m
        il2 = il2.m
        il3 = il3.m
        il4 = il4.m
        il5 = il5.m

        y_offset = y_offset.m

        pts = []
        pts.push Geom::Point3d.new(0.0, 0.0+y_offset ,h1)
        pts.push Geom::Point3d.new(il3, 0.0+y_offset ,h1)
        pts.push Geom::Point3d.new(il3, il4+y_offset ,h1)
        pts.push Geom::Point3d.new(il5, il4+y_offset ,h1)
        pts.push Geom::Point3d.new(il5, 0+y_offset ,h1)
        pts.push Geom::Point3d.new(il1, 0+y_offset ,h1)
        pts.push Geom::Point3d.new(il1, il2+y_offset ,h1)
        pts.push Geom::Point3d.new(0, il2+y_offset ,h1)

        pts.push Geom::Point3d.new(0.0, 0.0+y_offset ,h2)
        pts.push Geom::Point3d.new(il3, 0.0+y_offset ,h2)
        pts.push Geom::Point3d.new(il3, il4+y_offset ,h2)
        pts.push Geom::Point3d.new(il5, il4+y_offset ,h2)
        pts.push Geom::Point3d.new(il5, 0+y_offset ,h2)
        pts.push Geom::Point3d.new(il1, 0+y_offset ,h2)
        pts.push Geom::Point3d.new(il1, il2+y_offset ,h2)
        pts.push Geom::Point3d.new(0, il2+y_offset ,h2)


        bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
        s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_south,with_window)
        e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_east,with_window)
        s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_south,with_window)
        w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_west,with_window)
        s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_south,with_window)
        e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_east,with_window)
        n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_north,with_window)
        w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_west,with_window)
        top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
        top.material = top.back_material = @wall_materail
    end


    @window_material = Sketchup.active_model.materials.add('Joe')
    @window_material.color =  Sketchup::Color.new(100,149,237)
    @window_material.alpha = 0.5
    @wall_materail =  Sketchup.active_model.materials.add('moosas_wall')
    @wall_materail.color =  Sketchup::Color.new(255,255,255)
    def self.generate_face_wwr(entities,pts,wwr,with_window=true)
    # Function
    # --------
    # Generates a wall face with an optional window opening on it, based on given points and a window-to-wall ratio (WWR).
    # 
    # Parameters
    # ----------
    # entities : Sketchup::Entities
    # The entities collection to which the generated face(s) will be added.
    # pts : Array<Geom::Point3d>
    # An array of four 3D points defining the rectangular boundary of the wall face in counter-clockwise order.
    # wwr : Float
    # Window-to-wall ratio (between 0 and 1), representing the proportion of the window area relative to the total wall area.
    # with_window : Boolean, optional
    # If true (default), a window face is created within the wall; if false, no window is created.
    # 
    # Returns
    # -------
    # Array<Sketchup::Face, Sketchup::Face or nil>
    # A two-element array where the first element is the wall face, and the second element is the window face if `with_window` is true,
    # or nil if `with_window` is false.
        face =  entities.add_face pts

        face.material = face.back_material = @wall_materail


        if not with_window
            return [face,nil]
        end

        w = (1.0 - Math.sqrt(wwr)) / 2.0

        wpts = []
        wpts.push Geom::Point3d.linear_combination(1-w, pts[0], w, pts[2])
        wpts.push Geom::Point3d.linear_combination(1-w, pts[1], w, pts[3])
        wpts.push Geom::Point3d.linear_combination(1-w, pts[2], w, pts[0])
        wpts.push Geom::Point3d.linear_combination(1-w, pts[3], w, pts[1])

        window = entities.add_face wpts
        window.material = window.back_material = @window_material

        [face,window]
    end

    def self.generate_thu_env_building(ls)
    # Function:
    # Generates a 3D building structure in SketchUp using the provided list of floor parameters, where each floor is created with specific geometric attributes and stacked vertically.
    # 
    # Parameters:
    # ls : Array<Numeric>
    # A list of numeric values representing the length or size parameter for each floor level. Each value influences the dimensions of the corresponding floor in the generated building.
    # 
    # Returns:
    # Group
    # A SketchUp group entity that contains all the geometry of the generated multi-floor building. The group is tagged with a custom attribute 'optimizer' under the MoosasConstant::KEY_DICTIONARY namespace, with a unique identifier prefixed by 'thu_env_building'.

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "thu_env_building#{(rand()*1000).round()}"
        entities = group.entities

        h = 0.0
        ls.each do |l|
            MoosasShapeGenerator.add_single_floor_spill(entities,56,l,16,l-18,36,h,h+4,57-l)
            h += 4.0
        end
    end

    #生成许多毕业的方案
    def self.generate_xuduo_building(params)
    # """
    # Function
    # --------
    # generate_xuduo_building
    # 
    # Generates a 3D building model in SketchUp with variable geometric configurations based on input parameters. The building is constructed floor by floor, with each floor potentially having one of four distinct shape types (rectangular or L-shaped extensions on x/y axes). Window-to-wall ratios (WWRs) are applied to façades, and special vertical setbacks or stepped volumes are introduced based on height and offset rules.
    # 
    # Parameters
    # ----------
    # params : Array<Numeric>
    # An array of 10 numeric parameters used to define the building geometry:
    # - params[0] : Base width (w) of the building (in meters).
    # - params[1] : Multiplier for extension 'a' along x-axis (a = w * params[1]).
    # - params[2] : Multiplier for extension 'b' along y-axis (b = w * params[2]).
    # - params[3] : Rate of vertical transition space (c_r), used to calculate additional setback height.
    # - params[4] : Multiplier for offset 'x' along x-axis (x = w * params[4]).
    # - params[5] : Multiplier for offset 'y' along y-axis (y = w * params[5]).
    # - params[6] : Ratio determining starting floor for vertical transformation (z_r).
    # - params[7] : Window-to-wall ratio (WWR) for the south façade.
    # - params[8] : Window-to-wall ratio (WWR) for the west façade.
    # - params[9] : Window-to-wall ratio (WWR) for the east façade.
    # Note: WWR for the north façade is fixed at 0.2.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It modifies the active SketchUp model by adding a group entity representing the generated building, with faces for floors, walls, and optional window openings based on WWR settings.
    # """
        with_window = true

        w = params[0]
        a = w * params[1]
        b = w * params[2]
        c_r = params[3]
        x = w * params[4]
        y = w * params[5]
        z_r = params[6]
        wwr_s = params[7]
        wwr_w = params[8]
        wwr_e = params[9]
        wwr_n = 0.2

        fn = (10000.0 / (w * w)).round()  #楼层数
        h = fn * 4.5   #层高

        fz = (fn * z_r).round()   #对应z的起始楼层
        z = fz * 4.5

        if z < 50
            c = (50 - z) * c_r
            fc = (c / 4.5).round()   #交错空间的层数
            if fc + fz > fn
                fc = fn - fz
            end5
        else
            c = 0
            fc = 0
        end

        group = Sketchup.active_model.entities.add_group
        group.set_attribute MoosasConstant::KEY_DICTIONARY, "optimizer", "building"
        entities = group.entities

        w = w.m
        a = a.m
        b = b.m
        c = c.m
        x = x.m
        y = y.m
        z = z.m

        i = 0
        shape_type = nil
        while i < fn
            if i < fz or i >= fz + fc
                shape_type = 0  #矩形
            else
                if x + a <= w
                    if y + b <= w  #嵌入其中
                        shape_type = 0
                    else
                        shape_type = 2
                    end
                else
                    if y + b <= w
                        shape_type = 1
                    else
                        shape_type = 3
                    end
                end
            end
            #p "shape_type=#{shape_type}"

            h1 = (i * 4.5).m
            h2 = ((i +1)* 4.5).m
            if shape_type == 0  #矩形
                pts  =  []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)
                bottom = entities.add_face [pts[3],pts[2],pts[1],pts[0]]
                self.generate_face_wwr(entities,[pts[0],pts[1],pts[5],pts[4]],wwr_s,with_window)
                self.generate_face_wwr(entities,[pts[1],pts[2],pts[6],pts[5]],wwr_e,with_window)
                self.generate_face_wwr(entities,[pts[2],pts[3],pts[7],pts[6]],wwr_n,with_window)
                self.generate_face_wwr(entities,[pts[3],pts[0],pts[4],pts[7]],wwr_w,with_window)
                top = entities.add_face [pts[4],pts[5],pts[6],pts[7]]
            elsif shape_type == 1  #x边超出，y边未超出
                pts = []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, y, h1)
                pts.push Geom::Point3d.new(x+a, y, h1)
                pts.push Geom::Point3d.new(x+a, y+b, h1)
                pts.push Geom::Point3d.new(w, y+b, h1)
                pts.push Geom::Point3d.new(w, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, y, h2)
                pts.push Geom::Point3d.new(x+a, y, h2)
                pts.push Geom::Point3d.new(x+a, y+b, h2)
                pts.push Geom::Point3d.new(w, y+b, h2)
                pts.push Geom::Point3d.new(w, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)

                bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
                s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_s,with_window)
                e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_s,with_window)
                w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_w,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_n,with_window)
                e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_e,with_window)
                n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_n,with_window)
                w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_w,with_window)
                top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]

            elsif shape_type == 2  #x边未超出,y边超出

                pts = []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, w, h1)
                pts.push Geom::Point3d.new(x+a, w, h1)
                pts.push Geom::Point3d.new(x+a, y+b, h1)
                pts.push Geom::Point3d.new(x, y+b, h1)
                pts.push Geom::Point3d.new(x, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, w, h2)
                pts.push Geom::Point3d.new(x+a, w, h2)
                pts.push Geom::Point3d.new(x+a, y+b, h2)
                pts.push Geom::Point3d.new(x, y+b, h2)
                pts.push Geom::Point3d.new(x, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)

                bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
                s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_s,with_window)
                e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_n,with_window)
                w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_n,with_window)
                e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_w,with_window)
                n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_n,with_window)
                w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_w,with_window)
                top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
            
            elsif shape_type == 3  #x边和y边均超出

                pts = []
                pts.push Geom::Point3d.new(0.0, 0.0, h1)
                pts.push Geom::Point3d.new(w, 0.0, h1)
                pts.push Geom::Point3d.new(w, y, h1)
                pts.push Geom::Point3d.new(x+a, y, h1)
                pts.push Geom::Point3d.new(x+a, y+b, h1)
                pts.push Geom::Point3d.new(x, y+b, h1)
                pts.push Geom::Point3d.new(x, w, h1)
                pts.push Geom::Point3d.new(0, w, h1)
                pts.push Geom::Point3d.new(0.0, 0.0, h2)
                pts.push Geom::Point3d.new(w, 0.0, h2)
                pts.push Geom::Point3d.new(w, y, h2)
                pts.push Geom::Point3d.new(x+a, y, h2)
                pts.push Geom::Point3d.new(x+a, y+b, h2)
                pts.push Geom::Point3d.new(x, y+b, h2)
                pts.push Geom::Point3d.new(x, w, h2)
                pts.push Geom::Point3d.new(0, w, h2)

                bottom = entities.add_face [pts[7],pts[6],pts[5],pts[4],pts[3],pts[2],pts[1],pts[0]]
                s1,ws1 = self.generate_face_wwr(entities,[pts[0],pts[1],pts[9],pts[8]],wwr_s,with_window)
                e1,we1 = self.generate_face_wwr(entities,[pts[1],pts[2],pts[10],pts[9]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[2],pts[3],pts[11],pts[10]],wwr_s,with_window)
                w1,ww1 = self.generate_face_wwr(entities,[pts[3],pts[4],pts[12],pts[11]],wwr_e,with_window)
                s2,ws2 = self.generate_face_wwr(entities,[pts[4],pts[5],pts[13],pts[12]],wwr_n,with_window)
                e2,we2 = self.generate_face_wwr(entities,[pts[5],pts[6],pts[14],pts[13]],wwr_w,with_window)
                n1,wn1 = self.generate_face_wwr(entities,[pts[6],pts[7],pts[15],pts[14]],wwr_n,with_window)
                w2,ww2 = self.generate_face_wwr(entities,[pts[7],pts[0],pts[8],pts[15]],wwr_w,with_window)
                top = entities.add_face [pts[8],pts[9],pts[10],pts[11],pts[12],pts[13],pts[14],pts[15]]
            end
                    
            i += 1
        end
    end


    def self.test_xuduo()
    # """
    # Function
    # --------
    # test_xuduo : method of class object
    # Generates a random set of parameters and uses them to create a building
    # via the MoosasShapeGenerator for testing purposes. Outputs the generated
    # parameters to stdout.
    # 
    # Parameters
    # ----------
    # None
    # This method does not accept any parameters.
    # 
    # Returns
    # -------
    # Object
    # Returns the result of `MoosasShapeGenerator.generate_xuduo_building(params)`,
    # which is typically a generated building object or structure, though the exact
    # return type depends on the implementation of the generator method.
    # """
        params = [30 + 70 * rand(),rand(),rand(),rand(),rand(),rand(),rand(),rand(),rand(),rand()]
        p "x=#{params}"
        MoosasShapeGenerator.generate_xuduo_building(params)
    end

    def self.test(type=0)
    # Function:
    # Test method that generates a parametric building using predefined parameters with an optional type specifier.
    # 
    # Parameters:
    # type : int, optional
    # The type identifier for the building configuration (default is 0).
    # 
    # Returns:
    # object
    # The generated parametric building object returned by `generate_parametric_building`.
        params = [type,60.0,50.0,10,4.0,0.0,0.4,0.4,0.4,0.4]
        self.generate_parametric_building(params)
    end

end



end
