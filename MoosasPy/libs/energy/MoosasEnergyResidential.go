package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"os"
	"path"
	"path/filepath"
	"strconv"
	"strings"
)

const (
	AirDensity  float64 = 1.29  // 空气密度
	AirCapacity float64 = 0.717 // 空气比热容
)

var (
	summerTemCorrect  float64 = 3.0        // 夏季温度修正(考虑蓄热)
	winterTemCorrect  float64 = 3.0        // 冬季温度修正(考虑蓄热)
	summerRadCorrect  float64 = 0.5936     // 夏季辐射修正
	winterRadCorrect  float64 = 0.6234     // 冬季辐射修正
	lighting_schedule         = []float64{ // 灯光作息
		0, 0, 0, 0, 0, 0.65, 0.65, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.4, 0.4, 0.6, 0.4, 0, 0,
	}
	equipment_schedule = []float64{ // 设备作息
		0, 0, 0, 0, 0, 0, 0.65, 0.75, 0.35, 0.2, 0.2, 0.4, 0.35, 0.2, 0.2, 0.2, 0.2, 0.4, 0.35, 0.35, 0.6, 0.4, 0, 0,
	}
	months = []int{ // 月份数据
		0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365,
	}
	e_data EnergyData // 能耗结果
)

type simulationInfo struct {
	inputFile   string
	outputFile  string
	weatherFile string
	buildingTy  int
	latitude    float64
	altitude    float64
	shapeFactor float64
}

func help() {
	fmt.Println("Moosas Energy Analysis for Residential Buildings.")
	fmt.Println("Command line should be: MoosasEnergyResidential.exe [-h,-w...] inputFile.i")
	fmt.Println("Optional command:")
	fmt.Println("-h / -help : reprint the help information")
	fmt.Println("-w / -weather [weather file path.csv]: weather file formatted in DeST. for file formatted in EPW, please use the script in MoosasPy/weather.py")
	fmt.Println("-t / -type [0,1,2,3,4,5,6]: input building type:\n0 => RESIDENTIAL\n1 => OFFICE\n2 => HOTEL\n3 => SCHOOL\n4 => COMMERCIAL\n5 => OPERA\n6 => HOSPITAL")
	fmt.Println("-l / -lat : latitude of the site")
	fmt.Println("-a / -alt : altitude of the site")
	fmt.Println("-s / -shape : shape factor of the building = gross surface area (m2) / gross building volume (m3)")
	fmt.Println("-o / -output : output file path (default: .\\MoosasEnergy.o)")
}

