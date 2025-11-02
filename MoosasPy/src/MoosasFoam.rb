class MoosasFoam
  Ver = '0.6.3'

  @room = []
  @domain = []
  @windows = []
  @vels = []

  def self.analysis()
    # """
    # Function
    # ----------
    # analysis
    # Perform CFD (Computational Fluid Dynamics) simulation on a selected space using airflow_simulation
    # with predefined grid size and number of parallel processes, measure execution time,
    # output simulation duration or error message, and invoke visualization via ParaView.
    # 
    # Parameters
    # ----------
    # None :
    # This method does not take any parameters. It uses global variables `$current_model` and
    # `$space_select_index` to access the current building model and the index of the selected space.
    # 
    # Returns
    # -------
    # None :
    # This method does not return a value. It outputs timing information or error messages to stdout
    # and triggers a visualization process as a side effect.
    # """
    t1 = Time.new
    # 输入所选空间、网格大小（默认为0.5m）和并行数量（默认为4核）
    ach = airflow_simulation($current_model.spaces[$space_select_index], 0.5, 4)
    t2 = Time.new
    if ach
      p "CFD模拟用时： #{t2 - t1}s"
    else
      p 'CFD模拟出错.请检查'
    end
    # 调用paraView可视化
    self.view()
  end

  def self.airflow_simulation(space, grid_size, number_parallel)
    # Function
    # --------
    # Perform airflow simulation for a given space using OpenFOAM via blueCFD-Core.
    # 
    # This method checks for the presence of blueCFD-Core installation, validates the spatial configuration
    # (e.g., windows, walls), converts the 3D space geometry into STL format, sets up boundary conditions
    # including wind velocity from external data, and generates a complete OpenFOAM case directory structure.
    # It then executes the simulation in parallel if specified.
    # 
    # Parameters
    # ----------
    # space : object
    # A spatial object representing the room or building zone to simulate. Must contain geometric
    # components such as floors, ceilings, bounds (outer boundaries), walls, and glazings (windows/doors).
    # The object is expected to have methods and properties like `ceils`, `floor`, `bounds`, `is_outer`, etc.
    # grid_size : float or int
    # Specifies the mesh resolution (cell size) used in the OpenFOAM simulation. Controls the level of
    # detail in the computational fluid dynamics (CFD) mesh.
    # number_parallel : int
    # Number of processor cores to use for parallel execution of the OpenFOAM solver. Must be a positive integer.
    # 
    # Returns
    # -------
    # bool
    # Returns True if the simulation setup and execution are initiated successfully.
    # Returns False if any prerequisite fails, such as missing blueCFD installation, invalid geometry,
    # insufficient windows, or incorrect file paths.
    if not Dir.exist?("C:\\Program Files\\blueCFD-Core-2017\\")
      UI.messagebox("blueCFD not found in C:\\Program Files\\blueCFD-Core-2017\\.\nPlease check the installation of blueCFD or download from:\nhttp://bluecfd.github.io/Core/Downloads/#bluecfd-core-2017-1")
      return false
      # 判断空间是否合法
      # elif not space.is_outer
      #    UI.messagebox("所选空间非外区")
      #    return false
      # elsif space.ceils.length != 1
      #    UI.messagebox("天花板设计错误")
      #    return false
    end
    # 初始化
    @room.clear
    @domain = [1e+9, 1e+9, 1e+9, -1e+9, -1e+9, -1e+9, FoamUtil.calculate_deflection(space.bounds)]
    @windows.clear
    @vels.clear
    # 获取风速数据
    airVel = {}
    File.open(MPath::VENT + "airVel", "r") do |file|
      while line = file.gets
        av = line.split("|")
        airVel[av[0]] = av[1].to_f
      end
    end
    # 将MoosasSpace转换为stl（外窗独立）
    space.ceils.each { |ceiling| self.input_room(ceiling.face.vertices, ceiling.normal) }
    space.floor.each { |floor| self.input_room(floor.face.vertices, floor.normal) }

    space.bounds.each do |b|
      # if b.walls.length != 1
      #    UI.messagebox("外立面设计错误")
      #    return
      # end
      if b.glazings.length == 0 # 无门窗的立面
        self.input_room(b.walls[0].face.vertices, b.normal)
      else
        # 有门窗的立面
        self.input_windows(b.walls[0], b.glazings, b.normal)
        vertices_ = []
        space.floor.each { |fl| fl.face.vertices.each { |ver| vertices_.push(ver) } }
        self.input_vels(b.glazings, FoamUtil.calculate_midpoint(vertices_), b.normal, airVel)
      end
    end
    if @windows.length < 2
      UI.messagebox("The space need two or more doors and windows")
      return false
    end
    # 生成OpenFoam算例
    self.mkdir()
    self.generate_0()
    self.generate_constant()
    self.generate_system(grid_size, number_parallel)
    # 运行OpenFoam模拟
    self.run(number_parallel)
    return true
  end

  def self.input_room(vertices, normal)
    # Function
    # --------
    # Processes a list of vertices and a normal vector to generate triangulated faces for a 3D room surface,
    # transforming coordinates into inches and using Delaunay triangulation to compute the mesh.
    # The resulting triangular faces are stored in the class variable `@room`.
    # 
    # Parameters
    # ----------
    # vertices : Array<Vertex>
    # An array of vertex objects, each containing a `position` attribute (array of x, y, z coordinates).
    # normal : Array<Float>
    # A three-element array representing the normal vector of the surface (e.g., ceiling or floor).
    # Used to determine coordinate projection and domain input.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It modifies the class variable `@room` by appending
    # triangular face data constructed from the input vertices and normal vector.
    # 获取坐标索引（如顶面垂直于z轴，则取x,y坐标用作三角剖分，即0,1）
    index = FoamUtil.coordinate_index(normal)
    x, y = index[0], index[1]
    # 将坐标拼接成字符串，作为triangulate.exe的输入
    input, points = "", []
    vertices.each do |v|
      vx = (v.position[0].to_f * 0.0254).round(2)
      vy = (v.position[1].to_f * 0.0254).round(2)
      vz = (v.position[2].to_f * 0.0254).round(2)
      if x == 0 and y == 1 # 天花板和地板：确定计算域范围
        self.input_domain(vx, vy, vz)
      end
      vp = [vx.to_s, vy.to_s, vz.to_s]
      input += vp[x] + "," + vp[y] + ","
      points.push(vp[0] + " " + vp[1] + " " + vp[2])
    end
    triangles = FoamUtil.delaunay_triangulation(input[0..-2])
    # 将三角面片添加到@room数组中
    n = normal[0].round(2).to_s + " " + normal[1].round(2).to_s + " " + normal[2].round(2).to_s
    for triangle in triangles do
      face = [n, points[triangle[0]], points[triangle[1]], points[triangle[2]]]
      @room.push(face)
    end
  end

  def self.input_domain(vx, vy, vz)
    # """
    # Function
    # --------
    # Updates the domain bounds based on the transformed input vector components.
    # 
    # This method applies a 2D rotation transformation to the (vx, vy) components
    # using an angle stored in the instance variable @domain[6], then checks and
    # updates the minimum and maximum bounds for the x, y, and z axes stored in
    # @domain. The updated domain reflects the new extremal values after rotation.
    # 
    # Parameters
    # ----------
    # vx : Float
    # The x-component of the input vector before rotation.
    # vy : Float
    # The y-component of the input vector before rotation.
    # vz : Float
    # The z-component of the input vector (unaffected by rotation).
    # 
    # Returns
    # -------
    # None
    # This method modifies the instance variable @domain in place and does not return a value.
    # """
    angle = @domain[6] / 180 * Math::PI
    x = vx * Math.cos(angle) + vy * Math.sin(angle)
    if x < @domain[0]
      @domain[0] = x
    elsif x > @domain[3]
      @domain[3] = x
    end
    y = vy * Math.cos(angle) - vx * Math.sin(angle)
    if y < @domain[1]
      @domain[1] = y
    elsif y > @domain[4]
      @domain[4] = y
    end
    if vz < @domain[2]
      @domain[2] = vz
    elsif vz > @domain[5]
      @domain[5] = vz
    end
  end

  def self.input_windows(wall, glazings, normal)
    # Function
    # --------
    # Processes wall and glazing geometry to perform Delaunay triangulation on the wall surface,
    # separates triangular faces belonging to windows, and organizes them into room and window-specific structures.
    # 
    # Parameters
    # ----------
    # wall : Object
    # A wall object containing face geometry; used to extract vertices for triangulation.
    # glazings : Array
    # An array of glazing (window) objects, each with face geometry; used to identify window regions on the wall.
    # normal : Array[Numeric]
    # A 3-element array representing the normal vector of the wall plane; used to determine coordinate projection
    # for 2D triangulation and to label resulting faces.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It modifies instance variables `@room` and `@windows`:
    # - `@room`: Appends triangular face data not associated with any window.
    # - `@windows`: Appends arrays of triangular face data corresponding to each individual window.
    # 获取坐标索引
    index = FoamUtil.coordinate_index(normal)
    x, y = index[0], index[1]
    # 对外立面进行三角剖分
    input, points = "", []
    wall.face.vertices.each do |v|
      vx = (v.position[0].to_f * 0.0254).round(2).to_s
      vy = (v.position[1].to_f * 0.0254).round(2).to_s
      vz = (v.position[2].to_f * 0.0254).round(2).to_s
      vp = [vx, vy, vz]
      input += vp[x] + "," + vp[y] + ","
      points.push(vx + " " + vy + " " + vz)
    end
    triangles = FoamUtil.delaunay_triangulation(input[0..-2])
    # 获取外窗的点坐标
    points_win, windows, win_num = [], [], glazings.length
    glazings.each do |g|
      tem = []
      g.face.vertices.each do |v|
        vx = (v.position[0].to_f * 0.0254).round(2).to_s
        vy = (v.position[1].to_f * 0.0254).round(2).to_s
        vz = (v.position[2].to_f * 0.0254).round(2).to_s
        tem.push(vx + " " + vy + " " + vz)
      end
      points_win.push(tem)
      windows.push([])
    end
    # 将三角面片添加到@room数组中，并将立面上的外窗独立出来
    n = normal[0].round(2).to_s + " " + normal[1].round(2).to_s + " " + normal[2].round(2).to_s
    for triangle in triangles do
      p1, p2, p3 = points[triangle[0]], points[triangle[1]], points[triangle[2]]
      win_index, face = win_num, [n, p1, p2, p3]
      for i in 0..win_num - 1
        pw = points_win[i]
        if pw.include? p1 and pw.include? p2 and pw.include? p3
          win_index = i
          break
        end
      end
      if win_index == win_num
        @room.push(face)
      else
        windows[win_index].push(face)
      end
    end
    # 将三角面片添加到@windows数组中
    for w in windows do
      @windows.push(w)
    end
  end

  def self.input_vels(glazings, prefix, n, airVel)
    # Function
    # --------
    # Set input air velocity components for glazing surfaces based on direction and magnitude.
    # 
    # Given a list of glazing elements, a naming prefix, a normalized direction vector, and a hash of air velocities,
    # this method computes the 2D velocity components (x and y) at the midpoint of each glazing face. The computed
    # velocities are stored in the instance variable `@vels` as formatted strings. Negative velocities (indicating
    # inflow) are decomposed using the direction vector and recorded; positive or zero velocities (outflow) result
    # in an empty string entry.
    # 
    # Parameters
    # ----------
    # glazings : Array<OpenStudio::Model::SubSurface>
    # List of glazing (subsurface) objects representing windows or openings.
    # prefix : String
    # String prefix used to form the key when looking up velocity values in the airVel hash.
    # n : Array<Numeric>
    # Two-element array representing the in-plane direction vector [nx, ny]. This will be normalized internally.
    # airVel : Hash<String, Float>
    # Hash mapping string keys (formed as 'prefix,midpoint') to air velocity values. A negative value indicates inflow.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It modifies the instance variable `@vels` by appending formatted
    # velocity component strings (or empty strings for outflow conditions).
    nx, ny = n[0] / Math.sqrt((n[0]) ** 2 + (n[1]) ** 2), n[1] / Math.sqrt((n[0]) ** 2 + (n[1]) ** 2)
    glazings.each do |g|
      vel = airVel[prefix + "," + FoamUtil.calculate_midpoint(g.face.vertices)]
      if vel < 0 # 进风口
        @vels.push((vel * nx).round(2).to_s + " " + (vel * ny).round(2).to_s + " 0.0")
      else
        # 出风口
        @vels.push("")
      end
    end
  end

  def self.output_domain(grid_size)
    # """
    # Function
    # --------
    # Generate a list of formatted 3D coordinate strings representing the domain boundaries
    # after applying a rotational transformation, followed by grid resolution values.
    # 
    # The method computes the eight corner points of a 3D bounding box defined by `@domain`,
    # expands the bounds slightly (by ±0.02), applies a rotation in the XY-plane based on
    # an angle derived from `@domain[6]`, rounds coordinates to two decimal places, and
    # formats them as space-separated strings. Finally, it appends the number of grid
    # divisions along each axis based on `grid_size`.
    # 
    # Parameters
    # ----------
    # grid_size : Float
    # The size of each grid cell used to compute the number of divisions along
    # the x, y, and z axes. Must be positive.
    # 
    # Returns
    # -------
    # Array<String>
    # An array of nine strings. The first eight elements are transformed 3D corner
    # coordinates in the format "x y z", rounded to two decimal places. The ninth
    # element is the concatenation of the number of grid divisions in x, y, and z
    # directions, also separated by spaces.
    # """
    coordinates = [
      [@domain[0] - 0.02, @domain[1] - 0.02, @domain[2] - 0.02],
      [@domain[3] + 0.02, @domain[1] - 0.02, @domain[2] - 0.02],
      [@domain[3] + 0.02, @domain[4] + 0.02, @domain[2] - 0.02],
      [@domain[0] - 0.02, @domain[4] + 0.02, @domain[2] - 0.02],
      [@domain[0] - 0.02, @domain[1] - 0.02, @domain[5] + 0.02],
      [@domain[3] + 0.02, @domain[1] - 0.02, @domain[5] + 0.02],
      [@domain[3] + 0.02, @domain[4] + 0.02, @domain[5] + 0.02],
      [@domain[0] - 0.02, @domain[4] + 0.02, @domain[5] + 0.02]
    ]
    angle, domain = (360 - @domain[6]) / 180 * Math::PI, []
    coordinates.each do |c|
      x = c[0] * Math.cos(angle) + c[1] * Math.sin(angle)
      y = c[1] * Math.cos(angle) - c[0] * Math.sin(angle)
      z = c[2]
      domain.push(x.round(2).to_s + " " + y.round(2).to_s + " " + z.round(2).to_s)
    end
    x_num = ((@domain[3] - @domain[0] + 0.02) / grid_size).round().to_s
    y_num = ((@domain[4] - @domain[1] + 0.02) / grid_size).round().to_s
    z_num = ((@domain[5] - @domain[2] + 0.02) / grid_size).round().to_s
    domain.push(x_num + " " + y_num + " " + z_num)
    return domain
  end

  def self.mkdir()
    # """
    # Function
    # --------
    # Executes the mkdir command in a specified directory to create a new directory based on input path.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method that does not take any arguments.
    # 
    # Returns
    # -------
    # Boolean
    # Returns true if the system call to 'mkdir.exe' executes successfully, false otherwise.
    # Note: The actual return value depends on the behavior of the `system` call and the external executable.
    # """
    pwd = MPath::VENT + "mkdir/"
    Dir.chdir pwd
    File.write("mkdir.input", MPath::DATA + "vent/foam/")
    system("mkdir.exe")
  end

  def self.generate_0()
    # """
    # Function
    # --------
    # Generates OpenFOAM field files for initial conditions (0th time step) based on velocity data and stores them in a specified directory.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method with no parameters. It uses class variables `@vels` (velocity data) and `@windows` (window objects) to generate field files.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It performs file I/O operations to write OpenFOAM input files.
    # """
    path = MPath::DATA + "vent/foam/0/"
    win_num = @windows.length
    File.write(path + "epsilon", FoamFile.generate_epsilon(@vels))
    File.write(path + "k", FoamFile.generate_k(@vels))
    File.write(path + "nut", FoamFile.generate_nut(@vels))
    File.write(path + "p", FoamFile.generate_p(@vels))
    File.write(path + "U", FoamFile.generate_U(@vels))
  end

  def self.generate_constant()
    # """
    # Function
    # --------
    # generate_constant
    # 
    # Generates and writes several constant configuration files required for OpenFOAM simulation setup.
    # These files include the STL surface mesh of the indoor environment, gravitational settings,
    # transport properties, and turbulence properties.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method with no parameters. It uses class variables @room and @windows
    # to generate the necessary output files.
    # 
    # Returns
    # -------
    # nil
    # This method does not return any value. Its primary effect is writing files to the specified directory.
    # """
    path = MPath::DATA + "vent/foam/constant/"
    File.write(path + "triSurface/indoor_airflow.stl", FoamFile.generate_stl(@room, @windows))
    File.write(path + "g", FoamFile.generate_g())
    File.write(path + "transportProperties", FoamFile.generate_transportProperties())
    File.write(path + "turbulenceProperties", FoamFile.generate_turbulenceProperties())
  end

  def self.generate_system(grid_size, number_parallel)
    # Function:
    # Generates OpenFOAM case setup files for a ventilation simulation in a foam domain.
    # This method creates necessary dictionary files for meshing, solver control, parallel
    # decomposition, and numerical schemes based on the provided grid size and number of
    # parallel processes.
    # 
    # Parameters:
    # grid_size : Integer or Array-like
    # Specifies the resolution or cell density for the computational domain.
    # Passed to `output_domain` to compute physical domain bounds.
    # number_parallel : Integer
    # Number of subdomains for parallel computation, used to generate decomposeParDict.
    # 
    # Returns:
    # nil
    # This method does not return a value. It performs file I/O operations to write
    # multiple OpenFOAM configuration files to the specified data path.
    domain = self.output_domain(grid_size)
    path = MPath::DATA + "vent/foam/system/"
    File.write(path + "blockMeshDict", FoamFile.generate_blockMeshDict(domain))
    File.write(path + "controlDict", FoamFile.generate_controlDict())
    File.write(path + "decomposeParDict", FoamFile.generate_decomposeParDict(number_parallel))
    File.write(path + "fvSchemes", FoamFile.generate_fvSchemes())
    File.write(path + "fvSolution", FoamFile.generate_fvSolution())
    File.write(path + "snappyHexMeshDict", FoamFile.generate_snappyHexMeshDict(@windows.length, domain[0]))
    File.write(path + "surfaceFeatureExtractDict", FoamFile.generate_surfaceFeatureExtractDict())
  end

  def self.run(number_parallel)
    # Function:
    # Executes a series of OpenFOAM simulation commands by generating and running a batch script.
    # This method sets up the environment, runs meshing and solver processes, and handles
    # post-processing tasks such as reconstruction of results. The execution is performed
    # in a specified directory using Windows-style batch commands.
    # 
    # Parameters:
    # number_parallel : int
    # The number of processor cores to use for the parallel execution of the `simpleFoam` solver.
    # This value is passed to the `mpirun` command via the `-np` option.
    # 
    # Returns:
    # bool
    # Returns true if the system call to execute 'run.bat' succeeds (i.e., the batch file is
    # launched successfully), false otherwise. Note that this return value reflects only the
    # success of launching the batch script, not the success of the individual commands within it.
    lines = [
      "call \"C:\\Program Files\\blueCFD-Core-2017\\setvars.bat\"",
      "set PATH=%HOME%\\msys64\\usr\\bin;%PATH%",
    ]
    pwd = MPath::DATA + "vent/"
    Dir.chdir pwd
    lines.push(pwd[0..1])
    lines.push("cd " + pwd)
    lines.push("surfaceFeatureExtract >log\\surfaceFeatureExtract.log &")
    lines.push("blockMesh >log\\blockMesh.log &")
    lines.push("snappyHexMesh >log\\snappyHexMesh.log &")
    lines.push("del /q/a/f constant\\polyMesh")
    lines.push("copy 1\\polyMesh constant\\polyMesh")
    lines.push("del /q/a/f 1\\polyMesh")
    lines.push("rd 1\\polyMesh")
    lines.push("rd 1")
    lines.push("decomposePar >log\\decomposePar.log &")
    lines.push("mpirun -np " + number_parallel.to_s + " simpleFoam -parallel >log\\simpleFoam.log &")
    lines.push("reconstructPar >log\\reconstructPar.log &")
    path = pwd + "run.bat"
    File.write(path, lines.join("\n"))
    system("run.bat")
  end

  def self.view()
    # Function:
    # Executes a batch script to view a foam file by writing the filename to a batch script and running it.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # Boolean or nil: Returns true if the system command executes successfully, false if the command fails,
    # or nil if the command cannot be executed. The exact return value depends on the underlying system call behavior.
    pwd = MPath::DATA + "vent/"
    Dir.chdir pwd
    path = pwd + "view.bat"
    File.write(path, "vent.foam")
    system("view.bat")
  end

