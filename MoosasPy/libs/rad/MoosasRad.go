package main

import (
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
)

const (
	eps float64 = 1e-2
)

type vec struct {
	x float64
	y float64
	z float64
}

type ray struct {
	origin    vec
	direction vec
}

type face struct {
	loop   []vec
	factor vec
}

// IO
func loadRay(path string) []ray {
	input0, _ := os.ReadFile(path)
	seq := "\n"
	if strings.Contains(string(input0), "\r") {
		seq = "\r\n"
		fmt.Println(seq)
	}
	input1 := strings.Split(string(input0), seq)
	rays := make([]ray, 0)
	for i := 0; i < len(input1); i++ {
		input2 := strings.Split(input1[i], ",")
		if len(input2) < 3 {
			continue
		}
		ox, _ := strconv.ParseFloat(input2[0], 64)
		oy, _ := strconv.ParseFloat(input2[1], 64)
		oz, _ := strconv.ParseFloat(input2[2], 64)
		vx, _ := strconv.ParseFloat(input2[3], 64)
		vy, _ := strconv.ParseFloat(input2[4], 64)
		vz, _ := strconv.ParseFloat(input2[5], 64)
		rays = append(rays, ray{
			vec{ox, oy, oz},
			unit(vec{vx, vy, vz}),
		})
	}
	return rays
}

func loadgeo(path string) []face {
	input0, _ := os.ReadFile(path)
	blocks := strings.Split(string(input0), ";")
	faces := make([]face, 0)

	for j := 0; j < len(blocks); j++ {
		seq := "\n"
		if strings.Contains(blocks[j], "\r") {
			seq = "\r\n"
		}
		lines := strings.Split(blocks[j], seq)
		theFactor := vec{}
		theLoop := make([]vec, 0)

		for _, li := range lines {

			if !strings.HasPrefix(li, "!") && len(li) > 0 {
				if strings.Contains(li, "fn") {
					norString := strings.Split(li, ",")
					vx, _ := strconv.ParseFloat(norString[1], 64)
					vy, _ := strconv.ParseFloat(norString[2], 64)
					vz, _ := strconv.ParseFloat(norString[3], 64)
					theFactor = unit(vec{vx, vy, vz})
				}
				if strings.Contains(li, "fv") {
					//fmt.Println(lines[i])
					poiString := strings.Split(li, ",")
					px, _ := strconv.ParseFloat(poiString[1], 64)
					py, _ := strconv.ParseFloat(poiString[2], 64)
					pz, _ := strconv.ParseFloat(poiString[3], 64)
					theLoop = append(theLoop, vec{px, py, pz})
				}
				//fmt.Println(theLoop)
			}
		}
		if len(theLoop) > 0 {
			faces = append(faces, face{theLoop, theFactor})
		}

	}
	return faces
}

// 向量运算相关函数
func dot(vec1 vec, vec2 vec) float64 {
	return vec1.x*vec2.x + vec1.y*vec2.y + vec1.z*vec2.z
}

func add(start vec, end vec) vec {
	return vec{end.x + start.x, end.y + start.y, end.z + start.z}
}

func multi(mul float64, vector vec) vec {
	return vec{mul * vector.x, mul * vector.y, mul * vector.z}
}

func unit(vector vec) vec {
	theLength := length(vector)
	return vec{vector.x / theLength, vector.y / theLength, vector.z / theLength}
}

func length(vector vec) float64 {
	return math.Pow(vector.x*vector.x+vector.y*vector.y+vector.z*vector.z, 0.5)
}

func negative(vector vec) vec {
	return vec{-vector.x, -vector.y, -vector.z}
}

func force2d(mesh face) face {
	newloop := make([]vec, len(mesh.loop))
	for i := 0; i < len(mesh.loop); i++ {
		newloop[i] = vec{mesh.loop[i].x, mesh.loop[i].y, 0}
	}
	return face{newloop, vec{0, 0, 1}}
}

func containBy(p1 vec, p2 vec) bool {
	return dcmp(p1.x-p2.x) == 0 && dcmp(p1.y-p2.y) == 0 && dcmp(p1.z-p2.z) == 0
}

// 三态函数
func dcmp(x float64) int {
	if math.Abs(x) < eps {
		return 0
	} else {
		if x < 0 {
			return -1
		} else {
			return 1
		}
	}
}

func onSegment(point vec, segStart vec, segEnd vec) bool {
	unitDirectionDot := dot(unit(add(negative(segStart), point)), unit(add(negative(segEnd), point)))
	if unitDirectionDot <= -1+eps && unitDirectionDot >= -1-eps {
		return true
	}
	return false
}

// 顶层运算函数
func intersection(rayline ray, mesh face) ray {
	//平面参数方程: (P - p0).n = 0
	//射线参数方程: P(t) = p1 + tu
	//相交点方程：(P(t) - p0).n = (p1 + tu - p0).n = 0
	//解得： P(t) = p1 + t*u = p1 + ((p0 - p1).n/u.n) * u
	p0 := mesh.loop[0]
	p1 := rayline.origin
	if dot(mesh.factor, rayline.direction) < 0 {
		mesh.factor = negative(mesh.factor)
	}
	t := dot(add(p0, negative(p1)), mesh.factor) / dot(mesh.factor, rayline.direction)

	if t <= 0.01 {
		return ray{vec{-1, -1, -1}, vec{-1, -1, -1}}
	}
	newP := add(p1, multi(t, rayline.direction))
	newD := multi(dot(rayline.direction, mesh.factor), negative(mesh.factor))
	newD = multi(2.0, add(rayline.direction, newD))
	newD = negative(add(rayline.direction, newD))
	return ray{newP, newD}
}

