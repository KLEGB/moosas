package main

import (
	"fmt"
	"io"
	"log"
	"math"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type airFlowNetwork struct {
	zones []zone
	paths []flowPath
}

type zone struct {
	volume      float64
	row         int
	col         int
	hei         int
	points      [][]int
	prjname     string
	username    string
	heat        float64
	temperature float64
}

type flowPath struct {
	username string
	height   float64
	width    float64
	row      int
	col      int
	hei      int
	from     int
	to       int
	pressure float64
}

type globalInfo struct {
	networkFile string
	directory   string
	prjName     string
	resultFile  string
	simulation  bool
	split       bool
	t0          string
}

func help() {
	fmt.Println("Moosas ContamX Builder and reader.")
	fmt.Println("Command line should be: MoosasAFN.exe [-h,-p...] inputNetworkFile.net")
	fmt.Println("Optional command:")
	fmt.Println("-h / -help : reprint the help information")
	fmt.Println("-p / -project : base name of the prj file  (default: network)")
	fmt.Println("-d / -directory : directory where the project file and result to put  (default: execution directory)")
	fmt.Println("-o / -output : result output file path (default: execution directory\\airVel.o)")
	fmt.Println("-r / -run : 1 if run contamX for all built *.prj files and gather the results (default: 0)")
	fmt.Println("-s / -split : 1 if split the input network into several networks (default: 1)")
	fmt.Println("-t / -t0 : OutdoorTemperature (default: 25)")
}

func main() {
	exePath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}
	res, _ := filepath.EvalSymlinks(filepath.Dir(exePath))

	info := globalInfo{
		networkFile: "",
		directory:   res,
		prjName:     "network_",
		resultFile:  res + "\\airVel.o",
		simulation:  false,
		split:       true,
		t0:          "298.15",
	}

	for i := 1; i < len(os.Args); {
		if os.Args[i] == "-h" || os.Args[i] == "-help" {
			help()
			return
		}
		if os.Args[i] == "-p" || os.Args[i] == "-project" {
			info.prjName = os.Args[i+1]
		}
		if os.Args[i] == "-o" || os.Args[i] == "-output" {
			info.resultFile, _ = filepath.Abs(os.Args[i+1])
		}
		if os.Args[i] == "-r" || os.Args[i] == "-run" {
			info.simulation = os.Args[i+1] == "1"
		}
		if os.Args[i] == "-s" || os.Args[i] == "-split" {
			info.split = os.Args[i+1] == "1"
		}
		if os.Args[i] == "-t" || os.Args[i] == "-t0" {
			t, _ := strconv.ParseFloat(os.Args[i+1], 64)
			if t < 273.15 {
				t += 273.15
			}
			info.t0 = strconv.FormatFloat(t, 'f', 2, 64)
		}
		if os.Args[i] == "-d" || os.Args[i] == "-directory" {
			info.directory, _ = filepath.Abs(os.Args[i+1])
		}
		i++
	}

	info.networkFile, _ = filepath.Abs(os.Args[len(os.Args)-1])
	fileInfo, err := os.Lstat(info.networkFile)
	if err != nil {
		fmt.Println("invalid inputFile. Please check:", info.networkFile)
	} else {
		mode := fileInfo.Mode()
		if mode.IsRegular() {

			//Working here
			prjFilePath := make([]string, 0)
			networks := []airFlowNetwork{readFile(info.networkFile)}
			if info.split {
				networks = splitPaths(networks[0])
				for i, network := range networks {
					zoneFile := networkToFile(info.prjName+strconv.Itoa(i)+".net", info, network)
					fmt.Println("create such networkFile:", zoneFile)
					prjFile := generatePrj(info.prjName+strconv.Itoa(i)+".prj", info, network)
					prjFilePath = append(prjFilePath, prjFile)
					fmt.Println("create such prjFile:", prjFile)
				}
			} else {
				prjFile := generatePrj(info.prjName+".prj", info, networks[0])
				prjFilePath = append(prjFilePath, prjFile)
				fmt.Println("create such prjFile:", prjFile)
			}

			if info.simulation {
				runContamX(prjFilePath, networks, info.resultFile)
				fmt.Println("create such result:", info.resultFile)
			}

		} else {
			fmt.Println("inputFile flowPath is not a file. Please check:", info.networkFile)
		}
	}
}