end

class FoamFile

  def self.generate_epsilon(vels)
    # Function:
    # Generates a string representation of an OpenFOAM epsilon file based on given velocity data.
    # The output defines boundary conditions for the turbulence dissipation rate (epsilon) field,
    # using wall functions for room boundaries and either inletOutlet or fixedValue conditions
    # for window boundaries depending on whether velocity data is present.
    # 
    # Parameters:
    # vels : Array<Array<Numeric>>
    # A nested array where each sub-array corresponds to velocity data for a window.
    # If a sub-array is empty, it indicates no velocity data is available for that window,
    # resulting in an 'inletOutlet' boundary condition; otherwise, a 'fixedValue' condition is used.
    # 
    # Returns:
    # String
    # A formatted string representing the complete epsilon field file in OpenFOAM format,
    # with appropriate boundary conditions for each window and the room, joined by newlines.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		volScalarField;",
      "	location	\"0\";",
      "	object		epsilon;",
      "}",
      "dimensions		[0 2 -3 0 0 0 0];",
      "internalField		uniform 0.01;",
      "boundaryField",
      "{",
      "    room",
      "    {",
      "        type		epsilonWallFunction;",
      "        value		uniform 0.01;",
      "    }"
    ]
    for i in 1..vels.length do
      lines.push("    window_" + i.to_s)
      lines.push("    {")
      if vels[i - 1].length == 0
        lines.push("        type		inletOutlet;")
        lines.push("        inletValue		uniform 0.1;")
        lines.push("        value		uniform 0.1;")
      else
        lines.push("        type		fixedValue;")
        lines.push("        value		uniform 0.01;")
      end
      lines.push("    }")
    end
    lines.push("}")
    return lines.join("\n")
  end

  def self.generate_k(vels)
    # Function
    # --------
    # Generates a string representation of an OpenFOAM field file for turbulent kinetic energy (k)
    # based on the given velocity boundary conditions. The output is formatted as a FoamFile
    # with appropriate boundary field settings for walls, inlets, and outlets.
    # 
    # Parameters
    # ----------
    # vels : Array<Array<Numeric>>
    # A nested array where each sub-array corresponds to velocity data for a boundary patch.
    # If a sub-array is empty, the corresponding boundary is treated as an inlet/outlet;
    # otherwise, it is treated as a fixed value boundary.
    # 
    # Returns
    # -------
    # String
    # A formatted string representing the complete k field file in OpenFOAM format,
    # with each line separated by a newline character. The file includes header information,
    # dimensions, internal field setting, and boundary field definitions with appropriate
    # boundary condition types and values.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		volScalarField;",
      "	location	\"0\";",
      "	object		k;",
      "}",
      "dimensions		[0 2 -2 0 0 0 0];",
      "internalField		uniform 0.1;",
      "boundaryField",
      "{",
      "    room",
      "    {",
      "        type		kqRWallFunction;",
      "        value		uniform 0.1;",
      "    }"
    ]
    for i in 1..vels.length do
      lines.push("    window_" + i.to_s)
      lines.push("    {")
      if vels[i - 1].length == 0
        lines.push("        type		inletOutlet;")
        lines.push("        inletValue		uniform 0.1;")
        lines.push("        value		uniform 0.1;")
      else
        lines.push("        type		fixedValue;")
        lines.push("        value		uniform 0.1;")
      end
      lines.push("    }")
    end
    lines.push("}")
    return lines.join("\n")
  end

  def self.generate_nut(vels)
    # Function:
    # Generates a OpenFOAM field file for the turbulent viscosity (nut) based on the number of velocity entries.
    # Constructs a configuration file with predefined header and boundary conditions, then appends
    # boundary patches for each window corresponding to the input velocity array.
    # 
    # Parameters:
    # vels : Array
    # An array representing velocity values, where each element corresponds to a window.
    # The length of this array determines how many 'window_' boundary patches are generated.
    # 
    # Returns:
    # String
    # A formatted string representing the complete nut field file content, with each line
    # separated by a newline character. The file includes FoamFile header, dimensions,
    # internal field, and boundary field definitions with appropriate boundary conditions.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		volScalarField;",
      "	location	\"0\";",
      "	object		nut;",
      "}",
      "dimensions		[0 2 -1 0 0 0 0];",
      "internalField		uniform 0;",
      "boundaryField",
      "{",
      "    room",
      "    {",
      "        type		nutkWallFunction;",
      "        value		uniform 0.01;",
      "    }"
    ]
    for i in 1..vels.length do
      lines.push("    window_" + i.to_s)
      lines.push("    {")
      lines.push("        type		calculated;")
      lines.push("        value		uniform 0;")
      lines.push("    }")
    end
    lines.push("}")
    return lines.join("\n")
  end

  def self.generate_p(vels)
    # Function:
    # Generates a string representation of a OpenFOAM field file (e.g., 'p') with specified boundary conditions
    # based on the presence of velocity data for each window. The file defines a scalar field with zeroGradient
    # or fixedValue boundary conditions depending on whether velocities are present.
    # 
    # Parameters:
    # vels : Array<Array<Numeric>>
    # A nested array where each sub-array corresponds to velocity data for a window.
    # If a sub-array is empty, it indicates no velocity data, leading to a fixedValue boundary condition
    # with value 0; otherwise, a zeroGradient condition is applied.
    # 
    # Returns:
    # String
    # A formatted string representing the complete OpenFOAM field file content,
    # with each line separated by a newline character. The output includes FoamFile header,
    # dimensions, internal field, and boundary field definitions with appropriate
    # boundary conditions for each window.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		volScalarField;",
      "	location	\"0\";",
      "	object		p;",
      "}",
      "dimensions		[0 2 -2 0 0 0 0];",
      "internalField		uniform 0;",
      "boundaryField",
      "{",
      "    room",
      "    {",
      "        type		zeroGradient;",
      "    }"
    ]
    for i in 1..vels.length do
      lines.push("    window_" + i.to_s)
      lines.push("    {")
      if vels[i - 1].length == 0
        lines.push("        type		fixedValue;")
        lines.push("        value		uniform 0;")
      else
        lines.push("        type		zeroGradient;")
      end
      lines.push("    }")
    end
    lines.push("}")
    return lines.join("\n")
  end

  def self.generate_U(vels)
    # Function:
    # Generates a string representation of a velocity field file (U) in OpenFOAM format based on given velocity values for windows.
    # 
    # Parameters:
    # vels : Array<Array<String>>
    # An array where each element is an array of strings representing velocity components (e.g., ["1.5", "0.0", "0.0"])
    # for each window boundary. If a sub-array is empty, the corresponding boundary uses inletOutlet type with zero velocity;
    # otherwise, it uses fixedValue with the specified uniform velocity.
    # 
    # Returns:
    # String
    # A formatted string representing the OpenFOAM velocity field file (U), including FoamFile header, dimensions,
    # internal field, and boundary field definitions for 'room' and dynamically named 'window_i' patches.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		volVectorField;",
      "	location	\"0\";",
      "	object		U;",
      "}",
      "dimensions		[0 1 -1 0 0 0 0];",
      "internalField		uniform (0 0 0);",
      "boundaryField",
      "{",
      "    room",
      "    {",
      "        type		fixedValue;",
      "        value		uniform (0 0 0);",
      "    }"
    ]
    for i in 1..vels.length do
      lines.push("    window_" + i.to_s)
      lines.push("    {")
      if vels[i - 1].length == 0
        lines.push("        type		inletOutlet;")
        lines.push("        inletValue		uniform (0 0 0);")
        lines.push("        value		uniform (0 0 0);")
      else
        lines.push("        type		fixedValue;")
        lines.push("        value		uniform (" + vels[i - 1] + ");")
      end
      lines.push("    }")
    end
    lines.push("}")
    return lines.join("\n")
  end

  def self.generate_stl(room, windows)
    # Function
    # --------
    # Generate an STL (Stereolithography) file content as a string representing a 3D room and its windows.
    # The output is formatted in ASCII STL format, defining solid objects with triangular facets,
    # including normal vectors and vertices for each triangle.
    # 
    # Parameters
    # ----------
    # room : Array of Array of String
    # A collection of triangular facets representing the geometry of the room.
    # Each element is an array containing three elements: [normal, vertex1, vertex2, vertex3],
    # where each vertex is a space-separated string of coordinates (e.g., "x y z"),
    # and normal is the unit normal vector of the triangle.
    # 
    # windows : Array of Array of Array of String
    # A nested collection where each sub-array represents the triangular facets of a window.
    # Structure is analogous to `room`, with each window containing multiple triangles,
    # each defined by a normal and three vertices.
    # 
    # Returns
    # -------
    # String
    # A single string containing the complete ASCII STL format representation of the room and all windows,
    # with each line separated by a newline character (`\n`). The room is named "solid room",
    # and each window is named sequentially as "solid window_1", "solid window_2", etc.
    lines = ["solid room"]
    for r in room do
      lines.push("  facet normal " + r[0])
      lines.push("    outer loop")
      lines.push("      vertex " + r[1])
      lines.push("      vertex " + r[2])
      lines.push("      vertex " + r[3])
      lines.push("    endloop")
      lines.push("  endfacet")
    end
    lines.push("endsolid room")
    for i in 1..windows.length do
      lines.push("solid window_" + i.to_s)
      for w in windows[i - 1] do
        lines.push("  facet normal " + w[0])
        lines.push("    outer loop")
        lines.push("      vertex " + w[1])
        lines.push("      vertex " + w[2])
        lines.push("      vertex " + w[3])
        lines.push("    endloop")
        lines.push("  endfacet")
      end
      lines.push("endsolid window_" + i.to_s)
    end
    return lines.join("\n")
  end

  def self.generate_g()
    # """
    # Function
    # --------
    # Generates a formatted string representing the gravity field file (g) for OpenFOAM.
    # 
    # This method constructs a list of strings that conform to the OpenFOAM FoamFile
    # format for a uniformDimensionedVectorField, specifically used to define gravitational
    # acceleration in simulation settings. The output is joined into a single string
    # with newline separators.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method with no parameters.
    # 
    # Returns
    # -------
    # str
    # A string containing the formatted OpenFOAM gravity field definition,
    # with each line separated by a newline character. The string includes
    # the FoamFile header, dimensions, and gravitational vector value (0 0 -9.81).
    # """
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		uniformDimensionedVectorField;",
      "	location	\"constant\";",
      "	object		g;",
      "}",
      "dimensions		[0 1 -2 0 0 0 0];",
      "value		(0 0 -9.81);"
    ]
    return lines.join("\n")
  end

  def self.generate_transportProperties()
    # Function:
    # Generates a formatted string representing OpenFOAM transportProperties dictionary.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: A newline-separated string containing the OpenFOAM transportProperties configuration,
    # including version, format, class, location, object name, and physical properties
    # such as transport model, kinematic viscosity (nu), thermal expansion coefficient (beta),
    # reference temperature (TRef), Prandtl number (Pr), turbulent Prandtl number (Prt),
    # and specific heat capacity (Cp0).
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"constant\";",
      "	object		transportProperties;",
      "}",
      "transportModel		Newtonian;",
      "nu		nu [0 2 -1 0 0 0 0] 1e-05;",
      "beta		beta [0 0 0 -1 0 0 0] 3e-03;",
      "TRef		TRef [0 0 0 1 0 0 0] 300;",
      "Pr		Pr [0 0 0 0 0 0 0] 0.9;",
      "Prt		Prt [0 0 0 0 0 0 0] 0.7;",
      "Cp0		1000;"
    ]
    return lines.join("\n")
  end

  def self.generate_turbulenceProperties()
    # Function
    # --------
    # Generates the content for the `turbulenceProperties` dictionary file used in OpenFOAM simulations.
    # This file specifies the turbulence model settings, including the simulation type, RAS (Reynolds-Averaged Simulation) model,
    # and associated parameters such as model enablement and coefficient output.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # String
    # A formatted string representing the `turbulenceProperties` dictionary, with each line separated by a newline character.
    # The string includes the FoamFile header, simulationType, and RAS model configuration using RNGkEpsilon.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"constant\";",
      "	object		turbulenceProperties;",
      "}",
      "simulationType		RAS;",
      "RAS",
      "{",
      "    RASModel		RNGkEpsilon;",
      "    turbulence		on;",
      "    printCoeffs		on;",
      "}"
    ]
    return lines.join("\n")
  end

  def self.generate_blockMeshDict(domain)
    # Function:
    # Generates the content of a blockMeshDict file used in OpenFOAM for defining a computational mesh block.
    # The method constructs a list of formatted strings representing the dictionary entries, including
    # vertices, blocks, edges, boundary patches, and merge patch pairs, based on the provided domain configuration.
    # 
    # Parameters:
    # domain : Array[String]
    # An array of 9 string values representing:
    # - domain[0] to domain[7]: Coordinates of the 8 vertices of the hexahedral block in (x y z) format.
    # - domain[8]: Mesh density as a tuple (nx ny nz) specifying the number of cells in each direction.
    # 
    # Returns:
    # String
    # A newline-separated string containing the complete blockMeshDict file content formatted according
    # to OpenFOAM's syntax, including FoamFile header, geometry definitions, block structure,
    # grading, boundary conditions, and empty mergePatchPair section.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		blockMeshDict;",
      "}",
      "convertToMeters 1;",
      "vertices",
      "(",
      "	(" + domain[0] + ")",
      "	(" + domain[1] + ")",
      "	(" + domain[2] + ")",
      "	(" + domain[3] + ")",
      "	(" + domain[4] + ")",
      "	(" + domain[5] + ")",
      "	(" + domain[6] + ")",
      "	(" + domain[7] + ")",
      ");",
      "blocks",
      "(",
      "hex (0 1 2 3 4 5 6 7) (" + domain[8] + ")",
      "simpleGrading (",
      "	1.0",
      "	1.0",
      "	1.0",
      "	)",
      ");",
      "edges",
      "(",
      ");",
      "boundary",
      "(   boundingbox",
      "   {",
      "       type wall;",
      "       faces",
      "       (",
      "	(0 3 2 1)",
      "	(4 5 6 7)",
      "	(1 2 6 5)",
      "	(3 0 4 7)",
      "	(0 1 5 4)",
      "	(2 3 7 6)",
      "       );",
      "   }",
      ");",
      "mergePatchPair",
      "(",
      ");"
    ]
    return lines.join("\n")
  end

  def self.generate_controlDict()
    # Function:
    # Generates a OpenFOAM control dictionary file (controlDict) as a formatted string.
    # This dictionary controls the simulation parameters such as start time, end time,
    # time step, output settings, and runtime modifiability for solvers like simpleFoam.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: A string representing the complete controlDict file content, with each line
    # separated by a newline character. The string includes the FoamFile header,
    # application settings, time control parameters, output configuration,
    # and function objects placeholder.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		controlDict;",
      "}",
      "application		simpleFoam;",
      "startFrom		latestTime;",
      "startTime		0;",
      "stopAt		endTime;",
      "endTime		1000;",
      "deltaT		1;",
      "writeControl		timeStep;",
      "writeInterval		1000;",
      "purgeWrite		0;",
      "writeFormat		ascii;",
      "writePrecision		7;",
      "writeCompression		off;",
      "timeFormat		general;",
      "timePrecision		6;",
      "runTimeModifiable		true;",
      "functions{}"
    ]
    return lines.join("\n")
  end

  def self.generate_decomposeParDict(number_parallel)
    # """
    # Function
    # --------
    # Generates the content of a decomposeParDict file used in OpenFOAM for parallel decomposition.
    # 
    # This method constructs a configuration file as a string that specifies parameters for domain decomposition,
    # enabling parallel execution in OpenFOAM simulations. The generated dictionary defines the number of subdomains
    # and the decomposition method.
    # 
    # Parameters
    # ----------
    # number_parallel : Integer
    # The number of parallel processes (subdomains) into which the computational domain will be divided.
    # Must be a positive integer.
    # 
    # Returns
    # -------
    # String
    # A formatted string representing the complete decomposeParDict file content, including FoamFile header,
    # numberOfSubdomains setting, and decomposition method (set to 'scotch').
    # """
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		decomposeParDict;",
      "}",
      "numberOfSubdomains " + number_parallel.to_s + ";",
      "method          scotch;"
    ]
    return lines.join("\n")
  end

  def self.generate_fvSchemes()
    # """
    # Function
    # --------
    # generate_fvSchemes
    # 
    # Generates a list of strings representing the OpenFOAM fvSchemes dictionary file content, which defines discretization schemes for numerical solution of partial differential equations in computational fluid dynamics simulations. The output is formatted as an OpenFOAM dictionary with standard schemes for ddt, gradient, divergence, Laplacian, interpolation, and surface normal gradient terms.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # String
    # A string containing the complete fvSchemes dictionary content with each line separated by newline characters. The string includes proper FoamFile header and scheme specifications for steady-state incompressible flow simulations, using bounded and limited schemes to ensure stability.
    # """
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		fvSchemes;",
      "}",
      "ddtSchemes",
      "{",
      "    default		steadyState;",
      "}",
      "gradSchemes",
      "{",
      "    default		cellLimited leastSquares 1;",
      "}",
      "divSchemes",
      "{",
      "    default		none;",
      "    div(phi,epsilon)		bounded Gauss linearUpwind grad(epsilon);",
      "    div(phi,U)		bounded Gauss linearUpwindV grad(U);",
      "    div((nuEff*dev2(T(grad(U)))))		Gauss linear;",
      "    div(phi,k)		bounded Gauss linearUpwind grad(k);",
      "}",
      "laplacianSchemes",
      "{",
      "    default		Gauss linear limited corrected 0.333;",
      "}",
      "interpolationSchemes",
      "{",
      "    default		linear;",
      "}",
      "snGradSchemes",
      "{",
      "    default		limited corrected 0.333;",
      "}",
      "fluxRequired",
      "{",
      "    default		no;",
      "}"
    ]
    return lines.join("\n")
  end

  def self.generate_fvSolution()
    # Function
    # --------
    # Generates the content of an OpenFOAM fvSolution configuration file as a newline-separated string.
    # This dictionary defines solver settings for different fields (e.g., pressure, velocity, turbulence)
    # and solution algorithms such as SIMPLE and relaxation factors used during the simulation.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # String
    # A formatted string representing the fvSolution file content, with each line separated by a newline character.
    # The content includes solver configurations for p, U, k, epsilon, SIMPLE algorithm settings,
    # and relaxation factors for stable convergence in CFD simulations.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		fvSolution;",
      "}",
      "solvers",
      "{",
      "    p",
      "    {",
      "        agglomerator		faceAreaPair;",
      "        relTol		0.1;",
      "        tolerance		1e-6;",
      "        nCellsInCoarsestLevel		10;",
      "        smoother		GaussSeidel;",
      "        solver		GAMG;",
      "        cacheAgglomeration		on;",
      "        nPostSweeps		2;",
      "        nPreSweepsre		0;",
      "        mergeLevels		1;",
      "    }",
      "    U",
      "    {",
      "        relTol		0.1;",
      "        tolerance		1e-6;",
      "        nSweeps		1;",
      "        smoother		GaussSeidel;",
      "        solver		smoothSolver;",
      "    }",
      "    k",
      "    {",
      "        relTol		0.1;",
      "        tolerance		1e-6;",
      "        nSweeps		1;",
      "        smoother		GaussSeidel;",
      "        solver		smoothSolver;",
      "    }",
      "    epsilon",
      "    {",
      "        relTol		0.1;",
      "        tolerance		1e-6;",
      "        nSweeps		1;",
      "        smoother		GaussSeidel;",
      "        solver		smoothSolver;",
      "    }",
      "}",
      "SIMPLE",
      "{",
      "    nNonOrthogonalCorrectors		2;",
      "    residualControl",
      "    {",
      "        nut		0.0001;",
      "        k		0.0001;",
      "        U		0.0001;",
      "        p		0.0001;",
      "        epsilon		0.0001;",
      "    }",
      "}",
      "relaxationFactors",
      "{",
      "    k		0.7;",
      "    U		0.7;",
      "    epsilon		0.7;",
      "    p		0.3;",
      "}"
    ]
    return lines.join("\n")
  end

  def self.generate_snappyHexMeshDict(win_num, locationInMesh)
    # Function
    # --------
    # Generates the content of a `snappyHexMeshDict` file used in OpenFOAM for mesh generation,
    # configuring parameters for castellated meshing, snapping, layer addition, and mesh quality control.
    # The method dynamically includes window regions based on input count and sets the locationInMesh point.
    # 
    # Parameters
    # ----------
    # win_num : Integer
    # The number of windows to include in the geometry and refinement surfaces.
    # Used to generate entries for each window (e.g., window_1, window_2, ...) in both the geometry
    # and refinementSurfaces sections.
    # 
    # locationInMesh : String
    # A string representing the coordinates (in vector format, e.g., "1 2 3") of a point inside
    # the fluid region, required by snappyHexMesh to determine which cells to keep during meshing.
    # 
    # Returns
    # -------
    # String
    # A formatted string containing the complete `snappyHexMeshDict` dictionary content,
    # with each configuration line separated by a newline character (`\n`). This output is suitable
    # for direct writing to the system/snappyHexMeshDict file in an OpenFOAM case directory.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		snappyHexMeshDict;",
      "}",
      "castellatedMesh		true;",
      "snap		false;",
      "addLayers		false;",
      "geometry",
      "{",
      "    indoor_airflow.stl",
      "    {",
      "        type		triSurfaceMesh;",
      "        name		indoor_airflow;",
      "        regions",
      "        {",
      "            room",
      "            {",
      "                name		room;",
      "            }"
    ]
    for i in 1..win_num do
      lines.push("            window_" + i.to_s)
      lines.push("            {")
      lines.push("                name		window_" + i.to_s + ";")
      lines.push("            }")
    end
    lines.push("        }")
    lines.push("    }")
    lines.push("}")
    lines.push("castellatedMeshControls")
    lines.push("{")
    lines.push("    maxLocalCells		1000000;")
    lines.push("    maxGlobalCells		2000000;")
    lines.push("    minRefinementCells		10;")
    lines.push("    maxLoadUnbalance		0.10;")
    lines.push("    nCellsBetweenLevels		3;")
    lines.push("    features		({file \"indoor_airflow.eMesh\"; level 0;} );")
    lines.push("    refinementSurfaces")
    lines.push("    {")
    lines.push("        indoor_airflow")
    lines.push("        {")
    lines.push("            level		(0 0);")
    lines.push("            regions")
    lines.push("            {")
    for i in 1..win_num do
      lines.push("                window_" + i.to_s)
      lines.push("                {")
      lines.push("                    level		(2 2);")
      lines.push("                }")
    end
    lines.push("            }")
    lines.push("        }")
    lines.push("    }")
    lines.push("    resolveFeatureAngle		95;")
    lines.push("    refinementRegions{}")
    lines.push("    locationInMesh		(" + locationInMesh + ");")
    lines.push("    allowFreeStandingZoneFaces		true;")
    lines.push("}")
    lines.push("snapControls")
    lines.push("{")
    lines.push("    nSmoothPatch		5;")
    lines.push("    tolerance		5;")
    lines.push("    nSolveIter		100;")
    lines.push("    nRelaxIter		8;")
    lines.push("    nFeatureSnapIter		10;")
    lines.push("    extractFeaturesRefineLevel		true;")
    lines.push("    explicitFeatureSnap		true;")
    lines.push("}")
    lines.push("addLayersControls")
    lines.push("{")
    lines.push("    relativeSizes		true;")
    lines.push("    layers{}")
    lines.push("    expansionRatio		1.1;")
    lines.push("    finalLayerThickness		0.7;")
    lines.push("    minThickness		0.1;")
    lines.push("    nGrow		0;")
    lines.push("    featureAngle		110;")
    lines.push("    nRelaxIter		3;")
    lines.push("    nSmoothSurfaceNormals		1;")
    lines.push("    nSmoothThickness		10;")
    lines.push("    nSmoothNormals		3;")
    lines.push("    maxFaceThicknessRatio		0.5;")
    lines.push("    maxThicknessToMedialRatio		0.3;")
    lines.push("    minMedianAxisAngle		130;")
    lines.push("    nBufferCellsNoExtrude		0;")
    lines.push("    nLayerIter		50;")
    lines.push("    nRelaxedIter		20;")
    lines.push("}")
    lines.push("meshQualityControls")
    lines.push("{")
    lines.push("    maxNonOrtho		60;")
    lines.push("    maxBoundarySkewness		20;")
    lines.push("    maxInternalSkewness		4;")
    lines.push("    maxConcave		80;")
    lines.push("    minFlatness		0.5;")
    lines.push("    minVol		1e-13;")
    lines.push("    minTetQuality		1e-15;")
    lines.push("    minArea		-1;")
    lines.push("    minTwist		0.02;")
    lines.push("    minDeterminant		0.001;")
    lines.push("    minFaceWeight		0.02;")
    lines.push("    minVolRatio		0.01;")
    lines.push("    minTriangleTwist		-1;")
    lines.push("    nSmoothScale		4;")
    lines.push("    errorReduction		0.75;")
    lines.push("    relaxed")
    lines.push("    {")
    lines.push("        maxNonOrtho		75;")
    lines.push("    }")
    lines.push("}")
    lines.push("debug		0;")
    lines.push("mergeTolerance		1E-6;")
    return lines.join("\n")
  end

  def self.generate_surfaceFeatureExtractDict()
    # Function:
    # Generates a string representation of a surfaceFeatureExtractDict file used in OpenFOAM for defining parameters to extract features from a surface geometry.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: A newline-separated string containing the formatted dictionary entries for surface feature extraction configuration in OpenFOAM.
    lines = [
      "FoamFile",
      "{",
      "	version		4.0;",
      "	format		ascii;",
      "	class		dictionary;",
      "	location	\"system\";",
      "	object		surfaceFeatureExtractDict;",
      "}",
      "indoor_airflow.stl",
      "{",
      "    extractionMethod		extractFromSurface;",
      "    extractFromSurfaceCoeffs",
      "    {",
      "        includedAngle		150;",
      "        geometricTestOnly		on;",
      "    }",
      "    writeObj		off;",
      "}"
    ]
    return lines.join("\n")
  end

