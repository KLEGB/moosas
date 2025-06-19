package main

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"sort"
	"strconv"
	"strings"
)

var (
	zones []zone
	paths []path
)

type zone struct {
	volume float64
	row    int
	col    int
	hei    int
	points [][]int
	heat   float64
	temperature  float64
	zonename string
}

type path struct {
	height   float64
	width    float64
	row      int
	col      int
	hei      int
	from     int
	to       int
	pressure float64
}

func main() {
	// 读取文件
	out_temp:=readZones()
	readPaths()
	// 划分网络
	networks,airVol,airVel:=splitPaths(),float64(0),""
	for i:=0;i<len(networks);i++ {
		// 调用coantam执行模拟
		pathList:=generatePrj(getIconList(networks[i]),i,out_temp)
		callContam(len(pathList))
		outputResults(pathList,&airVol,&airVel)
	}
	// 输出结果
	os.Remove("airVol")
	file, _ := os.Create("airVol")
	io.WriteString(file, fmt.Sprintf("%.2f",airVol))
	os.Remove("airVel")
	file, _ = os.Create("airVel")
	io.WriteString(file, airVel[:len(airVel)-1])
}

func readZones() float64{
	zonesFile,_:=os.ReadFile("zones")
	heatFile,_:=os.ReadFile("roomheat")
	zonesList:=strings.Split(string(zonesFile), "\r\n")
	heatList:=strings.Split(string(heatFile), "\r\n")
	t0_str:=strings.Split(heatList[len(heatList)-1], ",")[1]
	t0, _ :=strconv.ParseFloat(t0_str, 64)
	zones=make([]zone,len(zonesList))
	for i:=0;i<len(zonesList);i++ {
		tem:=strings.Split(zonesList[i], ",")
		termal_parms:=strings.Split(heatList[i], ",")
		
		heat, _ :=strconv.ParseFloat(termal_parms[2], 64)
		temperature, _ :=strconv.ParseFloat(termal_parms[1], 64)
		zonename:=termal_parms[0]

		volume, _ := strconv.ParseFloat(tem[0], 64)
		row,_ := strconv.Atoi(tem[1])
		col,_ := strconv.Atoi(tem[2])
		hei,_ := strconv.Atoi(tem[3])
		points:=[][]int{}
		for i:=2;i<len(tem)/2;i++ {
			pointRow,_ := strconv.Atoi(tem[i*2+0])
			pointCol,_ := strconv.Atoi(tem[i*2+1])
			points=append(points,[]int{pointRow,pointCol})
		}
		zones[i]=zone{
			volume,
			row,
			col,
			hei,
			points,
			heat,
			temperature,
			zonename,
		}
	}
	return t0
}

func readPaths() {
	pathsFile,_:=os.ReadFile("paths")
	pathsList:=strings.Split(string(pathsFile), "\r\n")
	paths=make([]path,len(pathsList))
	for i:=0;i<len(pathsList);i++ {
		tem:=strings.Split(pathsList[i], ",")
		height,_ := strconv.ParseFloat(tem[0], 64)
		width,_ := strconv.ParseFloat(tem[1], 64)
		row,_ := strconv.Atoi(tem[2])
		col,_ := strconv.Atoi(tem[3])
		hei,_ := strconv.Atoi(tem[4])
		from,_ := strconv.Atoi(tem[5])
		to,_ := strconv.Atoi(tem[6])
		pressure,_ := strconv.ParseFloat(tem[7], 64)
		paths[i]=path{
			height,
			width,
			row,
			col,
			hei,
			from,
			to,
			pressure,
		}
	}
}

func splitPaths() [][]path {
	used,networks:=make([]bool,len(paths)),[][]path{}
	for getUnusedIndex(used)<len(paths) {
		i:=getUnusedIndex(used)
		zoneSet,network:=make(map[int]struct{}),[]path{paths[i]}
		if paths[i].from>=0 {
			zoneSet[paths[i].from]= struct{}{}
		}
		zoneSet[paths[i].to]= struct{}{}
		used[i]=true
		partitionNetwork(used,zoneSet,&network)
		networks=append(networks,network)
	}
	return networks
}

func getUnusedIndex(used []bool) int {
	for i:=0;i<len(used);i++ {
		if !used[i] {
			return i
		}
	}
	return len(used)
}

func partitionNetwork(used []bool,zoneSet map[int]struct{},network *[]path) {
	for count:=0;count<len(*network); {
		count=len(*network)
		for i:=0;i<len(paths);i++ {
			if used[i] {
				continue
			}
			if _,ok:=zoneSet[paths[i].from];ok {
				used[i]=true
				zoneSet[paths[i].to]= struct{}{}
				*network=append(*network,paths[i])
			} else if _,ok=zoneSet[paths[i].to];ok {
				used[i]=true
				if paths[i].from>=0 {
					zoneSet[paths[i].from]= struct{}{}
				}
				*network=append(*network,paths[i])
			}
		}
	}
}