// top Func
func runContamX(prjFilePath []string, networks []airFlowNetwork, resultFile string) {
	resultStr := ""

	// run simulation
	for i := 0; i < len(networks); i++ {
		lfrFile := callContam(networks[i], prjFilePath[i])
		resultStr += outputResults(networks[i], lfrFile)
	}

	// export result
	os.Remove(resultFile)
	file, _ := os.Create(resultFile)
	io.WriteString(file, resultStr)
}

// top Func
func readFile(zoneFile string) airFlowNetwork {
	//------------------------------------------------------

	//The network file can be decoded like this:
	//! All line with the prefix "!" are annotations and will be ignored.
	//! Zone Data or Path Data are identified be the length of the line, so dont worry about that.
	//! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon (len==9)
	//Bedroom0, z01, 1760, 27, 180, 16.2, 18.5, 3.0, 16.2 18.5 20.2 18.5 20.2 23.5 16.2 23.5
	//....
	//! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure (len==10)
	//BedroomWin0, p01, 1.8, 1.2, 17.4, 19.1, 3.6, -1, 2, 12.5
	//....
	//------------------------------------------------------
	input0, _ := os.ReadFile(zoneFile)
	input1 := strings.Split(string(input0), "\r\n")
	zoneStrList, pathStrList := make([][]string, 0), make([][]string, 0)
	for i := 0; i < len(input1); i++ {
		if !strings.HasPrefix(input1[i], "!") {
			arr := strings.Split(input1[i], ",")
			if len(arr) == 9 {
				zoneStrList = append(zoneStrList, arr)
			}
			if len(arr) == 10 {
				pathStrList = append(pathStrList, arr)
			}
		}

	}

	// read zone
	// ! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon (len==9)
	zones := make([]zone, len(zoneStrList))
	for i := 0; i < len(zoneStrList); i++ {
		heatload, _ := strconv.ParseFloat(zoneStrList[i][2], 64)
		temperature, _ := strconv.ParseFloat(zoneStrList[i][3], 64)
		if temperature < 273.15 {
			temperature += 273.15
		}
		volume, _ := strconv.ParseFloat(zoneStrList[i][4], 64)
		points := [][]int{}
		pointstring := strings.Split(zoneStrList[i][8], " ")
		for i := 0; i < len(pointstring)/2; i++ {
			pointRow := _MtoCM(pointstring[i*2+0])
			pointCol := _MtoCM(pointstring[i*2+1])
			points = append(points, []int{pointRow, pointCol})
		}
		zones[i] = zone{
			username:    zoneStrList[i][0],
			prjname:     zoneStrList[i][1],
			volume:      volume,
			temperature: temperature,
			heat:        heatload,
			row:         _MtoCM(zoneStrList[i][5]),
			col:         _MtoCM(zoneStrList[i][6]),
			hei:         _MtoCM(zoneStrList[i][7]),
			points:      points,
		}
	}

	// read flowPath
	// ! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure (len==10)
	paths := make([]flowPath, len(pathStrList))
	for i := 0; i < len(pathStrList); i++ {
		//pathIndex, _ := strconv.ParseFloat(pathStrList[i][1], 64)
		height, _ := strconv.ParseFloat(pathStrList[i][2], 64)
		width, _ := strconv.ParseFloat(pathStrList[i][3], 64)
		from, _ := strconv.Atoi(pathStrList[i][7])
		to, _ := strconv.Atoi(pathStrList[i][8])
		pressure, _ := strconv.ParseFloat(pathStrList[i][9], 64)
		paths[i] = flowPath{
			pathStrList[i][0],
			height,
			width,
			_MtoCM(pathStrList[i][4]),
			_MtoCM(pathStrList[i][5]),
			_MtoCM(pathStrList[i][6]),
			from,
			to,
			pressure,
		}
	}

	return airFlowNetwork{zones, paths}
}