end

class FoamUtil

  def self.calculate_deflection(bounds)
    # """
    # Function
    # --------
    # calculate_deflection
    # Calculates the deflection angle based on the orientation of boundary normals.
    # Iterates through given bounds and returns the first orientation value that is
    # within 45 degrees of the positive x-axis (i.e., <= 45 or >= 315 degrees).
    # If no such orientation is found, returns 0.
    # 
    # Parameters
    # ----------
    # bounds : Array
    # An array of boundary objects, each expected to have a `normal` attribute
    # representing the surface normal vector used to compute orientation.
    # 
    # Returns
    # -------
    # Integer or Float
    # The orientation angle in degrees of the first boundary whose orientation
    # is within the acceptable deflection range (<= 45 or >= 315), or 0 if none
    # meet the condition.
    # """
    bounds.each do |b|
      o = self.calculate_orientation(b.normal)
      if o <= 45 or o >= 315
        return o
      end
    end
    return 0
  end

  def self.calculate_orientation(n)
    # """
    # Function
    # --------
    # calculate_orientation :
    # Calculates the orientation angle (in degrees) of a 2D vector `n` with respect to the negative x-axis,
    # measured clockwise from 0 to 360 degrees. The result is adjusted based on the quadrant in which the vector lies.
    # 
    # Parameters
    # ----------
    # n : Array[Numeric]
    # A two-element array representing a 2D vector, where `n[0]` is the x-component and `n[1]` is the y-component.
    # 
    # Returns
    # -------
    # Numeric
    # The orientation angle in degrees, ranging from 0 to 360.
    # The angle is computed counterclockwise from the negative x-axis, then converted to a clockwise bearing.
    # If the resulting angle is exactly 360, it is normalized to 0.
    # """
    o = Math.acos((-1) * (n[0]) / Math.sqrt((n[0]) ** 2 + (n[1]) ** 2)) * 180 / Math::PI
    if n[1] > 0
      o = 360 - o
    end
    if o == 360
      o = 0
    end
    return o
  end

  def self.coordinate_index(normal)
    # """
    # Function:
    # Determines the indices of the two coordinate axes perpendicular to the dominant axis
    # based on the absolute values of a 3D normal vector. The dominant axis is defined as
    # the one with the maximum absolute component in the normal vector.
    # 
    # Parameters:
    # normal : Array<Numeric>
    # A 3-element array representing a normal vector [x, y, z]. The method uses the
    # absolute values of these components to determine the dominant axis.
    # 
    # Returns:
    # Array<Integer>
    # A 2-element array containing the indices of the two non-dominant coordinate axes,
    # ordered such that they are perpendicular to the dominant axis. Specifically:
    # - Returns [1, 2] if the x-axis (index 0) is dominant,
    # - Returns [0, 2] if the y-axis (index 1) is dominant,
    # - Returns [0, 1] if the z-axis (index 2) is dominant.
    # """
    n = [normal[0].abs, normal[1].abs, normal[2].abs]
    z = n.index(n.max)
    if z == 0
      return [1, 2]
    elsif z == 1
      return [0, 2]
    else
      return [0, 1]
    end
  end

  def self.delaunay_triangulation(input)
    # """
    # Function
    # ----------
    # Performs Delaunay triangulation on a given input using an external executable.
    # 
    # This method writes the input to a file, invokes an external triangulation program
    # (triangulate.exe), and reads the resulting triangulation output. It then parses
    # the output into an array of triangles, where each triangle is represented by three
    # vertex indices.
    # 
    # Parameters
    # ----------
    # input : str
    # A string representing the input data for the triangulation process.
    # This typically contains point coordinates or related geometric data
    # formatted as expected by the external 'triangulate.exe' program.
    # 
    # Returns
    # -------
    # list of list of int
    # A list of triangles, where each triangle is a list of three integers
    # representing the indices of the vertices that form the triangle.
    # The vertex indices are derived from the input point set.
    # """
    pwd = MPath::VENT + "triangulate"
    Dir.chdir pwd
    File.write("triangulate.input", input)
    system("triangulate.exe")
    output = []
    File.open("triangulate.output", "r") do |file|
      output = file.gets.split(",")
    end
    triangle_num = output.length / 3
    triangles = []
    for i in 0..triangle_num - 1 do
      p1 = output[i * 3 + 0].to_i
      p2 = output[i * 3 + 1].to_i
      p3 = output[i * 3 + 2].to_i
      triangle = [p1, p2, p3]
      triangles.push(triangle)
    end
    return triangles
  end

  def self.calculate_midpoint(vertices)
    # Function:
    # Calculates the midpoint of a set of 3D vertices by averaging their positions,
    # converting from inches to centimeters, and returns the result as a comma-separated string.
    # 
    # Parameters:
    # vertices : Array<Vertex>
    # An array of vertex objects, each having a `position` attribute that is a 3-element array-like
    # structure containing x, y, z coordinates in inches.
    # 
    # Returns:
    # String
    # A comma-separated string representing the averaged (x, y, z) coordinates of the input vertices
    # in centimeters, with each coordinate rounded to the nearest integer. Format: "x,y,z".
    c, x, y, z = 0, 0, 0, 0
    vertices.each do |v|
      c += 1
      x += v.position[0].to_f * 2.54
      y += v.position[1].to_f * 2.54
      z += v.position[2].to_f * 2.54
    end
    return (x / c).round.to_s + "," + (y / c).round.to_s + "," + (z / c).round.to_s
  end

end
