class MoosasFoam
    Ver='0.6.3'

    @room = []
    @domain = []
    @windows = []
    @vels = []

    def self.analysis()
        t1 = Time.new
        # 输入所选空间、网格大小（默认为0.5m）和并行数量（默认为4核）
        ach = airflow_simulation($current_model.spaces[$space_select_index], 0.5, 4)
        t2 = Time.new
        if ach
            p "CFD模拟用时： #{t2-t1}s"
        else
            p 'CFD模拟出错.请检查'
        end
        #调用paraView可视化
        self.view()
    end

    def self.airflow_simulation(space, grid_size, number_parallel)
        if not Dir.exist?("C:\\Program Files\\blueCFD-Core-2017\\")
            UI.messagebox("blueCFD not found in C:\\Program Files\\blueCFD-Core-2017\\.\nPlease check the installation of blueCFD or download from:\nhttp://bluecfd.github.io/Core/Downloads/#bluecfd-core-2017-1")
            return false
        # 判断空间是否合法
        #elif not space.is_outer
        #    UI.messagebox("所选空间非外区")
        #    return false
        #elsif space.ceils.length != 1
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
        File.open(MPath::VENT+ "airVel","r") do |file|
            while line = file.gets
                av = line.split("|")
                airVel[av[0]] = av[1].to_f
            end
        end
        # 将MoosasSpace转换为stl（外窗独立）
        space.ceils.each{|ceiling| self.input_room(ceiling.face.vertices, ceiling.normal)}
        space.floor.each{|floor| self.input_room(floor.face.vertices, floor.normal)}

        space.bounds.each do |b|
            #if b.walls.length != 1
            #    UI.messagebox("外立面设计错误")
            #    return
            #end
            if b.glazings.length == 0 # 无门窗的立面
                self.input_room(b.walls[0].face.vertices, b.normal)
            else # 有门窗的立面
                self.input_windows(b.walls[0], b.glazings, b.normal)
                vertices_=[]
                space.floor.each{|fl| fl.face.vertices.each{|ver| vertices_.push(ver)}}
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
            for i in 0..win_num-1
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
        nx, ny = n[0] / Math.sqrt((n[0])**2 + (n[1])**2), n[1] / Math.sqrt((n[0])**2 + (n[1])**2)
        glazings.each do |g|
            vel = airVel[prefix + "," + FoamUtil.calculate_midpoint(g.face.vertices)]
            if vel < 0 # 进风口
                @vels.push((vel * nx).round(2).to_s + " " + (vel * ny).round(2).to_s + " 0.0")
            else # 出风口
                @vels.push("")
            end
        end
    end

    def self.output_domain(grid_size)
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
        pwd = MPath::VENT+ "mkdir/"
        Dir.chdir pwd
        File.write("mkdir.input", MPath::DATA+ "vent/foam/")
        system("mkdir.exe")
    end

    def self.generate_0()
        path =MPath::DATA+ "vent/foam/0/"
        win_num = @windows.length
        File.write(path + "epsilon", FoamFile.generate_epsilon(@vels))
        File.write(path + "k", FoamFile.generate_k(@vels))
        File.write(path + "nut", FoamFile.generate_nut(@vels))
        File.write(path + "p", FoamFile.generate_p(@vels))
        File.write(path + "U", FoamFile.generate_U(@vels))
    end

    def self.generate_constant()
        path = MPath::DATA+ "vent/foam/constant/"
        File.write(path + "triSurface/indoor_airflow.stl", FoamFile.generate_stl(@room, @windows))
        File.write(path + "g", FoamFile.generate_g())
        File.write(path + "transportProperties", FoamFile.generate_transportProperties())
        File.write(path + "turbulenceProperties", FoamFile.generate_turbulenceProperties())
    end

    def self.generate_system(grid_size, number_parallel)
        domain = self.output_domain(grid_size)
        path =  MPath::DATA+ "vent/foam/system/"
        File.write(path + "blockMeshDict", FoamFile.generate_blockMeshDict(domain))
        File.write(path + "controlDict", FoamFile.generate_controlDict())
        File.write(path + "decomposeParDict", FoamFile.generate_decomposeParDict(number_parallel))
        File.write(path + "fvSchemes", FoamFile.generate_fvSchemes())
        File.write(path + "fvSolution", FoamFile.generate_fvSolution())
        File.write(path + "snappyHexMeshDict", FoamFile.generate_snappyHexMeshDict(@windows.length, domain[0]))
        File.write(path + "surfaceFeatureExtractDict", FoamFile.generate_surfaceFeatureExtractDict())
    end

    def self.run(number_parallel)
        lines = [
            "call \"C:\\Program Files\\blueCFD-Core-2017\\setvars.bat\"",
            "set PATH=%HOME%\\msys64\\usr\\bin;%PATH%",
        ]
        pwd = MPath::DATA+ "vent/"
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
        pwd = MPath::DATA+ "vent/"
        Dir.chdir pwd
        path = pwd + "view.bat"
        File.write(path, "vent.foam")
        system("view.bat")
    end

end

class FoamFile

    def self.generate_epsilon(vels)
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
            if vels[i-1].length == 0
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
            if vels[i-1].length == 0
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
            if vels[i-1].length == 0
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
            if vels[i-1].length == 0
                lines.push("        type		inletOutlet;")
                lines.push("        inletValue		uniform (0 0 0);")
                lines.push("        value		uniform (0 0 0);")
            else
                lines.push("        type		fixedValue;")
                lines.push("        value		uniform (" + vels[i-1] + ");")
            end
            lines.push("    }")
        end
        lines.push("}")
        return lines.join("\n")
    end

    def self.generate_stl(room, windows)
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
            for w in windows[i-1] do
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
        bounds.each do |b|
            o = self.calculate_orientation(b.normal)
            if o <= 45 or o >= 315
                return o
            end
        end
        return 0
    end

    def self.calculate_orientation(n)
        o = Math.acos((-1)*(n[0])/Math.sqrt((n[0])**2+(n[1])**2))*180/Math::PI
        if n[1] > 0
            o = 360-o
        end
        if o == 360
            o = 0
        end
        return o
    end

    def self.coordinate_index(normal)
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
        pwd = MPath::VENT + "triangulate"
        Dir.chdir pwd
        File.write("triangulate.input", input)
        system("triangulate.exe")
        output = []
        File.open("triangulate.output","r") do |file|
            output = file.gets.split(",")
        end
        triangle_num = output.length/3
        triangles = []
        for i in 0..triangle_num-1 do
            p1 = output[i*3+0].to_i
            p2 = output[i*3+1].to_i
            p3 = output[i*3+2].to_i
            triangle = [p1, p2, p3]
            triangles.push(triangle)
        end
        return triangles
    end

    def self.calculate_midpoint(vertices)
        c, x, y ,z = 0, 0, 0, 0
        vertices.each do |v|
            c += 1
            x += v.position[0].to_f * 2.54
            y += v.position[1].to_f * 2.54
            z += v.position[2].to_f * 2.54
        end
        return (x / c).round.to_s + "," + (y / c).round.to_s + "," + (z / c).round.to_s
    end

end