func networkToFile(zonFileBaseMame string, info globalInfo, network airFlowNetwork) string {
	networkStr := "! All annotations has prefix as !\n"
	networkStr += "! ZONE DATA\n"
	networkStr += "! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon (len==9)\n"
	for _, z := range network.zones {
		networkStr += z.username + "," +
			z.prjname + "," +
			fmt.Sprintf("%.2f", z.heat) + "," +
			fmt.Sprintf("%.2f", z.temperature) + "," +
			fmt.Sprintf("%.2f", z.volume) + "," +
			fmt.Sprintf("%.2f", float64(z.row)/100.0) + "," +
			fmt.Sprintf("%.2f", float64(z.col)/100) + "," +
			fmt.Sprintf("%.2f", float64(z.hei)/100) + ","
		pointStr := ""
		for _, p := range z.points {
			pointStr += fmt.Sprintf("%.2f", float64(p[0])/100) + " " + fmt.Sprintf("%.2f", float64(p[1])/100) + " "
		}
		networkStr += pointStr[0:len(pointStr)-1] + "\n"
	}
	networkStr += "! PATH DATA\n"
	networkStr += "! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure (len==10)\n"
	for i, p := range network.paths {
		networkStr += p.username + "," +
			"p" + strconv.Itoa(i) + "," +
			fmt.Sprintf("%.2f", p.height) + "," +
			fmt.Sprintf("%.2f", p.width) + "," +
			fmt.Sprintf("%.2f", float64(p.row)/100.0) + "," +
			fmt.Sprintf("%.2f", float64(p.col)/100.0) + "," +
			fmt.Sprintf("%.2f", float64(p.hei)/100.0) + "," +
			strconv.Itoa(p.from) + "," +
			strconv.Itoa(p.to) + "," +
			fmt.Sprintf("%.2f", p.pressure) + "\n"
	}

	os.Remove(path.Join(info.directory, zonFileBaseMame))
	// os.RemoveAll(prjDictionary)
	// os.Mkdir(prjDictionary, os.ModePerm)
	file, _ := os.Create(path.Join(info.directory, zonFileBaseMame))
	io.WriteString(file, networkStr)
	//return pathList
	return path.Join(info.directory, zonFileBaseMame)
}