func getIconList(network []path) [][]int {
	pathCount,zoneCount,iconList,rec:=0,0,[][]int{},make(map[string]struct{})
	for _,p:= range network {
		pathCount++
		iconList=append(iconList,[]int{27,p.row,p.col,pathCount,p.hei})
		for _,i:= range []int{p.from,p.to} {
			if i==-1 {
				continue
			}
			z:=zones[i]
			c:=strconv.Itoa(z.row)+","+strconv.Itoa(z.col)
			if _,ok:=rec[c];ok {
				continue
			}
			zoneCount++
			iconList=append(iconList,[]int{5,z.row,z.col,zoneCount,z.hei})
			rec[c]=struct{}{}
			for _,point:= range z.points {
				c=strconv.Itoa(point[0])+","+strconv.Itoa(point[1])
				if _,ok:=rec[c];ok {
					continue
				}
				iconList=append(iconList,[]int{16,point[0],point[1],0})
				rec[c]=struct{}{}
			}
		}
	}
	sort.Slice(iconList,func(i,j int) bool {
		if iconList[i][2]<iconList[j][2] {
			return true
		} else if iconList[i][2]==iconList[j][2] && iconList[i][1]<iconList[j][1] {
			return true
		} else {
			return false
		}
	})
	return iconList
}