func pointInFace(point vec, mesh face) bool {
	//射线法判断点是否在多边形内，兼容非凸
	flag := false
	planarFace := force2d(mesh)
	for i := 1; i < len(planarFace.loop); i++ {
		j := i - 1
		P1 := mesh.loop[i]
		P2 := mesh.loop[j]
		if onSegment(point, P1, P2) {
			return true
		}
		//前一个判断min(P1.y,P2.y)<P.y<=max(P1.y,P2.y)
		//后一个判断被测点 在 射线与边交点 的左边
		if ((dcmp(P1.y-point.y) > 0) != (dcmp(P2.y-point.y) > 0)) && dcmp(point.x-(point.y-P1.y)/(P1.y-P2.y)*(P1.x-P2.x)-P1.x) < 0 {
			flag = !flag
		}
	}
	return flag
}

func rayFaceTest(rayline ray, meshes []face) ray {
	for i := 0; i < len(meshes); i++ {
		intersetionRay := intersection(rayline, meshes[i])
		if !containBy(intersetionRay.origin, vec{-1, -1, -1}) {
			if pointInFace(intersetionRay.origin, meshes[i]) {
				return intersetionRay
			}
		}
	}
	return ray{vec{-1, -1, -1}, vec{-1, -1, -1}}
}

type simulationInfo struct {
	inputFile    string
	outputFile   string
	geometryFile string
}

func help() {
	fmt.Println("Moosas rayTest.")
	fmt.Println("Command line should be: MoosasRad.exe [-h,-g...] inputFile.i")
	fmt.Println("Optional command:")
	fmt.Println("-h / -help : reprint the help information")
	fmt.Println("-g / -geo : geometrical input for ray test contents")
	fmt.Println("-o / -output : output file path (default: .\\MoosasEnergy.o)")
}

func main() {
	info := simulationInfo{
		outputFile:   "MoosasRad.o",
		inputFile:    "MoosasRad.i",
		geometryFile: "MoosasRadGeometry.geo",
	}

	for i := 1; i < len(os.Args); {
		if os.Args[i] == "-h" || os.Args[i] == "-help" {
			help()
		}
		if os.Args[i] == "-o" || os.Args[i] == "-output" {
			info.outputFile, _ = filepath.Abs(os.Args[i+1])
		}
		if os.Args[i] == "-g" || os.Args[i] == "-geo" {
			info.geometryFile, _ = filepath.Abs(os.Args[i+1])
		}
		i++
	}
	info.inputFile, _ = filepath.Abs(os.Args[len(os.Args)-1])
	fileInfo, err := os.Lstat(info.inputFile)
	if err != nil {
		fmt.Println(err)
		fmt.Println("invalid inputFile. Please check:", info.inputFile)
	} else {
		mode := fileInfo.Mode()
		//fmt.Println(info)
		if mode.IsRegular() {
			simulation(info)
		} else {
			fmt.Println("inputFile path is not a file. Please check:", info.inputFile)
		}
	}
}

// 主函数
func simulation(inputInfo simulationInfo) {
	rays := loadRay(inputInfo.inputFile)
	meshes := loadgeo(inputInfo.geometryFile)
	ch,wg,res:= make(chan string,256),sync.WaitGroup{},strings.Builder{}
	for i := 0; i < len(rays); i++ {
		go func(rayline ray) {
			ray := rayFaceTest(rayline, meshes)
			intersect:=strings.Builder{}
			intersect.WriteString(strconv.FormatFloat(ray.origin.x, 'f', 2, 64))
			intersect.WriteString(",")
			intersect.WriteString(strconv.FormatFloat(ray.origin.y, 'f', 2, 64))
			intersect.WriteString(",")
			intersect.WriteString(strconv.FormatFloat(ray.origin.z, 'f', 2, 64))
			intersect.WriteString(",")
			intersect.WriteString(strconv.FormatFloat(ray.direction.x, 'f', 2, 64))
			intersect.WriteString(",")
			intersect.WriteString(strconv.FormatFloat(ray.direction.y, 'f', 2, 64))
			intersect.WriteString(",")
			intersect.WriteString(strconv.FormatFloat(ray.direction.z, 'f', 2, 64))
			intersect.WriteString("\n")
			ch<-intersect.String()
		}(rays[i])
		wg.Add(1)
	}

	go func() {
		for i:=0;i<len(rays);i++ {
			res.WriteString(<-ch)
			wg.Done()
		}
	}()
	wg.Wait()
	
	os.Remove(inputInfo.outputFile)
	file, _ := os.Create(inputInfo.outputFile)
	io.WriteString(file, res.String()[:len(res.String())-1])
}

// 测试函数
func test() {
	rays := ray{vec{0.5, 0.5, 0}, unit(vec{0.1, 0.5, 1})}
	loop := make([]vec, 5)
	loop[0] = vec{0, 0, 1}
	loop[1] = vec{1, 0, 1}
	loop[2] = vec{1, 1, 0}
	loop[3] = vec{0, 1, 0}
	loop[4] = vec{0, 0, 1}
	faces := face{loop, unit(vec{0, 1, 1})}
	//meshes := make([]face, 1)
	//meshes[0] = faces
	meshes := loadgeo("rad/faceGeometries.geo")
	fmt.Println(meshes)
	fmt.Println(intersection(rays, faces))
	fmt.Println(rayFaceTest(rays, meshes))

}