// top Func
func generatePrj(prjBaseName string, info globalInfo, network airFlowNetwork) string {
	iconList := getIconList(network)
	zones := network.zones
	lines := []string{
		"ContamW 3.4.0.4 0",
		"afn",
		"! rows cols ud uf    T   uT     N     wH  u  Ao    a",
		"    58   66  0  0 " + info.t0 + " 2    0.00 10.00 0 0.600 0.280",
		"!  scale     us  orgRow  orgCol  invYaxis showGeom",
		"  1.000e+00   0      56       1     0        0",
		"! Ta       Pb      Ws    Wd    rh  day u..",
		info.t0 + " 101325.0  0.000   0.0 0.000 1 2 0 0 1 ! steady simulation",
		info.t0 + " 101325.0  1.000 270.0 0.000 1 2 0 0 1 ! wind pressure test",
		"null ! no weather file",
		"null ! no contaminant file",
		"null ! no continuous values file",
		"null ! no discrete values file",
		"null ! no WPC file",
		"null ! no EWC file",
		"WPC description",
		"!  Xref    Yref    Zref   angle u",
		"   0.000   0.000   0.000   0.00 0",
		"! epsP epsS  tShift  dStart dEnd wp mf wpctrig",
		"  0.01 0.01 00:00:00   1/1   1/1  0  0  0",
		"! latd  longtd   tznr  altd  Tgrnd u..",
		" 40.00  -90.00  -6.00     0 283.15 2 0",
		"!sim_af afcalc afmaxi afrcnvg afacnvg afrelax uac Pbldg uPb",
		"     0      1     30   1e-05   1e-06    0.75   0 50.00   0",
		"!   slae rs aflmaxi aflcnvg aflinit Tadj",
		"      0   1    100   1e-06      1    0",
		"!sim_mf slae rs maxi   relcnvg   abscnvg relax gamma ucc",
		"    0             30  1.00e-04  1.00e-15 1.250         0 ! (cyclic)",
		"          0   1  100  1.00e-06  1.00e-15 1.100 1.000   0 ! (non-trace)",
		"          0   1  100  1.00e-06  1.00e-15 1.100 1.000   0 ! (trace)",
		"          0   1  100  1.00e-06  1.00e-15 1.100         0 ! (cvode)",
		"!mf_solver sim_1dz sim_1dd   celldx  sim_vjt udx",
		"     0        1       0     1.00e-01    0     0",
		"!cvode    rcnvg     acnvg    dtmax",
		"   0     1.00e-06  1.00e-13   0.00",
		"!tsdens relax tsmaxi cnvgSS densZP stackD dodMdt",
		"   0    0.75    20     1      0      0      0",
		"!date_st time_st  date_0 time_0   date_1 time_1    t_step   t_list   t_scrn",
		"  Jan01 00:00:00  Jan01 00:00:00  Jan01 24:00:00  00:05:00 01:00:00 01:00:00",
		"!restart  date  time",
		"    0    Jan01 00:00:00",
		"!list doDlg pfsave zfsave zcsave",
		"   1     1      1      1      1",
		"!vol ach -bw cbw exp -bw age -bw",
		"  0   0   0   0   0   0   0   0",
		"!rzf rzm rz1 csm srf log",
		"  0   0   0   1   1   1",
		"!bcx dcx pfq zfq zcq",
		"  0   0   0   0   0",
		"!dens   grav",
		" 1.2041 9.8055",
		"! 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 <- extra[]",
		"  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0",
		"0 ! rvals:",
		"!valZ valD valC",
		"   0    0    0",
		"!cfd   cfdcnvg  var zref maxi dtcmo solv smooth   cnvgUVW     cnvgT",
		"   0  1.00e-02    0    0 1000     1    1      1  1.00e-03  1.00e-03",
		"-999",
		"0 ! contaminants:",
		"0 ! species:",
		"-999",
		"1 ! levels plus icon data:",
		"! #  refHt   delHt  ni  u  name",
		"  1   0.000   3.000 " + strconv.Itoa(len(iconList)) + " 0 0 <1>",
		"!icn col row  #",
	}
	for _, icon := range iconList {
		icn, col, row, index := strconv.Itoa(icon[0]), strconv.Itoa(icon[1]), strconv.Itoa(icon[2]), strconv.Itoa(icon[3])
		lines = append(lines, "  "+icn+"  "+col+"  "+row+"  "+index)
	}

	lines = append(lines, []string{
		"-999",
		"0 ! day-schedules:",
		"-999",
		"0 ! week-schedules:",
		"-999",
		"0 ! wind pressure profiles:",
		"-999",
		"0 ! kinetic reactions:",
		"-999",
		"0 ! filter elements",
		"-999",
		"0 ! filters:",
		"-999",
		"0 ! source/sink elements:",
		"-999",
		strconv.Itoa(len(network.paths)) + " ! flow elements:",
	}...)
	for i, p := range network.paths {
		h, w := p.height, p.width
		lam := fmt.Sprintf("%.6f", h*w*h*w/(h+w)*0.02028)
		turb := fmt.Sprintf("%.6f", h*w*0.551543)
		dh := fmt.Sprintf("%.6f", h*0.222222)
		hd := strconv.FormatFloat(h, 'f', 2, 64)
		wd := strconv.FormatFloat(w, 'f', 2, 64)
		lines = append(lines, []string{
			strconv.Itoa(i+1) + " 27 dor_pl2 p" + strconv.Itoa(i+1),
			"",
			" " + lam + " " + turb + " 0.5 " + dh + " " + hd + " " + wd + " 0.78 0 0",
		}...)
	}
	lines = append(lines, []string{
		"-999",
		"0 ! duct elements:",
		"-999",
		"0 ! control super elements:",
		"-999",
		"0 ! control nodes:",
		"-999",
		"0 ! simple AHS:",
		"-999",
		strconv.Itoa(len(network.zones)) + " ! zones:",
		"! Z#  f  s#  c#  k#  l#  relHt    Vol  T0  P0  name  clr uH uT uP uV axs cdvf <cdvfName> cfd <cfdName> <1dData:>",
	}...)
	for i, z := range network.zones {
		vol := strconv.FormatFloat(z.volume, 'f', 2, 64)
		ta := strconv.FormatFloat(z.temperature, 'f', 2, 64)
		nr := strconv.Itoa(i + 1)
		lines = append(lines, "   "+nr+"  3   0   0   0   1   0.000    "+vol+" "+ta+" 0 "+z.prjname+" -1 0 2 0 0 0 0 0")
	}
	lines = append(lines, []string{
		"-999",
		"0 ! initial zone concentrations:",
		"-999",
		strconv.Itoa(len(network.paths)) + " ! flow paths:",
		"! P#    f  n#  m#  e#  f#  w#  a#  s#  c#  l#    X       Y      relHt  mult wPset wPmod wazm Fahs Xmax Xmin icn dir u[4] cdvf <cdvfName> cfd <cfdData[4]>",
	}...)
	for i, p := range network.paths {
		nr, pset := strconv.Itoa(i+1), strconv.FormatFloat(p.pressure, 'f', 2, 64)
		line := "   " + nr + "    "
		if p.from == -1 {
			line += "1  -1   " + _getZoneIndex(zones[p.to], network.zones)
		} else {
			line += "0   " + _getZoneIndex(zones[p.from], network.zones) + "   " + _getZoneIndex(zones[p.to], network.zones)
		}
		line += "   " + nr + "   0   0   0   0   0   1   0.000   0.000   0.000 1 " + pset + " 0 -1 0 0 0  27  1 -1 0 0 0 0 0 0"
		lines = append(lines, line)
	}
	lines = append(lines, []string{
		"-999",
		"0 ! duct junctions:",
		"-999",
		"0 ! initial junction concentrations:",
		"-999",
		"0 ! duct segments:",
		"-999",
		"0 ! source/sinks:",
		"-999",
		"0 ! occupancy schedules:",
		"-999",
		"0 ! exposures:",
		"-999",
		"0 ! annotations:",
		"-999",
		"* end project file.",
	}...)
	var builder strings.Builder
	for i := 0; i < len(lines); i++ {
		builder.WriteString(lines[i] + "\n")
	}
	os.Remove(path.Join(info.directory, prjBaseName))
	// os.RemoveAll(prjDictionary)
	// os.Mkdir(prjDictionary, os.ModePerm)
	file, _ := os.Create(path.Join(info.directory, prjBaseName))
	io.WriteString(file, builder.String())
	//return pathList
	return path.Join(info.directory, prjBaseName)
}

