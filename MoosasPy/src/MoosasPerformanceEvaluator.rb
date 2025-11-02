class MoosasPerformanceEvaluator
    Ver='0.6.1'

    '''
        计算体形系数和经济成本
    '''
    def self.evaluate_sc_and_economy(x)
    # Function:
    # Evaluates the structural and economic performance of a given shape based on its type.
    # Dispatches to specific evaluation methods depending on the shape type indicated by the first element of the input array.
    # 
    # Parameters:
    # x : Array
    # An array where the first element represents the shape type (0: rectangle, 1: triangle, 2: L-shape, 3: concave shape),
    # and subsequent elements contain shape-specific parameters. The array is expected to have numerical values.
    # 
    # Returns:
    # result : Object or nil
    # The result of the evaluation from the corresponding shape-specific method.
    # Returns nil if the shape type is not recognized or does not match any defined cases.

        type = x[0].to_f
        type = type.round()

        case type
        when 0  #矩形
            result = self.evaluate_sc_and_economy_rectangle(x)
        when 1  #三角形
            result = self.evaluate_sc_and_economy_triangle(x)
        when 2  #L形
            result = self.evaluate_sc_and_economy_l_shape(x)
        when 3  #凹形
            result = self.evaluate_sc_and_economy_spill_shape(x)
        else
            result = nil
        end

        return result
    end

    '''
        矩形
    '''
    def self.evaluate_sc_and_economy_rectangle(x)
    # Function:
    # Evaluate the shape coefficient (sc) and economic cost per square meter (eco) for a rectangular building design.
    # 
    # Parameters:
    # x : Array[Numeric]
    # An array containing design parameters for the building, where:
    # - x[1] : Numeric, length of the first side (l1)
    # - x[2] : Numeric, length of the second side (l2)
    # - x[3] : Numeric, number of floors (n), will be rounded to integer
    # - x[4] : Numeric, height of each floor (h)
    # - x[5] : Numeric, not used in current computation (t)
    # - x[6] : Numeric, window-to-wall ratio (WWR) for the east facade
    # - x[7] : Numeric, WWR for the south facade
    # - x[8] : Numeric, WWR for the west facade
    # - x[9] : Numeric, WWR for the north facade
    # 
    # Returns:
    # Array[Numeric]
    # A two-element array containing:
    # - sc : Numeric, shape coefficient defined as the ratio of total exterior surface area (walls, windows, roof) to building volume.
    # - eco : Numeric, average material cost per square meter, calculated as the weighted sum of wall, window, roof, and floor costs divided by total surface area. Costs are assumed as:
    # - 1400 per unit area for walls,
    # - 1800 per unit area for windows,
    # - 1000 per unit area for roof,
    # - 800 per unit area for floor.
        l1 = x[1]
        l2 = x[2]
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = l1 * l2 * h * n
        wall = (l1 * h * (1-wwr_south) + l1 * h * (1-wwr_north) + l2*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south + l1 * h * wwr_north + l2*h*wwr_east+l2*h*wwr_west) * n 
        floor = l1 * l2 * n  #内部的水平结构
        roof = l1 * l2  #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]
    end

    '''
        三角形
    '''
    def self.evaluate_sc_and_economy_triangle(x)
    # Function:
    # Evaluates the shape coefficient (SC) and economic cost per square meter of materials for a triangular L-shaped building structure based on geometric and window-to-wall ratio (WWR) parameters.
    # 
    # Parameters:
    # x : Array<Numeric>
    # An array containing input parameters for the evaluation, where:
    # - x[1] (l1): Length of one side of the triangular base (in meters).
    # - x[2] (l2): Length of the other side of the triangular base (in meters).
    # - x[3] (n): Number of floors (rounded to nearest integer).
    # - x[4] (h): Floor height (in meters).
    # - x[5] (t): Not used in current computation.
    # - x[6] (wwr_east): Window-to-wall ratio for the east-facing wall (0 to 1).
    # - x[7] (wwr_south): Window-to-wall ratio for the south-facing wall (0 to 1).
    # - x[8] (wwr_west): Window-to-wall ratio for the west-facing wall (0 to 1).
    # - x[9] (wwr_north): Window-to-wall ratio for the north-facing wall (0 to 1).
    # 
    # Returns:
    # Array<Float>
    # A two-element array containing:
    # - sc (Float): Shape coefficient, defined as the ratio of total exterior surface area (walls, windows, roof) to building volume.
    # - eco (Float): Weighted average material cost per square meter of total envelope area, calculated using fixed unit costs for walls (1400), windows (1800), roof (1000), and floor (800).

        l1 = x[1]
        l2 = x[2]
        l3 = (l1 ** 2 + l2 ** 2) ** 0.5
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = l1 * l2 / 2 * h * n
        wall = (l1 * h * (1-wwr_south) + l3*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south +  l3*h*wwr_east+l2*h*wwr_west) * n 
        floor = l1 * l2 / 2 * n  #内部的水平结构
        roof = l1 * l2 / 2 #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]

    end

    '''
        L形
    '''
    def self.evaluate_sc_and_economy_l_shape(x)
    # Function:
    # Evaluates the shape coefficient (sc) and average material cost per square meter (eco)
    # for an L-shaped building with concave geometry based on given design parameters.
    # 
    # Parameters:
    # x : array-like
    # A list or array containing the following elements in order:
    # [undefined, l1, l2, n, h, t, wwr_east, wwr_south, wwr_west, wwr_north]
    # - l1 : float
    # Length of the primary wing of the L-shaped building (x-direction).
    # - l2 : float
    # Length of the secondary wing of the L-shaped building (y-direction).
    # - n : float
    # Number of floors; will be rounded to the nearest integer.
    # - h : float
    # Floor-to-floor height.
    # - t : float
    # Thickness of structural elements (not used in current computation).
    # - wwr_east : float
    # Window-to-wall ratio on the east façade (between 0 and 1).
    # - wwr_south : float
    # Window-to-wall ratio on the south façade (between 0 and 1).
    # - wwr_west : float
    # Window-to-wall ratio on the west façade (between 0 and 1).
    # - wwr_north : float
    # Window-to-wall ratio on the north façade (between 0 and 1).
    # 
    # Returns:
    # list of float
    # A two-element list containing:
    # - sc : float
    # Shape coefficient, defined as the ratio of total exterior surface area
    # (walls, windows, and roof) to the building volume.
    # - eco : float
    # Average material cost per square meter of total exterior envelope area,
    # calculated as a weighted sum of wall, window, roof, and floor costs,
    # normalized by the total envelope area. Cost coefficients:
    # wall = 1400, window = 1800, roof = 1000, floor = 800 (arbitrary units).
        l1 = x[1]
        l2 = x[2]
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = (l1 * l2 - 0.6 * l1 * 0.6 * l2)*h * n
        wall = (l1 * h * (1-wwr_south) + l1 * h * (1-wwr_north) + l2*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south + l1 * h * wwr_north + l2*h*wwr_east+l2*h*wwr_west) * n 
        floor = (l1 * l2 - 0.6 * l1 * 0.6 * l2) * n  #内部的水平结构
        roof = (l1 * l2 - 0.6 * l1 * 0.6 * l2)  #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]
    end

    '''
        凹形
    '''
    def self.evaluate_sc_and_economy_spill_shape(x)
    # Function
    # --------
    # Evaluate the shape coefficient and economic cost per square meter of building materials
    # based on geometric and window-to-wall ratio (WWWR) parameters. This method computes
    # the volume, wall area, window area, floor area, and roof area to derive the shape
    # coefficient (SC) and economy (ECO) metrics.
    # 
    # Parameters
    # ----------
    # x : Array
    # Input array containing 10 elements in the following order:
    # - x[0]: Not used
    # - x[1] (l1): Length of the building in the east-west direction (float)
    # - x[2] (l2): Length of the building in the north-south direction (float)
    # - x[3] (n): Number of floors, rounded to nearest integer (numeric)
    # - x[4] (h): Height of each floor (float)
    # - x[5] (t): Not used
    # - x[6] (wwr_east): Window-to-wall ratio for the east facade (float, 0-1)
    # - x[7] (wwr_south): Window-to-wall ratio for the south facade (float, 0-1)
    # - x[8] (wwr_west): Window-to-wall ratio for the west facade (float, 0-1)
    # - x[9] (wwr_north): Window-to-wall ratio for the north facade (float, 0-1)
    # 
    # Returns
    # -------
    # Array
    # A two-element array containing:
    # - sc (float): Shape coefficient, defined as the ratio of total exterior surface area
    # (walls + windows + roof) to building volume.
    # - eco (float): Economic cost per square meter of building envelope materials,
    # calculated as a weighted average of material costs for walls (1400), windows (1800),
    # roof (1000), and floor (800) based on their respective areas.
        l1 = x[1]
        l2 = x[2]
        n = x[3].round()
        h = x[4]
        t = x[5]
        wwr_east = x[6]
        wwr_south = x[7]
        wwr_west = x[8]
        wwr_north = x[9]

        volumn = (l1 * l2 - 0.4 * l1 * 0.4 * l2) * h * n
        wall = (l1 * h * (1-wwr_south) + l1 * h * (1-wwr_north) + l2*h*(1-wwr_east)+l2*h*(1-wwr_west)) * n
        window = (l1 * h * wwr_south + l1 * h * wwr_north + l2*h*wwr_east+l2*h*wwr_west) * n 
        floor = (l1 * l2 - 0.4*l1 *0.4*l2) * n  #内部的水平结构
        roof = (l1 * l2 - 0.4*l1 *0.4*l2)  #外部的水平结构

        #计算体形系数
        sc = (wall + window + roof) / volumn
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)

        return [sc,eco]
    end


    '''
        计算体形系数和经济成本
    '''
    def self.evaluate_sc_and_economy_paper(x)
    # Function
    # --------
    # Evaluates the structural compactness (shape coefficient) and economic cost of a building design based on geometric parameters, using predefined window-to-wall ratios and floor height. The method computes integrated energy performance and material cost metrics across four floors.
    # 
    # Parameters
    # ----------
    # x : Array<Numeric>
    # An array of eight numeric values representing design variables:
    # - x[0] : w1 - Width parameter 1 (e.g., floor width in meters)
    # - x[1] : w3 - Width parameter 3
    # - x[2] : d21 - Depth of second floor in east-west direction
    # - x[3] : d31 - Depth of third floor in east-west direction
    # - x[4] : d41 - Depth of fourth floor in east-west direction
    # - x[5] : d22 - Depth of second floor in north-south direction
    # - x[6] : d32 - Depth of third floor in north-south direction
    # - x[7] : d42 - Depth of fourth floor in north-south direction
    # 
    # Returns
    # -------
    # Array<Numeric>
    # A two-element array containing:
    # - energy : A derived energy performance metric based on the shape coefficient (sc), calculated as `(sc * 100)**3 / 20 - 140`
    # - eco : A normalized economic cost index based on material costs per square meter, transformed as `(eco_normalized - 1000)**3 / 1000 + 680`, where `eco_normalized` is the weighted average cost of wall, window, roof, and floor materials
        w1 = x[0]
        w3 = x[1]
        d21 = x[2]
        d31 = x[3]
        d41 = x[4]
        d22 = x[5]
        d32 = x[6]
        d42 = x[7] 

        wwr_east = 0.4
        wwr_south = 0.4
        wwr_west = 0.5
        wwr_north = 0.3
        h = 6.0

        f1 = self.paper_calculate_floor_info(60,w1,w3,40,32,h,wwr_east,wwr_south,wwr_west,wwr_north)
        f2 = self.paper_calculate_floor_info(60,w1,w3,d21,d22,h,wwr_east,wwr_south,wwr_west,wwr_north)
        f3 = self.paper_calculate_floor_info(60,w1,w3,d31,d32,h,wwr_east,wwr_south,wwr_west,wwr_north)
        f4 = self.paper_calculate_floor_info(60,w1,w3,d41,d42,h,wwr_east,wwr_south,wwr_west,wwr_north)

        volumn = f1[3] + f2[3] + f3[3] + f4[3]
        wall = f1[1] + f2[1] + f3[1] + f4[1]
        window = f1[2] + f2[2] + f3[2] + f4[2]
        floor = f1[0] + f2[0] + f3[0] + f4[0]
        roof = f1[0]

        #计算体形系数
        sc = (wall + window + roof) / volumn
        energy = (sc * 100) ** 3 / 20 - 140
        #计算平米材质成本
        eco = (1400 * wall + 1800 * window + 1000 * roof + 800 * floor) / (wall + window + roof + floor)
        eco = (eco -1000) ** 3 / 1000 + 680

        return [energy,eco]
    end

    def self.paper_calculate_floor_info(w,w1,w3,d1,d2,h,we,ws,ww,wn)
    # Function:
    # Calculate floor-related geometric and architectural metrics for the Tsinghua Energy-Saving Building, including floor area, wall area, window area, and volume.
    # 
    # Parameters:
    # w : float
    # Total width of the floor in the east-west direction.
    # w1 : float
    # Width offset on one side of the floor (e.g., structural or design margin).
    # w3 : float
    # Width offset on the opposite side of the floor (e.g., structural or design margin).
    # d1 : float
    # Total depth of the floor in the north-south direction.
    # d2 : float
    # Depth reduction due to recessed or non-rectangular sections of the floor.
    # h : float
    # Height of the floor.
    # we : float
    # Window-to-wall ratio on the east-facing wall.
    # ws : float
    # Window-to-wall ratio on the south-facing wall.
    # ww : float
    # Window-to-wall ratio on the west-facing wall.
    # wn : float
    # Window-to-wall ratio on the north-facing wall.
    # 
    # Returns:
    # list of float
    # A list containing four calculated values:
    # - area (float): Net floor area after subtracting recessed regions.
    # - wall_area (float): Total exposed wall area excluding windows.
    # - window_area (float): Total area of all windows on the perimeter walls.
    # - volume (float): Volume of the floor space.
        area = w * d1 - (w - w1 -w3) * (d1 - d2)
        volumn = area * h
        wall_area = w * h * (1-ws) + w * h * (1-wn) + d1 * h * (1-we) + d1 * h * (1-ww) + (d1 - d2) * h * (1-we) + (d1 - d2) * h * (1-ww)
        window_area = w * h * ws + w * h * wn + d1 * h * we + d1 * h * ww + (d1 - d2) * h * we + (d1 - d2) * h * ww
        return [area,wall_area,window_area,volumn]
    end

    ''' 
        计算清华节能楼的体形系数和经济成本
    ''' 
    def self.evaluate_thu_env_sc_and_economy(x)
    # Function:
    # Evaluates the environmental performance and economic cost of a building's envelope
    # based on floor-level geometric and construction data. This method computes the shape
    # coefficient (SC) and the total envelope construction cost per square meter.
    # 
    # Parameters:
    # x : Array<Hash>
    # An array of floor-level configuration objects, where each element contains
    # geometric or structural parameters required for evaluating individual floors.
    # The exact structure is passed to `calculate_thu_env_floor_info` for processing.
    # 
    # Returns:
    # Array<Numeric>
    # A two-element array containing:
    # - sc (Numeric): The shape coefficient of the building, defined as 0.9 times
    # the total outer surface area divided by the building volume.
    # - eco (Numeric): The estimated total economic cost of the building envelope,
    # calculated using fixed unit costs for wall and window components.
    # Specifically: 350 * wall + 1250 * window_wse + 1250 * window_n.
        floor_info = []
        volumn = 0.0
        wall = 0.0
        window_wse = 0.0
        window_n = 0.0
        area = 0.0
        x.each do |l|
            f = self.calculate_thu_env_floor_info(56,16,20,l,18,4.0,0.7,0.7,0.7,0.2)
            floor_info.push(f)
            area += f[0]
            volumn += f[4]
            wall += f[1]
            window_wse += f[2]
            window_n += f[3]
        end

        floor = 0.0
        n = floor_info.length
        for i in 0..n-2
            floor += (floor_info[i][0] - floor_info[i+1][0]).abs
        end
        roof = floor_info[n-1][0]

        # p volumn
        # p floor
        # p roof
        # p window_wse
        # p window_n
        outer_surface_area = wall + window_wse +window_n+ roof+floor

        #计算体形系数
        sc = outer_surface_area*0.9 / volumn

        #计算平米围护结构造价
        eco = (350 * wall  + 1250 * window_wse + 1250 * window_n) #/ (wall + window_wse +window_n)

        p "wall=#{wall},window_wse=#{window_wse},window_n=#{window_n}"


        return [sc,eco]
    end

    def self.calculate_thu_env_floor_info(w,w1,w3,d1,d2,h,we,ws,ww,wn)
    # Function:
    # Calculate floor-related geometric and environmental parameters for the Tsinghua Energy-Saving Building, including area, wall area, window areas, and volume.
    # 
    # Parameters:
    # w : float
    # Total width of the floor plan.
    # w1 : float
    # Width offset on one side of the floor plan.
    # w3 : float
    # Width offset on the opposite side of the floor plan.
    # d1 : float
    # Total depth of the floor plan.
    # d2 : float
    # Depth offset or recess in the floor plan.
    # h : float
    # Height of the floor.
    # we : float
    # Window-to-wall ratio on the east facade.
    # ws : float
    # Window-to-wall ratio on the south facade.
    # ww : float
    # Window-to-wall ratio on the west facade.
    # wn : float
    # Window-to-wall ratio on the north facade.
    # 
    # Returns:
    # list of float
    # A list containing the following calculated values:
    # - area (float): Net floor area.
    # - wall_area (float): Total exterior wall area excluding windows.
    # - window_area_wse (float): Total window area on west, south, and east facades, including both main and recessed surfaces.
    # - window_area_n (float): Window area on the north facade.
    # - volume (float): Total interior volume of the floor.
        area = w * d1 - (w - w1 -w3) * (d1 - d2)
        volumn = area * h
        wall_area = w * h * (1-ws) + w * h * (1-wn) + d1 * h * (1-we) + d1 * h * (1-ww) + (d1 - d2) * h * (1-we) + (d1 - d2) * h * (1-ww)
        window_area_wse = w * h * ws  + d1 * h * we + d1 * h * ww + (d1 - d2) * h * we + (d1 - d2) * h * ww
        window_area_n = w * h * wn
        return [area,wall_area,window_area_wse,window_area_n,volumn]
    end

    ''' 
        计算清华节能楼的能耗和经济成本
    ''' 
    def self.evaluate_thu_env_energy_and_economy(x)
    # """
    # Function
    # --------
    # evaluate_thu_env_energy_and_economy
    # 
    # Evaluate the energy efficiency and economic cost of building envelope based on floor-level geometric and architectural parameters.
    # This method computes the shape coefficient (related to energy performance) and the total construction cost of the envelope components.
    # 
    # Parameters
    # ----------
    # x : Array<Array<Numeric>>
    # A nested array where each sub-array represents parameters for a building floor.
    # These parameters are passed to `calculate_thu_env_floor_info` to derive floor-specific data such as area, wall area, window areas, etc.
    # 
    # Returns
    # -------
    # Array<Numeric>
    # A two-element array containing:
    # - energy : Numeric
    # A metric representing the building's energy performance, calculated as the product of 0.9 times the outer surface area divided by volume, scaled by 600.
    # - eco : Numeric
    # An estimate of the total economic cost of the building envelope, calculated based on unit costs of walls (350 per unit area),
    # west/south/east windows (1250 per unit area), and north windows (1250 per unit area).
    # """

        floor_info = []
        volumn = 0.0
        wall = 0.0
        window_wse = 0.0
        window_n = 0.0
        area = 0.0
        x.each do |l|
            f = self.calculate_thu_env_floor_info(56,16,20,l,18,4.0,0.7,0.7,0.7,0.2)
            floor_info.push(f)
            area += f[0]
            volumn += f[4]
            wall += f[1]
            window_wse += f[2]
            window_n += f[3]
        end

        floor = 0.0
        n = floor_info.length
        for i in 0..n-2
            floor += (floor_info[i][0] - floor_info[i+1][0]).abs
        end
        roof = floor_info[n-1][0]

        # p volumn
        # p floor
        # p roof
        # p window_wse
        # p window_n
        outer_surface_area = wall + window_wse +window_n+ roof+floor

        #计算体形系数
        energy = outer_surface_area*0.9 / volumn * 600.0

        #计算平米围护结构造价
        eco = (350 * wall  + 1250 * window_wse + 1250 * window_n) #/ (wall + window_wse +window_n)

        #p "wall=#{wall},window_wse=#{window_wse},window_n=#{window_n}"


        return [energy,eco]
    end

    def self.calculate_thu_env_floor_zone_and_floor(w,w1,w3,d1,d2,h,we,ws,ww,wn)
    # Function:
    # Calculate and return geometric and environmental zone properties for a thermal environment floor space,
    # including area, wall area, window areas on different orientations, and volume. Constructs associated
    # MoosasFace and MoosasSpace objects to represent the floor, ceiling, and spatial volume.
    # 
    # Parameters:
    # w : float
    # Width of the main space (in inches).
    # w1 : float
    # Offset or cutout dimension on one side of the width.
    # w3 : float
    # Offset or cutout dimension on the opposite side of the width.
    # d1 : float
    # Depth of the main space (in inches).
    # d2 : float
    # Inner depth reduction, representing an inset or recessed area (in inches).
    # h : float
    # Height of the space (in inches).
    # we : float
    # Window-to-wall ratio on the east-facing walls.
    # ws : float
    # Window-to-wall ratio on the south-facing walls.
    # ww : float
    # Window-to-wall ratio on the west-facing walls.
    # wn : float
    # Window-to-wall ratio on the north-facing walls.
    # 
    # Returns:
    # list of float
    # A list containing the following calculated values:
    # - area: Floor area in square meters.
    # - wall_area: Total exposed wall area in square inches.
    # - window_area_wse: Total window area on south, east, and west faces in square inches.
    # - window_area_n: Window area on the north face in square inches.
    # - volumn: Volume of the space in cubic inches.
        area = w * d1 - (w - w1 -w3) * (d1 - d2)
        volumn = area * h
        wall_area = w * h * (1-ws) + w * h * (1-wn) + d1 * h * (1-we) + d1 * h * (1-ww) + (d1 - d2) * h * (1-we) + (d1 - d2) * h * (1-ww)
        window_area_wse = w * h * ws  + d1 * h * we + d1 * h * ww + (d1 - d2) * h * we + (d1 - d2) * h * ww
        window_area_n = w * h * wn


        floor = MoosasFace.new(nil,nil,area / MoosasConstant::INCH_METER_MULTIPLIER_SQR)
        floor.type = MoosasConstant::ENTITY_FLOOR
        ceil = MoosasFace.new(nil,nil,area / MoosasConstant::INCH_METER_MULTIPLIER_SQR)
        ceil.type = MoosasConstant::ENTITY_FLOOR
        s = MoosasSpace.new(floor,h / MoosasConstant::INCH_METER_MULTIPLIER,ceil)

        #e1 = 

        return [area,wall_area,window_area_wse,window_area_n,volumn]

    end

    '''
        评价许多毕设生形方案的性能
    '''
    def self.evaluate_xuduo_energy_and_df(params)
    # Function:
    # Evaluates the energy consumption and daylight factor (DF) of a building model based on input parameters.
    # This method constructs a 3D geometric model using the Moosas modeling system, simulates its energy performance,
    # and calculates average daylight factors across spaces. The results are returned as energy use intensity (EUI)
    # and a normalized daylight metric.
    # 
    # Parameters:
    # params : Array<Numeric>
    # An array of numeric parameters used to define the building geometry and properties:
    # - params[0]: Base width (w) of the building footprint.
    # - params[1]: Multiplier for dimension 'a' (a = w * params[1]).
    # - params[2]: Multiplier for dimension 'b' (b = w * params[2]).
    # - params[3]: Rate determining vertical offset (c_r), used to compute c = (50 - z) * c_r if z < 50.
    # - params[4]: Multiplier for extension 'x' (x = w * params[4]), affects floor plan protrusion.
    # - params[5]: Multiplier for extension 'y' (y = w * params[5]), affects floor plan protrusion.
    # - params[6]: Ratio determining starting floor height for special space types (z_r).
    # - params[7]: Window-to-wall ratio (WWWR) for the south facade.
    # - params[8]: Window-to-wall ratio (WWWR) for the west facade.
    # - params[9]: Window-to-wall ratio (WWWR) for the east facade.
    # Note: North facade WWR is fixed at 0.2.
    # 
    # Returns:
    # Array<Numeric>
    # A two-element array containing:
    # - eui (Numeric): Energy Use Intensity in kWh/m², calculated from total simulated energy demand.
    # - ave_df (Numeric): Adjusted average daylight factor; normalized such that values between 3 and 8 yield
    # scores decreasing from 10, while values outside this range are penalized with an added offset of 10.
        #第一步，生成MoosasModel


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

        floor_height = 4.5

        fn = (10000.0 / (w * w)).round()  #楼层数
        h = fn * 4.5   #层高

        fz = (fn * z_r).round()   #对应z的起始楼层
        z = fz * 4.5

        if z < 50
            c = (50 - z) * c_r
            fc = (c / 4.5).round()   #交错空间的层数
            if fc + fz > fn
                fc = fn - fz
            end
        else
            c = 0
            fc = 0
        end
        spaces = []

        n_s = [0.0,-1.0,0.0]
        n_e = [1.0,0.0,0.0]
        n_n = [0.0,1.0,0.0]
        n_w = [-1.0,0.0,0.0]

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

            h1 = i * 4.5
            h2 = h1 + 4.5

            area_m = 0  #面积
            bounds = []
            height = 4.5 /  MoosasConstant::INCH_METER_MULTIPLIER
            
            if shape_type == 0  #矩形
                area_m = w * w
                #南向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,w,floor_height)
                bounds.push(sb)
                #北向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,w,floor_height)
                bounds.push(sb)
                #西向墙
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)

            elsif shape_type == 1  #x边超出，y边未超出
                area_m = w * w + (x +a-w)*b
                #南1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,y,floor_height)
                bounds.push(sb)
                #南2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,(x+a-w),floor_height)
                bounds.push(sb)
                #东2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,b,floor_height)
                bounds.push(sb)
                #北1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,(x+a-w),floor_height)
                bounds.push(sb)
                #东3
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,(w-b-y),floor_height)
                bounds.push(sb)
                #北2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,w,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)
            elsif shape_type == 2  #x边未超出,y边超出
                area_m = w *w + (y + b - w)*a

                #南1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,w,floor_height)
                bounds.push(sb)
                #北1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,(w-x-a),floor_height)
                bounds.push(sb)
                #东2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,(y+b-w),floor_height)
                bounds.push(sb)
                #北2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,a,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,(y+b-w),floor_height)
                bounds.push(sb)
                #北3
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,x,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)

            elsif shape_type == 3  #x边和y边均超出
                area_m = w*w + a *b - (w - x) * (w - y)

                #南1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,w,floor_height)
                bounds.push(sb)
                #东1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,y,floor_height)
                bounds.push(sb)
                #南2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_s,n_s,(x+a-w),floor_height)
                bounds.push(sb)
                #东2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_e,n_e,b,floor_height)
                bounds.push(sb)
                #北1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,a,floor_height)
                bounds.push(sb)
                #西1
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,(y+b-w),floor_height)
                bounds.push(sb)
                #北2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_n,n_n,x,floor_height)
                bounds.push(sb)
                #西2
                sb = MoosasEdge.new(nil,height,false)
                sb.assign_value_directly(wwr_w,n_w,w,floor_height)
                bounds.push(sb)
            end
            area = area_m / MoosasConstant::INCH_METER_MULTIPLIER_SQR
            floor = MoosasFace.new(nil,nil,area,[0.0,0.0,1.0])
            if i == 0
                floor.type = MoosasConstant::ENTITY_GROUND_FLOOR
            else
                floor.type = MoosasConstant::ENTITY_FLOOR
            end
            ceils = []
            ceil = MoosasFace.new(nil,nil,area,[0.0,0.0,1.0])
            if i == fn-1
                ceil.type = MoosasConstant::ENTITY_ROOF
            else
                ceil.type = MoosasConstant::ENTITY_FLOOR
            end
            ceils.push(ceil)

            s = MoosasSpace.new(floor,height,ceils)
            s.bounds = bounds
            s.is_outer = true
            spaces.push(s)
            #s.print_info
            i += 1
        end

        model = MoosasModel.new(spaces)

        #第二步，分析模型
        #2.1分析能耗
        er = MoosasEnergy.analysis(model)
        eui = eval(er.total.to_array().join("+")) #能耗密度
        #p "energy = #{er.total.to_array()}"
        p "eui =#{eui} kWh/m2"

        #2.2分析采光
        dfs = MoosasDaylight.quick_analysis_ave_daylight_factor(model)
        ave_df = 0.0
        weight_df = 0.0
        area_all = 0.0
        dfs_pecent = [0.0,0.0,0.0]
        dfs.each do |t|
            df = t[0]

            if df <= 3.0
                dfs_pecent[0] += t[1]
                weight_df += t[0] * t[1] * 10.0
            elsif df < 8.0
                weight_df += t[0] * t[1]
                dfs_pecent[1] += t[1]
            else
                weight_df += t[0] * t[1]
                dfs_pecent[2] += t[1]
            end
            ave_df += t[0] * t[1]
            area_all += t[1]
        end
        ave_df = ave_df / area_all
        if ave_df <3  or ave_df > 8
            ave_df += 10.0
        else
            ave_df = 10.0 - ave_df
        end

        p "ave_df = #{ave_df}"
        
        #weight_df = weight_df / area_all
        #p "weight_df = #{weight_df}"

        #df_unnormal_ratio = (1 - dfs_pecent[1]/area_all)*100.0  #不达标采光面积比例
        #p "df_unnormal_ratio=#{df_unnormal_ratio} %"

        return [eui,ave_df]
    end

end