func main() {
	exePath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}
	res, _ := filepath.EvalSymlinks(filepath.Dir(exePath))
	res = path.Join(res, "..\\..\\db\\weather\\545110.csv")
	info := simulationInfo{
		weatherFile: res,
		outputFile:  "MoosasEnergy.o",
		buildingTy:  0,
		latitude:    0.0,
		altitude:    0.0,
		shapeFactor: 0.78,
	}

	for i := 1; i < len(os.Args); {
		if os.Args[i] == "-h" || os.Args[i] == "-help" {
			help()
		}
		if os.Args[i] == "-w" || os.Args[i] == "-weather" {
			info.weatherFile, _ = filepath.Abs(os.Args[i+1])
		}
		if os.Args[i] == "-o" || os.Args[i] == "-output" {
			info.outputFile, _ = filepath.Abs(os.Args[i+1])
		}
		if os.Args[i] == "-t" || os.Args[i] == "-type" {
			info.buildingTy, _ = strconv.Atoi(os.Args[i+1])
		}
		if os.Args[i] == "-l" || os.Args[i] == "-lat" {
			info.latitude, _ = strconv.ParseFloat(os.Args[i+1], 64)
		}
		if os.Args[i] == "-a" || os.Args[i] == "-alt" {
			info.altitude, _ = strconv.ParseFloat(os.Args[i+1], 64)
		}
		if os.Args[i] == "-s" || os.Args[i] == "-shape" {
			info.shapeFactor, _ = strconv.ParseFloat(os.Args[i+1], 64)
		}
		i++
	}
	info.inputFile, _ = filepath.Abs(os.Args[len(os.Args)-1])
	fileInfo, err := os.Lstat(info.inputFile)
	if err != nil {
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

func simulation(inputInfo simulationInfo) {
	// 输入
	input0, _ := os.ReadFile(inputInfo.inputFile)
	input1 := strings.Split(string(input0), "\n")
	//input2 := strings.Split(input1[0], ",")
	//latitude, _ := strconv.ParseFloat(input2[2], 64)
	energy := MoosasEnergy{
		WeatherFile: inputInfo.weatherFile,
		Latitude:    inputInfo.latitude,
	}
	for i := 0; i < len(input1); i++ {
		if !strings.HasPrefix(input1[i], "!") {
			input2 := strings.Split(input1[i], ",")
			spaceHeight, _ := strconv.ParseFloat(input2[0], 64)
			spaceArea, _ := strconv.ParseFloat(input2[1], 64)
			outsideArea, _ := strconv.ParseFloat(input2[2], 64)
			facadeArea, _ := strconv.ParseFloat(input2[3], 64)
			windowArea, _ := strconv.ParseFloat(input2[4], 64)
			roofArea, _ := strconv.ParseFloat(input2[5], 64)
			skylightArea, _ := strconv.ParseFloat(input2[6], 64)
			floorArea, _ := strconv.ParseFloat(input2[7], 64)
			summerSolar, _ := strconv.ParseFloat(input2[8], 64)
			winterSolar, _ := strconv.ParseFloat(input2[9], 64)
			wall_u, _ := strconv.ParseFloat(input2[10], 64)
			window_u, _ := strconv.ParseFloat(input2[11], 64)
			window_shgc, _ := strconv.ParseFloat(input2[12], 64)
			cooling_tem, _ := strconv.ParseFloat(input2[13], 64)
			cooling_hum, _ := strconv.ParseFloat(input2[14], 64)
			heating_tem, _ := strconv.ParseFloat(input2[15], 64)
			cooling_eer, _ := strconv.ParseFloat(input2[16], 64)
			heating_eer, _ := strconv.ParseFloat(input2[17], 64)
			work_start, _ := strconv.Atoi(input2[18])
			work_end, _ := strconv.Atoi(input2[19])
			ppsm, _ := strconv.ParseFloat(input2[20], 64)
			pfav, _ := strconv.ParseFloat(input2[21], 64)
			phd, _ := strconv.ParseFloat(input2[22], 64)
			ehd, _ := strconv.ParseFloat(input2[23], 64)
			lhd, _ := strconv.ParseFloat(input2[24], 64)
			ach, _ := strconv.ParseFloat(input2[25], 64)
			achn, _ := strconv.ParseFloat(input2[26], 64)
			energy.Spaces = append(energy.Spaces, MoosasSpace{
				spaceHeight,
				spaceArea,
				outsideArea,
				facadeArea,
				windowArea,
				roofArea,
				skylightArea,
				floorArea,
				summerSolar,
				winterSolar,
				wall_u,
				window_u,
				window_shgc,
				cooling_tem,
				cooling_hum,
				heating_tem,
				cooling_eer,
				heating_eer,
				work_start,
				work_end,
				ppsm,
				pfav,
				phd,
				ehd,
				lhd,
				ach,
				achn,
			})
		}
	}
	// 计算
	energy.Analysis()
	// 输出
	totalArea := float64(0)
	for i := 0; i < len(energy.Spaces); i++ {
		totalArea += energy.Spaces[i].SpaceArea
	}
	output := "!TOTAL:\n!Cooling,Heating,Lighting\n"
	output += convertResult(e_data.Total, totalArea)
	output += ";\n!SPACE RESULT:\n!Cooling,Heating,Lighting\n"
	for i := 0; i < len(e_data.Spaces); i++ {
		output += convertResult(e_data.Spaces[i], energy.Spaces[i].SpaceArea)
	}
	output += ";\n!MONTH RESULT:\n!Cooling,Heating,Lighting\n"
	for i := 0; i < len(e_data.Months); i++ {
		output += convertResult(e_data.Months[i], totalArea)
	}
	os.Remove(inputInfo.outputFile)
	file, _ := os.Create(inputInfo.outputFile)
	io.WriteString(file, output[:len(output)-1])
}

type MoosasEnergy struct {
	WeatherFile string
	Latitude    float64
	Spaces      []MoosasSpace
}

type MoosasSpace struct {
	SpaceHeight  float64
	SpaceArea    float64
	OutsideArea  float64
	FacadeArea   float64
	WindowArea   float64
	RoofArea     float64
	SkylightArea float64
	FloorArea    float64
	SummerSolar  float64
	WinterSolar  float64
	Wall_U       float64 // 外墙U值
	Window_U     float64 // 外窗U值
	Window_SHGC  float64 // 外窗SHGC值
	CoolingTem   float64 // 空调控制温度
	CoolingHum   float64 // 空调控制湿度
	HeatingTem   float64 // 采暖控制温度
	CoolingEER   float64 // 空调能效比
	HeatingEER   float64 // 采暖能效比
	WorkStart    int     // 运行开始时刻
	WorkEnd      int     // 运行结束时刻
	PPSM         float64 // 每平米人数
	PFAV         float64 // 人均新风量
	PHD          float64 // 人员散热
	EHD          float64 // 设备散热
	LHD          float64 // 灯光散热
	ACH          float64 // 换气次数
	ACHN         float64 // 夜间换气次数
}

type MoosasWeather struct {
	SummerStart int       // 空调季开始日
	SummerEnd   int       // 空调季结束日
	WinterStart int       // 采暖季开始日
	WinterEnd   int       // 采暖季结束日
	AirTem      []float64 // 空气温度
	GroTem      []float64 // 地面温度
}

type EnergyData struct {
	Total  EnergyItem
	Spaces []EnergyItem
	Months []EnergyItem
}

type EnergyItem struct {
	CoolingEnergy  float64
	HeatingEnergy  float64
	LightingEnergy float64
}

func (e MoosasEnergy) Analysis() {
	// 前处理: 获取天气数据
	weather := latitudeCorrection(e.Latitude)
	weather_file, _ := os.Open(e.WeatherFile)
	weather_data, _ := csv.NewReader(weather_file).ReadAll()
	for _, v := range weather_data {
		at, _ := strconv.ParseFloat(v[3], 64)
		weather.AirTem = append(weather.AirTem, at)
		gt, _ := strconv.ParseFloat(v[7], 64)
		weather.GroTem = append(weather.GroTem, gt)
	}
	// 迭代计算
	rec := make([][][]float64, len(e.Spaces))
	for i := 0; i < len(e.Spaces); i++ {
		rec[i] = make([][]float64, 365)
		for d := 0; d < 365; d++ {
			rec[i][d] = make([]float64, 3)
		}
	}
	for i := 0; i < len(e.Spaces); i++ {
		s := e.Spaces[i]
		s.SummerSolar = s.SummerSolar * summerRadCorrect / float64(weather.SummerEnd-weather.SummerStart+1)
		s.WinterSolar = s.WinterSolar * winterRadCorrect / float64(365-weather.WinterStart+weather.WinterEnd+1)
		for d := 0; d < 365; d++ {
			for h := 0; h < 24; h++ {
				lightingEnergy := s.LHD * lighting_schedule[h] * s.SpaceArea
				rec[i][d][2] += lightingEnergy
				if d >= weather.SummerStart && d <= weather.SummerEnd { // 空调季
					deltaT := weather.AirTem[d*24+h] - s.CoolingTem
					deltaG := weather.GroTem[d*24+h] - s.CoolingTem
					envelopeLoad := calculate_envelope_load(s, deltaT+summerTemCorrect, deltaG) // 围护结构负荷
					heatDissipation := (s.PPSM*s.PHD+s.EHD*equipment_schedule[h])*s.SpaceArea + lightingEnergy
					if s.OutsideArea > 0 {
						infiltrationLoad := AirDensity * AirCapacity * deltaT * s.SpaceArea * s.SpaceHeight * s.ACH / 3.6
						rec[i][d][0] += non(envelopeLoad + heatDissipation + infiltrationLoad)
					} else {
						rec[i][d][0] += non(envelopeLoad + heatDissipation) // 内区不考虑渗风
					}
				} else if d >= weather.WinterStart || d <= weather.WinterEnd { // 采暖季
					deltaT := s.HeatingTem - weather.AirTem[d*24+h]
					deltaG := s.HeatingTem - weather.GroTem[d*24+h]
					envelopeLoad := calculate_envelope_load(s, deltaT-winterTemCorrect, deltaG)
					heatDissipation := (s.PPSM*s.PHD+s.EHD*equipment_schedule[h])*s.SpaceArea + lightingEnergy
					if s.OutsideArea > 0 {
						infiltrationLoad := AirDensity * AirCapacity * deltaT * s.SpaceArea * s.SpaceHeight * s.ACH / 3.6
						rec[i][d][1] += non(envelopeLoad - heatDissipation + infiltrationLoad)
					} else {
						rec[i][d][1] += non(envelopeLoad - heatDissipation)
					}
				}
			}
			if d >= weather.SummerStart && d <= weather.SummerEnd {
				rec[i][d][0] = non(rec[i][d][0]+s.SummerSolar*s.Window_SHGC) / s.CoolingEER
			} else if d >= weather.WinterStart || d <= weather.WinterEnd {
				rec[i][d][1] = non(rec[i][d][1]-s.WinterSolar*s.Window_SHGC) / s.HeatingEER
			}
		}
	}
	// 后处理：输出能耗结果
	e_data.Months, e_data.Spaces = make([]EnergyItem, 12), make([]EnergyItem, len(e.Spaces))
	for i := 0; i < len(e.Spaces); i++ {
		for d := 0; d < 365; d++ {
			e_data.Total.CoolingEnergy += rec[i][d][0]
			e_data.Total.HeatingEnergy += rec[i][d][1]
			e_data.Total.LightingEnergy += rec[i][d][2]
			e_data.Spaces[i].CoolingEnergy += rec[i][d][0]
			e_data.Spaces[i].HeatingEnergy += rec[i][d][1]
			e_data.Spaces[i].LightingEnergy += rec[i][d][2]
		}
		for m := 0; m < 12; m++ {
			for _, v := range rec[i][months[m]:months[m+1]] {
				e_data.Months[m].CoolingEnergy += v[0]
				e_data.Months[m].HeatingEnergy += v[1]
				e_data.Months[m].LightingEnergy += v[2]
			}
		}
	}
}

func latitudeCorrection(latitude float64) MoosasWeather {
	weather := MoosasWeather{}
	if latitude > 0.74 { // 严寒地区
		summerTemCorrect, winterTemCorrect, summerRadCorrect, winterRadCorrect = 2.0, 4.0, 0.5689, 1.0543
		weather.SummerStart, weather.SummerEnd, weather.WinterStart, weather.WinterEnd = 151, 242, 293, 99
	} else if latitude > 0.62 { // 寒冷地区
		summerTemCorrect, winterTemCorrect, summerRadCorrect, winterRadCorrect = 3.0, 3.0, 0.5936, 0.6234
		weather.SummerStart, weather.SummerEnd, weather.WinterStart, weather.WinterEnd = 140, 262, 319, 73
	} else if latitude > 0.47 { // 夏热冬冷地区
		summerTemCorrect, winterTemCorrect, summerRadCorrect, winterRadCorrect = 4.0, 2.0, 0.9239, 0.4877
		weather.SummerStart, weather.SummerEnd, weather.WinterStart, weather.WinterEnd = 135, 272, 334, 58
	} else { // 夏热冬暖地区
		summerTemCorrect, winterTemCorrect, summerRadCorrect, winterRadCorrect = 5.0, 1.0, 0.8414, 0.3762
		weather.SummerStart, weather.SummerEnd, weather.WinterStart, weather.WinterEnd = 90, 303, 334, 58
	}
	return weather
}

func calculate_envelope_load(s MoosasSpace, deltaT, deltaG float64) float64 {
	el := (s.FacadeArea + s.RoofArea) * s.Wall_U * deltaT
	el += (s.WindowArea + s.SkylightArea) * s.Window_U * deltaT
	el += s.FloorArea * s.Wall_U * deltaG
	return el
}

func non(x float64) float64 {
	if x < 0 {
		return 0
	}
	return x
}

func convertResult(item EnergyItem, area float64) string {
	coolingEnergy := strconv.FormatFloat(item.CoolingEnergy/area/1000, 'f', 2, 64)
	heatingEnergy := strconv.FormatFloat(item.HeatingEnergy/area/1000, 'f', 2, 64)
	lightingEnergy := strconv.FormatFloat(item.LightingEnergy/area/1000, 'f', 2, 64)
	return coolingEnergy + "," + heatingEnergy + "," + lightingEnergy + "\n"
}