// top Func
func splitPaths(networkInput airFlowNetwork) []airFlowNetwork {
	paths := networkInput.paths
	used, networks := make([]bool, len(paths)), []airFlowNetwork{}
	for _getUnusedIndex(used) < len(paths) {
		// Find an unused flowPath to start
		startPoint := _getUnusedIndex(used)
		zoneInNetwork := make([]bool, len(networkInput.zones))
		subPath := []flowPath{networkInput.paths[startPoint]}
		subZone := make([]zone, 0)

		// Mark startPoint as used
		used[startPoint] = true
		if networkInput.paths[startPoint].from >= 0 {
			zoneInNetwork[networkInput.paths[startPoint].from] = true
		}
		zoneInNetwork[networkInput.paths[startPoint].to] = true

		// Iterate until subPath is unchanged
		for count := 0; count < len(subPath); {
			count = len(subPath)
			for i := 0; i < len(networkInput.paths); i++ {
				if !used[i] {
					// Test whether this flowPath is connected to a zone in zoneInNetwork
					if zoneInNetwork[networkInput.paths[i].from] || zoneInNetwork[networkInput.paths[i].to] {
						// Mark flowPath[i] as used
						used[i] = true
						zoneInNetwork[networkInput.paths[i].to] = true
						if networkInput.paths[i].from >= 0 {
							zoneInNetwork[networkInput.paths[i].from] = true
						}
						subPath = append(subPath, networkInput.paths[i])
					}
				}
			}
		}

		// Transform the topology of flowPath according to the new zone index
		transform := make(map[int]int)
		for i, _ := range zoneInNetwork {
			if zoneInNetwork[i] {
				subZone = append(subZone, networkInput.zones[i])
				transform[i] = len(subZone) - 1
			}
		}
		for i, _ := range subPath {
			subPath[i].from = transform[subPath[i].from]
			subPath[i].to = transform[subPath[i].to]
		}

		// New network
		networks = append(networks, airFlowNetwork{subZone, subPath})
	}

	return networks
}