func generatePrj(iconList [][]int,netindex int,t0 float64) []path {
	out_temp := strconv.FormatFloat(t0+273.15,'f',3,64)
	lines:=[]string{
		"ContamW 3.4.0.4 0",
		"afn",
		"! rows cols ud uf    T   uT     N     wH  u  Ao    a",
		"    58   66  0  0 " + out_temp + " 2    0.00 10.00 0 0.600 0.280",
		"!  scale     us  orgRow  orgCol  invYaxis showGeom",
		"  1.000e+00   0      56       1     0        0",
		"! Ta       Pb      Ws    Wd    rh  day u..",
		out_temp + " 101325.0  0.000   0.0 0.000 1 2 0 0 1 ! steady simulation",
		out_temp + " 101325.0  1.000 270.0 0.000 1 2 0 0 1 ! wind pressure test",
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
		"  1   0.000   3.000 "+strconv.Itoa(len(iconList))+" 0 0 <1>",
		"!icn col row  #",
	}
	for _,icon:= range iconList {
		icn,col,row,index:=strconv.Itoa(icon[0]),strconv.Itoa(icon[1]),strconv.Itoa(icon[2]),strconv.Itoa(icon[3])
		lines=append(lines,"  "+icn+"  "+col+"  "+row+"  "+index)
	}
	pathList,zoneList:=getPathAndZoneList(iconList)
	lines=append(lines,[]string{
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
		strconv.Itoa(len(pathList))+" ! flow elements:",
	}...)
	for i,p:= range pathList {
		h,w:=p.height,p.width
		lam:=fmt.Sprintf("%.6f",h*w*h*w/(h+w)*0.02028)
		turb:=fmt.Sprintf("%.6f",h*w*0.551543)
		dh:=fmt.Sprintf("%.6f",h*0.222222)
		hd:=strconv.FormatFloat(h,'f',2,64)
		wd:=strconv.FormatFloat(w,'f',2,64)
		lines=append(lines,[]string{
			strconv.Itoa(i+1)+" 27 dor_pl2 p"+strconv.Itoa(i+1),
			"",
			" "+lam+" "+turb+" 0.5 "+dh+" "+hd+" "+wd+" 0.78 0 0",
		}...)
	}
	lines=append(lines,[]string{
		"-999",
		"0 ! duct elements:",
		"-999",
		"0 ! control super elements:",
		"-999",
		"0 ! control nodes:",
		"-999",
		"0 ! simple AHS:",
		"-999",
		strconv.Itoa(len(zoneList))+" ! zones:",
		"! Z#  f  s#  c#  k#  l#  relHt    Vol  T0  P0  name  clr uH uT uP uV axs cdvf <cdvfName> cfd <cfdName> <1dData:>",
	}...)
	roomheat:=make([]string,len(zoneList)) 
	for i,z:= range zoneList {
		nr,vol:=strconv.Itoa(i+1),strconv.FormatFloat(z.volume,'f',2,64)
		z_temp:= strconv.FormatFloat(273.15+z.temperature,'f',2,64)
		lines=append(lines,"   "+nr+"  3   0   0   0   1   0.000    "+vol+" "+z_temp+" 0 z"+nr+" -1 0 2 0 0 0 0 0")
		roomheat[i]=z.zonename+","+strconv.FormatFloat(z.heat,'f',2,64)
	}
	lines=append(lines,[]string{
		"-999",
		"0 ! initial zone concentrations:",
		"-999",
		strconv.Itoa(len(pathList))+" ! flow paths:",
		"! P#    f  n#  m#  e#  f#  w#  a#  s#  c#  l#    X       Y      relHt  mult wPset wPmod wazm Fahs Xmax Xmin icn dir u[4] cdvf <cdvfName> cfd <cfdData[4]>",
	}...)
	for i,p:= range pathList {
		nr,pset:=strconv.Itoa(i+1),strconv.FormatFloat(p.pressure,'f',2,64)
		line:="   "+nr+"    "
		if p.from==-1 {
			line+="1  -1   "+getZoneIndex(zones[p.to],zoneList)
		} else {
			line+="0   "+getZoneIndex(zones[p.from],zoneList)+"   "+getZoneIndex(zones[p.to],zoneList)
		}
		line+="   "+nr+"   0   0   0   0   0   1   0.000   0.000   0.000 1 "+pset+" 0 -1 0 0 0  27  1 -1 0 0 0 0 0 0"
		lines=append(lines,line)
	}
	lines=append(lines,[]string{
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
	var heatbuilder strings.Builder
	for i:=0;i<len(lines);i++ {
		builder.WriteString(lines[i]+"\n")
	}
	for i:=0;i<len(roomheat);i++ {
		heatbuilder.WriteString(roomheat[i]+"\n")
	}
	os.RemoveAll("afn")
	os.RemoveAll("thermal")
	os.Mkdir("afn",os.ModePerm)
	os.Mkdir("thermal",os.ModePerm)
	file, _ := os.Create("afn/afn.prj")
	io.WriteString(file, builder.String())
	thermfile, _ := os.Create("thermal/thermal_afn_"+strconv.Itoa(netindex)+".prj")
	roomheatfile,_:= os.Create("thermal/thermal_afn_"+strconv.Itoa(netindex)+".heat")
	io.WriteString(thermfile, builder.String())
	io.WriteString(roomheatfile, heatbuilder.String())
	return pathList
}

func getPathAndZoneList(iconList [][]int) ([]path,[]zone) {
	pathList,zoneList:=[]path{},[]zone{}
	for _,icon:= range iconList {
		if icon[0]==27 {
			for _,p:= range paths {
				if icon[1]==p.row && icon[2]==p.col && icon[4]==p.hei {
					pathList=append(pathList,p)
				}
			}
		} else if icon[0]==5 {
			for _,z:= range zones {
				if icon[1]==z.row && icon[2]==z.col && icon[4]==z.hei {
					zoneList=append(zoneList,z)
				}
			}
		}
	}
	return pathList,zoneList
}

func getZoneIndex(to zone,zoneList []zone) string {
	for i,z:= range zoneList {
		if z.row==to.row && z.col==to.col {
			return strconv.Itoa(i+1)
		}
	}
	return ""
}

func callContam(pathCount int) {
	// 创建bat文件
	lines:="cd contam\ncontamx3 ..\\afn\\afn.prj\n"
	lines+="(echo n && echo y && echo 1-"+strconv.Itoa(pathCount)+") | simread ..\\afn\\afn.sim"
	os.Remove("afn.bat")
	file, _ := os.Create("afn.bat")
	io.WriteString(file, lines)
	file.Close()
	// 执行bat文件
	dir,_:=os.Getwd()
	//os.Chdir(dir)
	exec.Command(dir+"\\afn.bat").Run()
}

func outputResults(pathList []path,airVol *float64,airVel *string) {
	dir,_:=os.Getwd()
	lfrFile,_:=os.ReadFile(dir+"\\afn\\afn.lfr")
	lfrData:=strings.Split(string(lfrFile), "\r\n")
	for i,p:= range pathList {
		lfrRow:=cleanLfrRow(strings.Split(lfrData[i+1], " "))
		flow,_:=strconv.ParseFloat(lfrRow[2][:len(lfrRow[2])-1],64)
		if p.from==-1 {
			if flow>0 {
				*airVol+=flow/1.205*3600
			}
		} else {
			*airVel+=strconv.Itoa(zones[p.from].row)+","+strconv.Itoa(zones[p.from].col)+","+strconv.Itoa(zones[p.from].hei)+","+strconv.Itoa(p.row)+","+strconv.Itoa(p.col)+","+strconv.Itoa(p.hei)+"|"+fmt.Sprintf("%.2f",flow/(1.205*p.height*p.width))+"\n"
		}
		*airVel+=strconv.Itoa(zones[p.to].row)+","+strconv.Itoa(zones[p.to].col)+","+strconv.Itoa(zones[p.to].hei)+","+strconv.Itoa(p.row)+","+strconv.Itoa(p.col)+","+strconv.Itoa(p.hei)+"|"+fmt.Sprintf("%.2f",-flow/(1.205*p.height*p.width))+"\n"
	}
}

func cleanLfrRow(strs []string) []string {
	res:=[]string{}
	for _,v:= range strs {
		if len(v)>4 {
			res=append(res,v)
		}
	}
	return res
}