// assist Func
func callContam(network airFlowNetwork, prjFile string) string {
	exePath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}
	exeDir, _ := filepath.EvalSymlinks(filepath.Dir(exePath))
	simFile := path.Join(filepath.Dir(prjFile), strings.TrimSuffix(path.Base(prjFile), ".prj")+".sim")
	batFile := path.Join(filepath.Dir(prjFile), strings.TrimSuffix(path.Base(prjFile), ".prj")+".bat")
	// construct *.bat
	lines := "cd " + exeDir + "\n"
	lines += "contam\\contamx3 " + prjFile + "\n"
	lines += "(echo n && echo y && echo 1-" + strconv.Itoa(len(network.paths)) + ") | simread " + simFile + "\n"
	os.Remove(batFile)
	file, _ := os.Create(batFile)
	io.WriteString(file, lines)
	file.Close()
	// 执行bat文件
	exec.Command(batFile).Run()
	return path.Join(filepath.Dir(prjFile), strings.TrimSuffix(path.Base(prjFile), ".prj")+".lfr")
}

// assist Func
func getIconList(network airFlowNetwork) [][]int {
	pathCount, zoneCount, iconList, rec := 0, 0, [][]int{}, make(map[string]struct{})
	for _, p := range network.paths {
		pathCount++
		iconList = append(iconList, []int{27, p.row, p.col, pathCount, p.hei})
		for _, i := range []int{p.from, p.to} {
			if i == -1 {
				continue
			}
			z := network.zones[i]
			c := strconv.Itoa(z.row) + "," + strconv.Itoa(z.col)
			if _, ok := rec[c]; ok {
				continue
			}
			zoneCount++
			iconList = append(iconList, []int{5, z.row, z.col, zoneCount, z.hei})
			rec[c] = struct{}{}
			for _, point := range z.points {
				c = strconv.Itoa(point[0]) + "," + strconv.Itoa(point[1])
				if _, ok := rec[c]; ok {
					continue
				}
				iconList = append(iconList, []int{16, point[0], point[1], 0})
				rec[c] = struct{}{}
			}
		}
	}
	sort.Slice(iconList, func(i, j int) bool {
		if iconList[i][2] < iconList[j][2] {
			return true
		} else if iconList[i][2] == iconList[j][2] && iconList[i][1] < iconList[j][1] {
			return true
		} else {
			return false
		}
	})
	return iconList
}

// assist Func
func outputResults(network airFlowNetwork, lfrFilePath string) string {
	airVol := float64(0)
	airVel := ""
	airNetwork := make([][]float64, len(network.zones)+1)
	for i, _ := range airNetwork {
		airNetwork[i] = make([]float64, len(network.zones)+1)
		for j, _ := range airNetwork[i] {
			airNetwork[i][j] = 0
		}
	}

	lfrFile, _ := os.ReadFile(lfrFilePath)
	lfrData := strings.Split(string(lfrFile), "\r\n")
	for i, p := range network.paths {
		lfrRow := _getLfrRow(strings.Split(lfrData[i+1], " "))
		flow, _ := strconv.ParseFloat(lfrRow[2][:len(lfrRow[2])-1], 64)
		if p.from == -1 {
			if flow > 0 {
				airVol += flow / 1.205 * 3600
			}
			airNetwork[len(network.zones)][p.from] += flow / 1.205 * 3600
			airNetwork[p.from][len(network.zones)] -= flow / 1.205 * 3600
		} else {
			airVel += p.username + "," + network.zones[p.from].username + "," + network.zones[p.to].username + "," + fmt.Sprintf("%.2f", p.height*p.width) + "," + fmt.Sprintf("%.2f", flow/(1.205*p.height*p.width)) + "\n"
			airNetwork[p.from][p.to] += flow / 1.205 * 3600
			airNetwork[p.to][p.from] -= flow / 1.205 * 3600
		}
	}
	resultStr := ""
	resultStr += "!TOTAL AIR CHANGE COEFFICIENT (AIR CHANGE PER HOUR, ACH)\n"
	resultStr += fmt.Sprintf("%.2f", airVol)
	resultStr += "!Path AIR FLOW (AIR VELOCITY, m/s)\n"
	resultStr += "!pathName,fromZone,toZone,Volume(m3),Velocity(m/s)\n"
	resultStr += airVel[:len(airVel)-1]
	resultStr += "!ZONE AIR FLOW NETWORK (AIR CHANGE PER HOUR, ACH)\n"

	resultStr += "!ZONE NAME,\t"
	for _, z := range network.zones {
		resultStr += "," + z.username
	}
	resultStr += ",outdoor(amt)\n"

	resultStr += "!\t,FROM\\TO"
	for _, z := range network.zones {
		resultStr += "," + z.prjname
	}
	resultStr += ",outdoor(amt)\n"

	for i, _ := range network.zones {
		resultStr += network.zones[i].username + "," + network.zones[i].prjname
		for j, _ := range airNetwork[i] {
			resultStr += "," + fmt.Sprintf("%.2f", airNetwork[i][j])
		}
		resultStr += "\n"
	}
	resultStr += "\t,outdoor(amt)"
	for j, _ := range airNetwork[len(network.zones)] {
		resultStr += "," + fmt.Sprintf("%.2f", airNetwork[len(network.zones)][j])
	}
	resultStr += "\n"
	return resultStr
}

// nested Func
func _MtoCM(char string) int {
	data, _ := strconv.ParseFloat(char, 64)
	return int(math.Floor(data * 100))
}
func _getUnusedIndex(used []bool) int {
	for i := 0; i < len(used); i++ {
		if !used[i] {
			return i
		}
	}
	return len(used)
}
func _getZoneIndex(to zone, zoneList []zone) string {
	for i, z := range zoneList {
		if z.row == to.row && z.col == to.col {
			return strconv.Itoa(i + 1)
		}
	}
	return ""
}
func _getLfrRow(strs []string) []string {
	res := []string{}
	for _, v := range strs {
		if len(v) > 4 {
			res = append(res, v)
		}
	}
	return res
}
