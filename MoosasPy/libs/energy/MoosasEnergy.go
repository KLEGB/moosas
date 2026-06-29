package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"math"
	"os"
	"path"
	"path/filepath"
	"strconv"
	"strings"
)

// ═════════════════════════════════════════════════════════════
// 物理常量
// ═════════════════════════════════════════════════════════════

const (
	AirDensity    float64 = 1.29   // 空气密度 (kg/m³)
	AirCapacity   float64 = 1.40   // 空气比热容 (kJ/(kg·K)) — 公共建筑使用
	AirCapacityRe float64 = 0.717  // 空气比热容 (kJ/(kg·K)) — 居住建筑使用
	SolarConstant float64 = 1367.0 // 太阳常数 (W/m²)
)

// ═════════════════════════════════════════════════════════════
// 全局变量
// ═════════════════════════════════════════════════════════════

var (
	// 辐射修正系数（由气候区判断函数设置）
	summerRadiationCorrection float64 = 0.5936
	winterRadiationCorrection float64 = 0.6234

	// 公共建筑：周末修正回归系数
	weekendCorrectionAlphaT float64 = -1.83
	weekendCorrectionAlphaS float64 = 2.16

	// 居住建筑：蓄热温度修正
	summerTemperatureCorrection float64 = 3.0
	winterTemperatureCorrection float64 = 3.0

	// 居住建筑：硬编码灯光和设备作息（24小时）
	residentialLightingSchedule = []float64{
		0, 0, 0, 0, 0, 0.65, 0.65, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.4, 0.4, 0.6, 0.4, 0, 0,
	}
	residentialEquipmentSchedule = []float64{
		0, 0, 0, 0, 0, 0, 0.65, 0.75, 0.35, 0.2, 0.2, 0.4, 0.35, 0.2, 0.2, 0.2, 0.2, 0.4, 0.35, 0.35, 0.6, 0.4, 0, 0,
	}

	// 全局天气数据和能耗结果
	globalWeather      MoosasWeather
	monthStartDayIndex = []int{0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365}
	globalEnergyResult EnergyData
)

// ═════════════════════════════════════════════════════════════
// 作息表类型常量
// ═════════════════════════════════════════════════════════════

type ScheduleType int

const (
	ScheduleWeekly ScheduleType = iota
	ScheduleDaily
	ScheduleHourly
)

// ═════════════════════════════════════════════════════════════
// 数据结构定义
// ═════════════════════════════════════════════════════════════

// SimulationConfig 保存命令行解析后的模拟配置参数。
type SimulationConfig struct {
	InputFilePath       string  // 输入文件路径（位置参数，最后一个参数）
	OutputFilePath      string  // 输出文件路径（-o / -output）
	WeatherFilePath     string  // 天气文件路径（-w / -weather）
	ScheduleFilePath    string  // 作息表文件路径（-sch / -schedule），空字符串表示不使用
	BuildingType        int     // 建筑类型（-t / -type）：0=居住建筑，其他=公共建筑
	ExportHourly        int     // 是否输出逐时数据（-r / -hourly）：1=输出，0=不输出
	ExportDaily         int     // 是否输出逐日数据（-d / -daily）：1=输出，0=不输出
	ExportByZone        int     // 是否分空间输出（-z / -zone）：1=输出，0=不输出
	SiteLatitude        float64 // 场地纬度（-l / -lat），弧度制
	SiteAltitude        float64 // 场地海拔（-a / -alt），米
	BuildingShapeFactor float64 // 体形系数（-s / -shape）= 外表面积 / 体积
}

// SchedulableParam 表示一个"可作息化"的参数。
// 在 Energy.i 中，以下 8 个参数的字段值既可以是数字（固定值），也可以是作息表名称（逐时变化值）。
type SchedulableParam struct {
	IsSchedule      bool           // true=使用作息表, false=使用固定值
	FixedValue      float64        // 固定值（IsSchedule=false 时有效）
	ScheduleFactors *[8760]float64 // 作息表展开后的 8760 个逐时数值指针（IsSchedule=true 时有效）
}

// getValueAtHour 返回该参数在第 absHourIdx 小时的实际数值。
func (sp *SchedulableParam) getValueAtHour(absHourIdx int) float64 {
	if sp.IsSchedule && sp.ScheduleFactors != nil {
		return sp.ScheduleFactors[absHourIdx]
	}
	return sp.FixedValue
}

// MoosasEnergy 是建筑能耗计算的主体结构。
type MoosasEnergy struct {
	WeatherFilePath       string
	Latitude              float64
	Altitude              float64
	ShapeCoefficient      float64
	AverageEnvelopeK      float64 // 公共建筑：平均传热系数
	WeekendLoadCorrection float64 // 公共建筑：周末负荷修正系数
	Spaces                []MoosasSpace
}

// MoosasSpace 描述单个功能空间的物理和运行参数。
// 8 个参数使用 SchedulableParam 类型，支持固定值或作息表名称。
type MoosasSpace struct {
	StoryHeight             float64          // 层高 (m)
	FloorArea               float64          // 建筑面积 (m²)
	PerimeterZoneArea       float64          // 外区面积 (m²)
	ExteriorWallArea        float64          // 外墙面积 (m²)
	ExteriorWindowArea      float64          // 外窗面积 (m²)
	RoofArea                float64          // 屋顶面积 (m²)
	SkylightArea            float64          // 天窗面积 (m²)
	GroundFloorArea         float64          // 接地楼板面积 (m²)
	SeasonalSummerSolarGain SchedulableParam // 夏季辐射得热总量 (Wh) 或逐时辐射得热 (Wh)
	SeasonalWinterSolarGain SchedulableParam // 冬季辐射得热总量 (Wh) 或逐时辐射得热 (Wh)
	WallUValue              float64          // 外墙传热系数 (W/(m²·K))
	WindowUValue            float64          // 外窗传热系数 (W/(m²·K))
	WindowSHGC              float64          // 外窗太阳得热系数
	CoolingSetpointTemp     SchedulableParam // 空调设定温度 (°C)
	CoolingSetpointHumidity SchedulableParam // 空调设定相对湿度 (0~1)
	HeatingSetpointTemp     SchedulableParam // 采暖设定温度 (°C)
	CoolingEER              float64          // 空调能效比
	HeatingEER              float64          // 采暖能效比
	OccupancyStartHour      int              // 运行开始时刻
	OccupancyEndHour        int              // 运行结束时刻
	OccupantDensity         SchedulableParam // 人员密度 (人/m²)
	FreshAirPerPerson       SchedulableParam // 人均新风量 (m³/(h·人))
	OccupantHeatGain        SchedulableParam // 人员散热强度 (W/人)
	EquipmentHeatGain       SchedulableParam // 设备散热强度 (W/m²)
	LightingHeatGain        SchedulableParam // 灯光散热强度 (W/m²)
	InfiltrationACH         float64          // 工作时段换气次数 (次/h)
	NightVentilationACH     float64          // 夜间换气次数 (次/h)
}

// MoosasWeather 保存气候分区的季节边界和逐时气象数据。
type MoosasWeather struct {
	CoolingSeasonStart int
	CoolingSeasonEnd   int
	HeatingSeasonStart int
	HeatingSeasonEnd   int
	HourlyDryBulbTemp  []float64 // 逐时干球温度 (°C)
	HourlyDewPointTemp []float64 // 逐时露点温度 (°C) — 仅公共建筑使用
	HourlyGroundTemp   []float64 // 逐时地面温度 (°C)
}

// MoosasSolar 保存太阳辐射计算的中间变量（仅公共建筑使用）。
type MoosasSolar struct {
	solarDeclination      float64
	daylightHours         float64
	sunriseHour           int
	sunsetHour            int
	extraterrestrialIrrad float64
	hottelCoeffA1         float64
	hottelCoeffA2         float64
	hottelCoeffA3         float64
}

// EnergyData 是最终输出的能耗结果容器。
type EnergyData struct {
	TotalAnnual  EnergyItem
	BySpace      []EnergyItem
	ByMonth      []EnergyItem
	ByDay        []EnergyItem   // 逐日（365项），仅 ExportDaily=1 时填充
	ByHour       []EnergyItem   // 逐时（8760项），仅 ExportHourly=1 时填充
	BySpaceMonth [][]EnergyItem // 分空间逐月，仅 ExportByZone=1 时填充
	BySpaceDay   [][]EnergyItem // 分空间逐日，仅 ExportByZone=1 且 ExportDaily=1 时填充
	BySpaceHour  [][]EnergyItem // 分空间逐时，仅 ExportByZone=1 且 ExportHourly=1 时填充
}

// EnergyItem 是能耗三元组，单位为 Wh。
type EnergyItem struct {
	CoolingEnergy  float64
	HeatingEnergy  float64
	LightingEnergy float64
}

// Schedule 保存一条作息记录。
type Schedule struct {
	Name          string
	Type          ScheduleType
	HourlyFactors [8760]float64
}

// ScheduleLibrary 是以作息名称为键的作息表集合。
type ScheduleLibrary map[string]*Schedule

// ═════════════════════════════════════════════════════════════
// 作息表读取与转换
// ═════════════════════════════════════════════════════════════

// convertDailyToHourly 将 24 个数值（Daily 作息）展开为全年 8760 个值。
func convertDailyToHourly(dailyFactors []float64) [8760]float64 {
	var hourlyFactors [8760]float64
	for dayIdx := 0; dayIdx < 365; dayIdx++ {
		for hourIdx := 0; hourIdx < 24; hourIdx++ {
			if hourIdx < len(dailyFactors) {
				hourlyFactors[dayIdx*24+hourIdx] = dailyFactors[hourIdx]
			}
		}
	}
	return hourlyFactors
}

// convertWeeklyToHourly 将 Weekly 作息展开为全年 8760 个值。
// dayIdx=0 为周一，dayIdx%7 映射到 weeklyDailyNames[0..6]。
func convertWeeklyToHourly(weeklyDailyNames []string, lib ScheduleLibrary) [8760]float64 {
	var hourlyFactors [8760]float64
	for dayIdx := 0; dayIdx < 365; dayIdx++ {
		weekdayIdx := dayIdx % 7
		if weekdayIdx < len(weeklyDailyNames) {
			dailyScheduleName := strings.TrimSpace(weeklyDailyNames[weekdayIdx])
			dailySch, exists := lib[dailyScheduleName]
			if !exists {
				log.Fatalf("Error: Weekly schedule references Daily schedule '%s' which does not exist in the schedule library.", dailyScheduleName)
			}
			for hourIdx := 0; hourIdx < 24; hourIdx++ {
				hourlyFactors[dayIdx*24+hourIdx] = dailySch.HourlyFactors[hourIdx]
			}
		}
	}
	return hourlyFactors
}

// loadScheduleFile 读取作息表文件，返回 ScheduleLibrary。
// 若文件路径为空，返回空库。若文件不存在或解析失败，直接报错退出。
func loadScheduleFile(filePath string) ScheduleLibrary {
	lib := make(ScheduleLibrary)
	if filePath == "" {
		return lib
	}

	scheduleFile, err := os.Open(filePath)
	if err != nil {
		log.Fatalf("Error: cannot open schedule file '%s': %v", filePath, err)
	}
	defer scheduleFile.Close()

	csvReader := csv.NewReader(scheduleFile)
	csvReader.FieldsPerRecord = -1
	rows, err := csvReader.ReadAll()
	if err != nil {
		log.Fatalf("Error: cannot parse schedule file '%s': %v", filePath, err)
	}

	// 第一遍：解析 Daily 和 Hourly 作息
	for _, row := range rows {
		if len(row) < 2 {
			continue
		}
		scheduleName := strings.TrimSpace(row[0])
		scheduleTypeStr := strings.TrimSpace(row[1])

		switch scheduleTypeStr {
		case "Daily":
			if len(row) < 26 {
				log.Fatalf("Error: Daily schedule '%s' requires 24 data values but only %d provided.", scheduleName, len(row)-2)
			}
			sch := &Schedule{Name: scheduleName, Type: ScheduleDaily}
			dailyFactors := make([]float64, 0, 24)
			for colIdx := 2; colIdx < len(row) && len(dailyFactors) < 24; colIdx++ {
				val, parseErr := strconv.ParseFloat(strings.TrimSpace(row[colIdx]), 64)
				if parseErr != nil {
					log.Fatalf("Error: Daily schedule '%s' has invalid value at column %d: '%s'", scheduleName, colIdx, row[colIdx])
				}
				dailyFactors = append(dailyFactors, val)
			}
			sch.HourlyFactors = convertDailyToHourly(dailyFactors)
			lib[scheduleName] = sch

		case "Hourly":
			if len(row) < 8762 {
				log.Fatalf("Error: Hourly schedule '%s' requires 8760 data values but only %d provided.", scheduleName, len(row)-2)
			}
			sch := &Schedule{Name: scheduleName, Type: ScheduleHourly}
			for hourIdx := 0; hourIdx < 8760; hourIdx++ {
				val, parseErr := strconv.ParseFloat(strings.TrimSpace(row[hourIdx+2]), 64)
				if parseErr != nil {
					log.Fatalf("Error: Hourly schedule '%s' has invalid value at column %d: '%s'", scheduleName, hourIdx+2, row[hourIdx+2])
				}
				sch.HourlyFactors[hourIdx] = val
			}
			lib[scheduleName] = sch
		}
	}

	// 第二遍：解析 Weekly 作息（依赖已解析的 Daily 作息）
	for _, row := range rows {
		if len(row) < 2 {
			continue
		}
		scheduleName := strings.TrimSpace(row[0])
		scheduleTypeStr := strings.TrimSpace(row[1])

		if scheduleTypeStr == "Weekly" {
			if len(row) < 9 {
				log.Fatalf("Error: Weekly schedule '%s' requires 7 Daily schedule names but only %d provided.", scheduleName, len(row)-2)
			}
			sch := &Schedule{Name: scheduleName, Type: ScheduleWeekly}
			weeklyDailyNames := make([]string, 0, 7)
			for colIdx := 2; colIdx < len(row) && len(weeklyDailyNames) < 7; colIdx++ {
				weeklyDailyNames = append(weeklyDailyNames, strings.TrimSpace(row[colIdx]))
			}
			sch.HourlyFactors = convertWeeklyToHourly(weeklyDailyNames, lib)
			lib[scheduleName] = sch
		}
	}

	return lib
}

// parseSchedulableParam 解析一个字段值：先尝试 ParseFloat，成功则为固定值；
// 失败则视为作息表名称去库中查找。找不到则报错退出。
func parseSchedulableParam(fieldValue, fieldName string, scheduleLib ScheduleLibrary) SchedulableParam {
	fieldValue = strings.TrimSpace(fieldValue)
	val, err := strconv.ParseFloat(fieldValue, 64)
	if err == nil {
		return SchedulableParam{IsSchedule: false, FixedValue: val}
	}
	// 不是数字，视为作息表名称
	if len(scheduleLib) == 0 {
		log.Fatalf("Error: field '%s' has value '%s' which is not a number, but no schedule file was loaded. Use -sch to specify a schedule file.", fieldName, fieldValue)
	}
	sch, exists := scheduleLib[fieldValue]
	if !exists {
		available := make([]string, 0, len(scheduleLib))
		for k := range scheduleLib {
			available = append(available, k)
		}
		log.Fatalf("Error: field '%s' references schedule '%s' which does not exist in the schedule library. Available schedules: %s", fieldName, fieldValue, strings.Join(available, ", "))
	}
	return SchedulableParam{IsSchedule: true, ScheduleFactors: &sch.HourlyFactors}
}

func seasonAwareHourlySolarGain(param SchedulableParam, absHourIdx int, inSeason bool) float64 {
	if !inSeason {
		return 0.0
	}
	if param.IsSchedule {
		return param.getValueAtHour(absHourIdx)
	}
	return 0.0
}

func seasonAwareDailySolarGain(param SchedulableParam, dayIdx int, inSeason bool) float64 {
	if !inSeason {
		return 0.0
	}
	if param.IsSchedule {
		daySum := 0.0
		baseHour := dayIdx * 24
		for hourIdx := 0; hourIdx < 24; hourIdx++ {
			daySum += param.getValueAtHour(baseHour + hourIdx)
		}
		return daySum
	}
	return 0.0
}

func adjustedSeasonalSolarGain(param SchedulableParam, correction float64, seasonDays int) float64 {
	if param.IsSchedule {
		return 0.0
	}
	if seasonDays <= 0 {
		return 0.0
	}
	return param.FixedValue * correction / float64(seasonDays)
}

// ═════════════════════════════════════════════════════════════
// 命令行入口
// ═════════════════════════════════════════════════════════════

func printHelp() {
	fmt.Println("MoosasEnergy — Building Energy Analysis Tool (Residential + Public)")
	fmt.Println("Usage: MoosasEnergy [-h,-w,...] inputFile.i")
	fmt.Println("")
	fmt.Println("Required:")
	fmt.Println("  inputFile.i            Input file path (last argument)")
	fmt.Println("")
	fmt.Println("Options:")
	fmt.Println("  -h / -help             Print this help information")
	fmt.Println("  -w / -weather <path>   Weather file path (DeST CSV format)")
	fmt.Println("  -t / -type <int>       Building type: 0=RESIDENTIAL, 1=OFFICE, 2=HOTEL, 3=SCHOOL, 4=COMMERCIAL, 5=OPERA, 6=HOSPITAL")
	fmt.Println("  -l / -lat <float>      Latitude of the site (radians)")
	fmt.Println("  -a / -alt <float>      Altitude of the site (meters)")
	fmt.Println("  -s / -shape <float>    Shape factor = gross surface area (m²) / gross building volume (m³)")
	fmt.Println("  -o / -output <path>    Output file path (default: MoosasEnergy.o)")
	fmt.Println("  -d / -daily <1/0>      Export daily results (default: 0)")
	fmt.Println("  -r / -hourly <1/0>     Export hourly results (default: 0)")
	fmt.Println("  -z / -zone <1/0>       Export results by zone/space (default: 0)")
	fmt.Println("  -sch / -schedule <path> Schedule file path (CSV format)")
}

func main() {
	exePath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}
	res, _ := filepath.EvalSymlinks(filepath.Dir(exePath))
	res = path.Join(res, "..\\..\\db\\weather\\545110.csv")

	config := SimulationConfig{
		WeatherFilePath:     res,
		OutputFilePath:      "MoosasEnergy.o",
		BuildingType:        0,
		ExportHourly:        0,
		ExportDaily:         0,
		ExportByZone:        0,
		SiteLatitude:        0.0,
		SiteAltitude:        0.0,
		BuildingShapeFactor: 0.78,
	}

	for i := 1; i < len(os.Args); {
		switch os.Args[i] {
		case "-h", "-help":
			printHelp()
			return
		case "-w", "-weather":
			config.WeatherFilePath, _ = filepath.Abs(os.Args[i+1])
			i += 2
			continue
		case "-o", "-output":
			config.OutputFilePath, _ = filepath.Abs(os.Args[i+1])
			i += 2
			continue
		case "-t", "-type":
			config.BuildingType, _ = strconv.Atoi(os.Args[i+1])
			i += 2
			continue
		case "-l", "-lat":
			config.SiteLatitude, _ = strconv.ParseFloat(os.Args[i+1], 64)
			i += 2
			continue
		case "-a", "-alt":
			config.SiteAltitude, _ = strconv.ParseFloat(os.Args[i+1], 64)
			i += 2
			continue
		case "-s", "-shape":
			config.BuildingShapeFactor, _ = strconv.ParseFloat(os.Args[i+1], 64)
			i += 2
			continue
		case "-d", "-daily":
			config.ExportDaily, _ = strconv.Atoi(os.Args[i+1])
			i += 2
			continue
		case "-r", "-hourly":
			config.ExportHourly, _ = strconv.Atoi(os.Args[i+1])
			i += 2
			continue
		case "-z", "-zone":
			config.ExportByZone, _ = strconv.Atoi(os.Args[i+1])
			i += 2
			continue
		case "-sch", "-schedule":
			config.ScheduleFilePath, _ = filepath.Abs(os.Args[i+1])
			i += 2
			continue
		}
		i++
	}

	config.InputFilePath, _ = filepath.Abs(os.Args[len(os.Args)-1])
	fileInfo, err := os.Lstat(config.InputFilePath)
	if err != nil {
		fmt.Println("Invalid input file. Please check:", config.InputFilePath)
		return
	}
	if !fileInfo.Mode().IsRegular() {
		fmt.Println("Input file path is not a file. Please check:", config.InputFilePath)
		return
	}

	runSimulation(config)
}

// ═════════════════════════════════════════════════════════════
// 模拟主流程
// ═════════════════════════════════════════════════════════════

func runSimulation(config SimulationConfig) {
	// ── 读取输入文件 ────────────────────────────────
	inputBytes, _ := os.ReadFile(config.InputFilePath)
	inputLines := strings.Split(string(inputBytes), "\n")

	// ── 加载作息表（若指定） ──────────────────────────
	scheduleLib := loadScheduleFile(config.ScheduleFilePath)

	// ── 构建建筑模型 ────────────────────────────────
	buildingModel := MoosasEnergy{
		WeatherFilePath:  config.WeatherFilePath,
		Latitude:         config.SiteLatitude,
		Altitude:         config.SiteAltitude,
		ShapeCoefficient: config.BuildingShapeFactor,
	}

	for _, line := range inputLines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "!") {
			continue
		}
		fields := strings.Split(line, ",")
		if len(fields) < 27 {
			continue
		}

		// 字段 0~12：几何和热工参数（固定数值）
		storyHeight, _ := strconv.ParseFloat(fields[0], 64)
		floorArea, _ := strconv.ParseFloat(fields[1], 64)
		perimeterZoneArea, _ := strconv.ParseFloat(fields[2], 64)
		exteriorWallArea, _ := strconv.ParseFloat(fields[3], 64)
		exteriorWindowArea, _ := strconv.ParseFloat(fields[4], 64)
		roofArea, _ := strconv.ParseFloat(fields[5], 64)
		skylightArea, _ := strconv.ParseFloat(fields[6], 64)
		groundFloorArea, _ := strconv.ParseFloat(fields[7], 64)
		summerSolarGain := parseSchedulableParam(fields[8], "SummerSolarGain", scheduleLib)
		winterSolarGain := parseSchedulableParam(fields[9], "WinterSolarGain", scheduleLib)
		wallUValue, _ := strconv.ParseFloat(fields[10], 64)
		windowUValue, _ := strconv.ParseFloat(fields[11], 64)
		windowSHGC, _ := strconv.ParseFloat(fields[12], 64)

		// 字段 13~15：可作息化参数（温度/湿度设定）
		coolingSetpointTemp := parseSchedulableParam(fields[13], "CoolingSetpointTemp", scheduleLib)
		coolingSetpointHumidity := parseSchedulableParam(fields[14], "CoolingSetpointHumidity", scheduleLib)
		heatingSetpointTemp := parseSchedulableParam(fields[15], "HeatingSetpointTemp", scheduleLib)

		// 字段 16~19：固定数值
		coolingEER, _ := strconv.ParseFloat(fields[16], 64)
		heatingEER, _ := strconv.ParseFloat(fields[17], 64)
		occupancyStartHour, _ := strconv.Atoi(fields[18])
		occupancyEndHour, _ := strconv.Atoi(fields[19])

		// 字段 20~24：可作息化参数（人员/设备/灯光）
		occupantDensity := parseSchedulableParam(fields[20], "OccupantDensity", scheduleLib)
		freshAirPerPerson := parseSchedulableParam(fields[21], "FreshAirPerPerson", scheduleLib)
		occupantHeatGain := parseSchedulableParam(fields[22], "OccupantHeatGain", scheduleLib)
		equipmentHeatGain := parseSchedulableParam(fields[23], "EquipmentHeatGain", scheduleLib)
		lightingHeatGain := parseSchedulableParam(fields[24], "LightingHeatGain", scheduleLib)

		// 字段 25~26：固定数值
		infiltrationACH, _ := strconv.ParseFloat(fields[25], 64)
		nightVentACH, parseErr := strconv.ParseFloat(strings.TrimSpace(fields[26]), 64)
		if parseErr != nil {
			nightVentACH, _ = strconv.ParseFloat(fields[26][:len(fields[26])-1], 64)
		}

		buildingModel.Spaces = append(buildingModel.Spaces, MoosasSpace{
			StoryHeight:             storyHeight,
			FloorArea:               floorArea,
			PerimeterZoneArea:       perimeterZoneArea,
			ExteriorWallArea:        exteriorWallArea,
			ExteriorWindowArea:      exteriorWindowArea,
			RoofArea:                roofArea,
			SkylightArea:            skylightArea,
			GroundFloorArea:         groundFloorArea,
			SeasonalSummerSolarGain: summerSolarGain,
			SeasonalWinterSolarGain: winterSolarGain,
			WallUValue:              wallUValue,
			WindowUValue:            windowUValue,
			WindowSHGC:              windowSHGC,
			CoolingSetpointTemp:     coolingSetpointTemp,
			CoolingSetpointHumidity: coolingSetpointHumidity,
			HeatingSetpointTemp:     heatingSetpointTemp,
			CoolingEER:              coolingEER,
			HeatingEER:              heatingEER,
			OccupancyStartHour:      occupancyStartHour,
			OccupancyEndHour:        occupancyEndHour,
			OccupantDensity:         occupantDensity,
			FreshAirPerPerson:       freshAirPerPerson,
			OccupantHeatGain:        occupantHeatGain,
			EquipmentHeatGain:       equipmentHeatGain,
			LightingHeatGain:        lightingHeatGain,
			InfiltrationACH:         infiltrationACH,
			NightVentilationACH:     nightVentACH,
		})
	}

	// ── 执行能耗计算（按建筑类型分流） ──────────────
	if config.BuildingType == 0 {
		buildingModel.AnalysisResidential(config.ExportDaily, config.ExportHourly, config.ExportByZone)
	} else {
		buildingModel.AnalysisPublic(config.ExportDaily, config.ExportHourly, config.ExportByZone)
	}

	// ── 格式化输出（两种建筑类型共享输出格式） ──────────
	totalBuildingArea := float64(0)
	for _, space := range buildingModel.Spaces {
		totalBuildingArea += space.FloorArea
	}

	outputText := "!TOTAL:\n!Cooling,Heating,Lighting\n"
	outputText += formatEnergyItem(globalEnergyResult.TotalAnnual, totalBuildingArea)
	outputText += ";\n!SPACE RESULT:\n!Cooling,Heating,Lighting\n"
	for spaceIdx, spaceResult := range globalEnergyResult.BySpace {
		outputText += formatEnergyItem(spaceResult, buildingModel.Spaces[spaceIdx].FloorArea)
	}
	outputText += ";\n!MONTH RESULT:\n!Cooling,Heating,Lighting\n"
	for _, monthResult := range globalEnergyResult.ByMonth {
		outputText += formatEnergyItem(monthResult, totalBuildingArea)
	}

	if config.ExportDaily == 1 {
		outputText += ";\n!DAY RESULT:\n!Cooling,Heating,Lighting\n"
		for _, dayResult := range globalEnergyResult.ByDay {
			outputText += formatEnergyItemWithPrecision(dayResult, totalBuildingArea, 4)
		}
	}

	if config.ExportHourly == 1 {
		outputText += ";\n!HOUR RESULT:\n!Cooling,Heating,Lighting\n"
		for _, hourResult := range globalEnergyResult.ByHour {
			outputText += formatEnergyItemWithPrecision(hourResult, totalBuildingArea, 5)
		}
	}

	if config.ExportByZone == 1 {
		outputText += ";\n!ZONE MONTH RESULT:\n!SpaceIndex,Cooling,Heating,Lighting\n"
		for spaceIdx, spaceMonthResults := range globalEnergyResult.BySpaceMonth {
			for _, monthResult := range spaceMonthResults {
				outputText += formatEnergyItemWithZone(spaceIdx, monthResult, buildingModel.Spaces[spaceIdx].FloorArea)
			}
		}
	}

	if config.ExportByZone == 1 && config.ExportDaily == 1 {
		outputText += ";\n!ZONE DAY RESULT:\n!SpaceIndex,Cooling,Heating,Lighting\n"
		for spaceIdx, spaceDayResults := range globalEnergyResult.BySpaceDay {
			for _, dayResult := range spaceDayResults {
				outputText += formatEnergyItemWithZonePrecision(spaceIdx, dayResult, buildingModel.Spaces[spaceIdx].FloorArea, 4)
			}
		}
	}

	if config.ExportByZone == 1 && config.ExportHourly == 1 {
		outputText += ";\n!ZONE HOUR RESULT:\n!SpaceIndex,Cooling,Heating,Lighting\n"
		for spaceIdx, spaceHourResults := range globalEnergyResult.BySpaceHour {
			for _, hourResult := range spaceHourResults {
				outputText += formatEnergyItemWithZonePrecision(spaceIdx, hourResult, buildingModel.Spaces[spaceIdx].FloorArea, 5)
			}
		}
	}

	os.Remove(config.OutputFilePath)
	outputFile, _ := os.Create(config.OutputFilePath)
	defer outputFile.Close()
	io.WriteString(outputFile, strings.TrimRight(outputText, "\n"))
}

// ═════════════════════════════════════════════════════════════
// 居住建筑能耗计算核心
// ═════════════════════════════════════════════════════════════

// AnalysisResidential 执行居住建筑全年逐时能耗计算。
//
// 与公共建筑的主要差异：
//   - 使用 latitudeCorrection() 确定气候区（设置温度修正系数）
//   - 天气数据仅使用干球温度和地面温度（无露点温度）
//   - 围护结构负荷无周末修正系数
//   - 蓄热修正使用固定温度偏移量（summerTemperatureCorrection / winterTemperatureCorrection）
//   - 无新风负荷和焓差计算
//   - 灯光和设备使用居住建筑专用作息（可被 SchedulableParam 覆盖）
//   - 渗风使用 AirCapacityRe（0.717）而非 AirCapacity（1.40）
func (buildingModel MoosasEnergy) AnalysisResidential(exportDaily, exportHourly, exportByZone int) {
	// ── 前处理：气候区判断与天气数据读取 ────────────
	globalWeather = determineClimateZoneResidential(buildingModel.Latitude)

	weatherFile, _ := os.Open(buildingModel.WeatherFilePath)
	weatherRows, _ := csv.NewReader(weatherFile).ReadAll()
	for _, row := range weatherRows {
		dryBulbTemp, _ := strconv.ParseFloat(row[3], 64)
		globalWeather.HourlyDryBulbTemp = append(globalWeather.HourlyDryBulbTemp, dryBulbTemp)
		groundTemp, _ := strconv.ParseFloat(row[7], 64)
		globalWeather.HourlyGroundTemp = append(globalWeather.HourlyGroundTemp, groundTemp)
	}

	// ── 分配计算缓存 ──────────────────────────────
	numSpaces := len(buildingModel.Spaces)

	dailyLoadCache := make([][][]float64, numSpaces)
	for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
		dailyLoadCache[spaceIdx] = make([][]float64, 365)
		for dayIdx := 0; dayIdx < 365; dayIdx++ {
			dailyLoadCache[spaceIdx][dayIdx] = make([]float64, 3)
		}
	}

	needHourlyCache := exportDaily == 1 || exportHourly == 1
	var hourlyLoadCache [][][][]float64
	if needHourlyCache {
		hourlyLoadCache = make([][][][]float64, numSpaces)
		for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
			hourlyLoadCache[spaceIdx] = make([][][]float64, 365)
			for dayIdx := 0; dayIdx < 365; dayIdx++ {
				hourlyLoadCache[spaceIdx][dayIdx] = make([][]float64, 24)
				for hourIdx := 0; hourIdx < 24; hourIdx++ {
					hourlyLoadCache[spaceIdx][dayIdx][hourIdx] = make([]float64, 3)
				}
			}
		}
	}

	// ── 迭代计算：逐空间 × 逐天 × 逐小时 ────────────
	for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
		space := buildingModel.Spaces[spaceIdx]

		// Fixed-value solar input keeps the legacy semantics:
		// seasonal total (Wh) -> climate correction -> average daily gain.
		coolingSeasonDays := globalWeather.CoolingSeasonEnd - globalWeather.CoolingSeasonStart + 1
		heatingSeasonDays := 365 - globalWeather.HeatingSeasonStart + globalWeather.HeatingSeasonEnd + 1
		adjustedSummerSolarGain := adjustedSeasonalSolarGain(space.SeasonalSummerSolarGain, summerRadiationCorrection, coolingSeasonDays)
		adjustedWinterSolarGain := adjustedSeasonalSolarGain(space.SeasonalWinterSolarGain, winterRadiationCorrection, heatingSeasonDays)

		for dayIdx := 0; dayIdx < 365; dayIdx++ {
			for hourIdx := 0; hourIdx < 24; hourIdx++ {
				absHourIdx := dayIdx*24 + hourIdx

				// 获取该小时的可作息化参数值
				currentCoolingSetpointTemp := space.CoolingSetpointTemp.getValueAtHour(absHourIdx)
				currentHeatingSetpointTemp := space.HeatingSetpointTemp.getValueAtHour(absHourIdx)
				currentOccupantDensity := space.OccupantDensity.getValueAtHour(absHourIdx)
				currentOccupantHeatGain := space.OccupantHeatGain.getValueAtHour(absHourIdx)
				currentEquipmentHeatGain := space.EquipmentHeatGain.getValueAtHour(absHourIdx)
				currentLightingHeatGain := space.LightingHeatGain.getValueAtHour(absHourIdx)

				// 照明能耗：使用居住建筑硬编码作息 × 灯光散热强度
				lightingEnergy := currentLightingHeatGain * residentialLightingSchedule[hourIdx] * space.FloorArea

				dailyLoadCache[spaceIdx][dayIdx][2] += lightingEnergy
				if needHourlyCache {
					hourlyLoadCache[spaceIdx][dayIdx][hourIdx][2] += lightingEnergy
				}

				if dayIdx >= globalWeather.CoolingSeasonStart && dayIdx <= globalWeather.CoolingSeasonEnd {
					// ── 空调季：计算制冷负荷 ──────────────────
					deltaT := globalWeather.HourlyDryBulbTemp[absHourIdx] - currentCoolingSetpointTemp
					deltaG := globalWeather.HourlyGroundTemp[absHourIdx] - currentCoolingSetpointTemp
					envelopeLoad := calcEnvelopeHeatTransferLoadResidential(space, deltaT+summerTemperatureCorrection, deltaG)
					heatDissipation := (currentOccupantDensity*currentOccupantHeatGain+currentEquipmentHeatGain*residentialEquipmentSchedule[hourIdx])*space.FloorArea + lightingEnergy

					coolingLoad := float64(0)
					if space.PerimeterZoneArea > 0 {
						infiltrationLoad := AirDensity * AirCapacityRe * deltaT * space.FloorArea * space.StoryHeight * space.InfiltrationACH / 3.6
						coolingLoad = clampToPositive(envelopeLoad + heatDissipation + infiltrationLoad)
					} else {
						coolingLoad = clampToPositive(envelopeLoad + heatDissipation)
					}

					dailyLoadCache[spaceIdx][dayIdx][0] += coolingLoad
					if needHourlyCache {
						hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0] += coolingLoad
					}

				} else if dayIdx >= globalWeather.HeatingSeasonStart || dayIdx <= globalWeather.HeatingSeasonEnd {
					// ── 采暖季：计算采暖负荷 ──────────────────
					deltaT := currentHeatingSetpointTemp - globalWeather.HourlyDryBulbTemp[absHourIdx]
					deltaG := currentHeatingSetpointTemp - globalWeather.HourlyGroundTemp[absHourIdx]
					envelopeLoad := calcEnvelopeHeatTransferLoadResidential(space, deltaT-winterTemperatureCorrection, deltaG)
					heatDissipation := (currentOccupantDensity*currentOccupantHeatGain+currentEquipmentHeatGain*residentialEquipmentSchedule[hourIdx])*space.FloorArea + lightingEnergy

					heatingLoad := float64(0)
					if space.PerimeterZoneArea > 0 {
						infiltrationLoad := AirDensity * AirCapacityRe * deltaT * space.FloorArea * space.StoryHeight * space.InfiltrationACH / 3.6
						heatingLoad = clampToPositive(envelopeLoad - heatDissipation + infiltrationLoad)
					} else {
						heatingLoad = clampToPositive(envelopeLoad - heatDissipation)
					}

					dailyLoadCache[spaceIdx][dayIdx][1] += heatingLoad
					if needHourlyCache {
						hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1] += heatingLoad
					}
				}
			}

			// 日结束后：叠加辐射得热修正并除以能效比
			if dayIdx >= globalWeather.CoolingSeasonStart && dayIdx <= globalWeather.CoolingSeasonEnd {
				summerDailySolarGain := adjustedSummerSolarGain
				if space.SeasonalSummerSolarGain.IsSchedule {
					summerDailySolarGain = seasonAwareDailySolarGain(space.SeasonalSummerSolarGain, dayIdx, true)
				}
				dailyLoadCache[spaceIdx][dayIdx][0] = clampToPositive(dailyLoadCache[spaceIdx][dayIdx][0]+summerDailySolarGain*space.WindowSHGC) / space.CoolingEER
				if needHourlyCache {
					if space.SeasonalSummerSolarGain.IsSchedule {
						for hourIdx := 0; hourIdx < 24; hourIdx++ {
							absHourIdx := dayIdx*24 + hourIdx
							hourlySolarGain := seasonAwareHourlySolarGain(space.SeasonalSummerSolarGain, absHourIdx, true) * space.WindowSHGC
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]+hourlySolarGain) / space.CoolingEER
						}
					} else {
						numWorkHours := 24 // 居住建筑全天运行
						solarGainPerHour := summerDailySolarGain * space.WindowSHGC / float64(numWorkHours)
						for hourIdx := 0; hourIdx < 24; hourIdx++ {
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]+solarGainPerHour) / space.CoolingEER
						}
					}
				}
			} else if dayIdx >= globalWeather.HeatingSeasonStart || dayIdx <= globalWeather.HeatingSeasonEnd {
				winterDailySolarGain := adjustedWinterSolarGain
				if space.SeasonalWinterSolarGain.IsSchedule {
					winterDailySolarGain = seasonAwareDailySolarGain(space.SeasonalWinterSolarGain, dayIdx, true)
				}
				dailyLoadCache[spaceIdx][dayIdx][1] = clampToPositive(dailyLoadCache[spaceIdx][dayIdx][1]-winterDailySolarGain*space.WindowSHGC) / space.HeatingEER
				if needHourlyCache {
					if space.SeasonalWinterSolarGain.IsSchedule {
						for hourIdx := 0; hourIdx < 24; hourIdx++ {
							absHourIdx := dayIdx*24 + hourIdx
							hourlySolarGain := seasonAwareHourlySolarGain(space.SeasonalWinterSolarGain, absHourIdx, true) * space.WindowSHGC
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]-hourlySolarGain) / space.HeatingEER
						}
					} else {
						numWorkHours := 24
						solarGainPerHour := winterDailySolarGain * space.WindowSHGC / float64(numWorkHours)
						for hourIdx := 0; hourIdx < 24; hourIdx++ {
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]-solarGainPerHour) / space.HeatingEER
						}
					}
				}
			}
		} // 天循环结束
	} // 空间循环结束

	// ── 后处理：汇总能耗结果（与公共建筑共享逻辑） ──
	aggregateResults(numSpaces, dailyLoadCache, hourlyLoadCache, needHourlyCache, exportDaily, exportHourly, exportByZone)
}

// ═════════════════════════════════════════════════════════════
// 公共建筑能耗计算核心
// ═════════════════════════════════════════════════════════════

// AnalysisPublic 执行公共建筑全年逐时能耗计算。
//
// 与居住建筑的主要差异：
//   - 使用 determineClimateZonePublic() 确定气候区（设置周末修正系数）
//   - 天气数据使用干球温度、露点温度和地面温度
//   - 围护结构负荷有周末修正系数
//   - 蓄热修正使用动态计算（calcNightThermalMassCorrection）
//   - 有新风负荷和焓差计算
//   - 照明使用太阳辐射采光模型（calcLightingEnergy）
//   - 渗风使用 AirCapacity（1.40）
func (buildingModel MoosasEnergy) AnalysisPublic(exportDaily, exportHourly, exportByZone int) {
	// ── 前处理：气候区判断与天气数据读取 ────────────
	globalWeather = determineClimateZonePublic(buildingModel.Latitude)

	weatherFile, _ := os.Open(buildingModel.WeatherFilePath)
	weatherRows, _ := csv.NewReader(weatherFile).ReadAll()
	for _, row := range weatherRows {
		dryBulbTemp, _ := strconv.ParseFloat(row[3], 64)
		globalWeather.HourlyDryBulbTemp = append(globalWeather.HourlyDryBulbTemp, dryBulbTemp)
		dewPointTemp, _ := strconv.ParseFloat(row[4], 64)
		globalWeather.HourlyDewPointTemp = append(globalWeather.HourlyDewPointTemp, dewPointTemp)
		groundTemp, _ := strconv.ParseFloat(row[7], 64)
		globalWeather.HourlyGroundTemp = append(globalWeather.HourlyGroundTemp, groundTemp)
	}

	// 计算建筑平均传热系数
	totalEnvelopeArea, totalEnvelopeAreaTimesK := float64(0), float64(0)
	for _, space := range buildingModel.Spaces {
		totalEnvelopeArea += space.ExteriorWallArea + space.ExteriorWindowArea + space.RoofArea + space.SkylightArea
		totalEnvelopeAreaTimesK += (space.ExteriorWallArea+space.RoofArea)*space.WallUValue + (space.ExteriorWindowArea+space.SkylightArea)*space.WindowUValue
	}
	if totalEnvelopeArea > 0 {
		buildingModel.AverageEnvelopeK = totalEnvelopeAreaTimesK / totalEnvelopeArea
	} else {
		buildingModel.AverageEnvelopeK = 0.35
	}
	buildingModel.WeekendLoadCorrection = 1 + (weekendCorrectionAlphaT*buildingModel.AverageEnvelopeK*buildingModel.ShapeCoefficient + weekendCorrectionAlphaS*buildingModel.ShapeCoefficient)

	// ── 分配计算缓存 ──────────────────────────────
	numSpaces := len(buildingModel.Spaces)

	dailyLoadCache := make([][][]float64, numSpaces)
	for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
		dailyLoadCache[spaceIdx] = make([][]float64, 365)
		for dayIdx := 0; dayIdx < 365; dayIdx++ {
			dailyLoadCache[spaceIdx][dayIdx] = make([]float64, 3)
		}
	}

	needHourlyCache := exportDaily == 1 || exportHourly == 1
	var hourlyLoadCache [][][][]float64
	if needHourlyCache {
		hourlyLoadCache = make([][][][]float64, numSpaces)
		for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
			hourlyLoadCache[spaceIdx] = make([][][]float64, 365)
			for dayIdx := 0; dayIdx < 365; dayIdx++ {
				hourlyLoadCache[spaceIdx][dayIdx] = make([][]float64, 24)
				for hourIdx := 0; hourIdx < 24; hourIdx++ {
					hourlyLoadCache[spaceIdx][dayIdx][hourIdx] = make([]float64, 3)
				}
			}
		}
	}

	// ── 迭代计算：逐空间 × 逐天 × 逐小时 ────────────
	solarCalc := MoosasSolar{}
	for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
		space := buildingModel.Spaces[spaceIdx]

		// Fixed-value solar input keeps the legacy semantics:
		// seasonal total (Wh) -> climate correction -> average daily gain.
		coolingSeasonDays := globalWeather.CoolingSeasonEnd - globalWeather.CoolingSeasonStart + 1
		heatingSeasonDays := 365 - globalWeather.HeatingSeasonStart + globalWeather.HeatingSeasonEnd + 1
		adjustedSummerSolarGain := adjustedSeasonalSolarGain(space.SeasonalSummerSolarGain, summerRadiationCorrection, coolingSeasonDays)
		adjustedWinterSolarGain := adjustedSeasonalSolarGain(space.SeasonalWinterSolarGain, winterRadiationCorrection, heatingSeasonDays)

		// 计算窗墙比
		glazingRatio := float64(0)
		totalOpaqueAndGlazingArea := space.ExteriorWallArea + space.ExteriorWindowArea + space.RoofArea + space.SkylightArea
		if totalOpaqueAndGlazingArea != 0 {
			glazingRatio = (space.ExteriorWindowArea + space.SkylightArea) / totalOpaqueAndGlazingArea
		}

		for dayIdx := 0; dayIdx < 365; dayIdx++ {
			nightAvgOutdoorTemp := calcNightAverageOutdoorTemp(dayIdx, space.OccupancyStartHour, space.OccupancyEndHour)

			for hourIdx := space.OccupancyStartHour - 1; hourIdx <= space.OccupancyEndHour-2; hourIdx++ {
				if hourIdx < 0 {
					hourIdx = 0
				}
				absHourIdx := dayIdx*24 + hourIdx

				// 获取该小时 8 个可作息化参数的实际数值
				currentCoolingSetpointTemp := space.CoolingSetpointTemp.getValueAtHour(absHourIdx)
				currentCoolingSetpointHumidity := space.CoolingSetpointHumidity.getValueAtHour(absHourIdx)
				currentHeatingSetpointTemp := space.HeatingSetpointTemp.getValueAtHour(absHourIdx)
				currentOccupantDensity := space.OccupantDensity.getValueAtHour(absHourIdx)
				currentFreshAirPerPerson := space.FreshAirPerPerson.getValueAtHour(absHourIdx)
				currentOccupantHeatGain := space.OccupantHeatGain.getValueAtHour(absHourIdx)
				currentEquipmentHeatGain := space.EquipmentHeatGain.getValueAtHour(absHourIdx)
				currentLightingHeatGain := space.LightingHeatGain.getValueAtHour(absHourIdx)

				// 计算该小时的照明能耗（太阳辐射采光模型）
				interiorZoneArea := space.FloorArea - space.PerimeterZoneArea
				hourlyLightingLoad := solarCalc.calcLightingEnergy(
					buildingModel.Latitude, buildingModel.Altitude,
					dayIdx+1, hourIdx+1,
					glazingRatio, interiorZoneArea, space.PerimeterZoneArea, currentLightingHeatGain,
				)

				dailyLoadCache[spaceIdx][dayIdx][2] += hourlyLightingLoad / 2
				if needHourlyCache {
					hourlyLoadCache[spaceIdx][dayIdx][hourIdx][2] += hourlyLightingLoad / 2
				}

				if dayIdx >= globalWeather.CoolingSeasonStart && dayIdx <= globalWeather.CoolingSeasonEnd {
					// ── 空调季：计算制冷负荷 ──────────────────
					tempDiffCooling := globalWeather.HourlyDryBulbTemp[absHourIdx] - currentCoolingSetpointTemp +
						calcNightThermalMassCorrection(buildingModel.AverageEnvelopeK, buildingModel.ShapeCoefficient, nightAvgOutdoorTemp, currentCoolingSetpointTemp, float64(space.OccupancyEndHour-space.OccupancyStartHour), space.NightVentilationACH)
					enthalpyDiff := calcOutdoorAirEnthalpy(globalWeather.HourlyDryBulbTemp[absHourIdx], globalWeather.HourlyDewPointTemp[absHourIdx]) -
						calcIndoorDesignEnthalpy(currentCoolingSetpointTemp, currentCoolingSetpointHumidity)
					groundTempDiffCooling := globalWeather.HourlyGroundTemp[absHourIdx] - currentCoolingSetpointTemp
					envelopeLoad := calcEnvelopeHeatTransferLoadPublic(space, tempDiffCooling, groundTempDiffCooling, buildingModel.WeekendLoadCorrection)

					freshAirLoad := currentOccupantDensity * currentFreshAirPerPerson * clampToPositive(enthalpyDiff) * space.FloorArea / 3.6
					heatDissipation := (currentOccupantDensity*currentOccupantHeatGain+currentEquipmentHeatGain)*space.FloorArea + hourlyLightingLoad/2
					coolingLoad := float64(0)
					if space.PerimeterZoneArea > 0 {
						infiltrationLoad := AirDensity * AirCapacity * clampToPositive(tempDiffCooling) * space.FloorArea * space.StoryHeight * space.InfiltrationACH / 3.6
						coolingLoad = clampToPositive(envelopeLoad + freshAirLoad + heatDissipation + infiltrationLoad)
					} else {
						coolingLoad = clampToPositive(envelopeLoad + freshAirLoad + heatDissipation)
					}

					dailyLoadCache[spaceIdx][dayIdx][0] += coolingLoad
					if needHourlyCache {
						hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0] += coolingLoad
					}

				} else if dayIdx >= globalWeather.HeatingSeasonStart || dayIdx <= globalWeather.HeatingSeasonEnd {
					// ── 采暖季：计算采暖负荷 ──────────────────
					tempDiffHeating := currentHeatingSetpointTemp - globalWeather.HourlyDryBulbTemp[absHourIdx] -
						calcNightThermalMassCorrection(buildingModel.AverageEnvelopeK, buildingModel.ShapeCoefficient, nightAvgOutdoorTemp, currentHeatingSetpointTemp, float64(space.OccupancyEndHour-space.OccupancyStartHour), space.NightVentilationACH)
					groundTempDiffHeating := currentHeatingSetpointTemp - globalWeather.HourlyGroundTemp[absHourIdx]
					envelopeLoad := calcEnvelopeHeatTransferLoadPublic(space, tempDiffHeating, groundTempDiffHeating, buildingModel.WeekendLoadCorrection)

					freshAirLoad := currentOccupantDensity * currentFreshAirPerPerson * AirDensity * AirCapacity * clampToPositive(tempDiffHeating) / 3.6 * space.FloorArea
					heatDissipation := (currentOccupantDensity*currentOccupantHeatGain+currentEquipmentHeatGain)*space.FloorArea + hourlyLightingLoad/2
					heatingLoad := float64(0)
					if space.PerimeterZoneArea > 0 {
						infiltrationLoad := AirDensity * AirCapacity * clampToPositive(tempDiffHeating) * space.FloorArea * space.StoryHeight * space.InfiltrationACH / 3.6
						heatingLoad = clampToPositive(envelopeLoad + freshAirLoad - heatDissipation + infiltrationLoad)
					} else {
						heatingLoad = clampToPositive(envelopeLoad + freshAirLoad - heatDissipation)
					}

					dailyLoadCache[spaceIdx][dayIdx][1] += heatingLoad
					if needHourlyCache {
						hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1] += heatingLoad
					}
				}
			}

			// 日结束后：叠加辐射得热修正并除以能效比
			if dayIdx >= globalWeather.CoolingSeasonStart && dayIdx <= globalWeather.CoolingSeasonEnd {
				summerDailySolarGain := adjustedSummerSolarGain
				if space.SeasonalSummerSolarGain.IsSchedule {
					summerDailySolarGain = seasonAwareDailySolarGain(space.SeasonalSummerSolarGain, dayIdx, true)
				}
				dailyLoadCache[spaceIdx][dayIdx][0] = clampToPositive(dailyLoadCache[spaceIdx][dayIdx][0]+summerDailySolarGain*space.WindowSHGC) / space.CoolingEER
				if needHourlyCache {
					if space.SeasonalSummerSolarGain.IsSchedule {
						for hourIdx := space.OccupancyStartHour - 1; hourIdx <= space.OccupancyEndHour-2; hourIdx++ {
							if hourIdx < 0 {
								hourIdx = 0
							}
							absHourIdx := dayIdx*24 + hourIdx
							hourlySolarGain := seasonAwareHourlySolarGain(space.SeasonalSummerSolarGain, absHourIdx, true) * space.WindowSHGC
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]+hourlySolarGain) / space.CoolingEER
						}
					} else {
						numWorkHours := space.OccupancyEndHour - space.OccupancyStartHour
						if numWorkHours <= 0 {
							numWorkHours = 1
						}
						solarGainPerWorkHour := summerDailySolarGain * space.WindowSHGC / float64(numWorkHours)
						for hourIdx := space.OccupancyStartHour - 1; hourIdx <= space.OccupancyEndHour-2; hourIdx++ {
							if hourIdx < 0 {
								hourIdx = 0
							}
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]+solarGainPerWorkHour) / space.CoolingEER
						}
					}
				}
			} else if dayIdx >= globalWeather.HeatingSeasonStart || dayIdx <= globalWeather.HeatingSeasonEnd {
				winterDailySolarGain := adjustedWinterSolarGain
				if space.SeasonalWinterSolarGain.IsSchedule {
					winterDailySolarGain = seasonAwareDailySolarGain(space.SeasonalWinterSolarGain, dayIdx, true)
				}
				dailyLoadCache[spaceIdx][dayIdx][1] = clampToPositive(dailyLoadCache[spaceIdx][dayIdx][1]-winterDailySolarGain*space.WindowSHGC) / space.HeatingEER
				if needHourlyCache {
					if space.SeasonalWinterSolarGain.IsSchedule {
						for hourIdx := space.OccupancyStartHour - 1; hourIdx <= space.OccupancyEndHour-2; hourIdx++ {
							if hourIdx < 0 {
								hourIdx = 0
							}
							absHourIdx := dayIdx*24 + hourIdx
							hourlySolarGain := seasonAwareHourlySolarGain(space.SeasonalWinterSolarGain, absHourIdx, true) * space.WindowSHGC
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]-hourlySolarGain) / space.HeatingEER
						}
					} else {
						numWorkHours := space.OccupancyEndHour - space.OccupancyStartHour
						if numWorkHours <= 0 {
							numWorkHours = 1
						}
						solarGainPerWorkHour := winterDailySolarGain * space.WindowSHGC / float64(numWorkHours)
						for hourIdx := space.OccupancyStartHour - 1; hourIdx <= space.OccupancyEndHour-2; hourIdx++ {
							if hourIdx < 0 {
								hourIdx = 0
							}
							hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1] = clampToPositive(hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]-solarGainPerWorkHour) / space.HeatingEER
						}
					}
				}
			}
		} // 天循环结束
	} // 空间循环结束

	// ── 后处理：汇总能耗结果（与居住建筑共享逻辑） ──
	aggregateResults(numSpaces, dailyLoadCache, hourlyLoadCache, needHourlyCache, exportDaily, exportHourly, exportByZone)
}

// ═════════════════════════════════════════════════════════════
// 共享后处理：汇总能耗结果
// ═════════════════════════════════════════════════════════════

// aggregateResults 将 dailyLoadCache / hourlyLoadCache 汇总到 globalEnergyResult。
// 两种建筑类型的后处理逻辑完全相同。
func aggregateResults(numSpaces int, dailyLoadCache [][][]float64, hourlyLoadCache [][][][]float64, needHourlyCache bool, exportDaily, exportHourly, exportByZone int) {
	globalEnergyResult = EnergyData{} // 重置
	globalEnergyResult.ByMonth = make([]EnergyItem, 12)
	globalEnergyResult.BySpace = make([]EnergyItem, numSpaces)

	if exportDaily == 1 {
		globalEnergyResult.ByDay = make([]EnergyItem, 365)
	}
	if exportHourly == 1 {
		globalEnergyResult.ByHour = make([]EnergyItem, 8760)
	}

	if exportByZone == 1 {
		globalEnergyResult.BySpaceMonth = make([][]EnergyItem, numSpaces)
		for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
			globalEnergyResult.BySpaceMonth[spaceIdx] = make([]EnergyItem, 12)
		}
		if exportDaily == 1 {
			globalEnergyResult.BySpaceDay = make([][]EnergyItem, numSpaces)
			for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
				globalEnergyResult.BySpaceDay[spaceIdx] = make([]EnergyItem, 365)
			}
		}
		if exportHourly == 1 {
			globalEnergyResult.BySpaceHour = make([][]EnergyItem, numSpaces)
			for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
				globalEnergyResult.BySpaceHour[spaceIdx] = make([]EnergyItem, 8760)
			}
		}
	}

	for spaceIdx := 0; spaceIdx < numSpaces; spaceIdx++ {
		// 全年总量和分空间总量
		for dayIdx := 0; dayIdx < 365; dayIdx++ {
			globalEnergyResult.TotalAnnual.CoolingEnergy += dailyLoadCache[spaceIdx][dayIdx][0]
			globalEnergyResult.TotalAnnual.HeatingEnergy += dailyLoadCache[spaceIdx][dayIdx][1]
			globalEnergyResult.TotalAnnual.LightingEnergy += dailyLoadCache[spaceIdx][dayIdx][2]
			globalEnergyResult.BySpace[spaceIdx].CoolingEnergy += dailyLoadCache[spaceIdx][dayIdx][0]
			globalEnergyResult.BySpace[spaceIdx].HeatingEnergy += dailyLoadCache[spaceIdx][dayIdx][1]
			globalEnergyResult.BySpace[spaceIdx].LightingEnergy += dailyLoadCache[spaceIdx][dayIdx][2]
		}

		// 逐月
		for monthIdx := 0; monthIdx < 12; monthIdx++ {
			for _, dayLoad := range dailyLoadCache[spaceIdx][monthStartDayIndex[monthIdx]:monthStartDayIndex[monthIdx+1]] {
				globalEnergyResult.ByMonth[monthIdx].CoolingEnergy += dayLoad[0]
				globalEnergyResult.ByMonth[monthIdx].HeatingEnergy += dayLoad[1]
				globalEnergyResult.ByMonth[monthIdx].LightingEnergy += dayLoad[2]
			}
		}

		// 逐日
		if exportDaily == 1 && needHourlyCache {
			for dayIdx := 0; dayIdx < 365; dayIdx++ {
				for hourIdx := 0; hourIdx < 24; hourIdx++ {
					globalEnergyResult.ByDay[dayIdx].CoolingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]
					globalEnergyResult.ByDay[dayIdx].HeatingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]
					globalEnergyResult.ByDay[dayIdx].LightingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][2]
				}
			}
		}

		// 逐时
		if exportHourly == 1 && needHourlyCache {
			for dayIdx := 0; dayIdx < 365; dayIdx++ {
				for hourIdx := 0; hourIdx < 24; hourIdx++ {
					absHourIdx := dayIdx*24 + hourIdx
					globalEnergyResult.ByHour[absHourIdx].CoolingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]
					globalEnergyResult.ByHour[absHourIdx].HeatingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]
					globalEnergyResult.ByHour[absHourIdx].LightingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][2]
				}
			}
		}

		// 分空间
		if exportByZone == 1 {
			for monthIdx := 0; monthIdx < 12; monthIdx++ {
				for _, dayLoad := range dailyLoadCache[spaceIdx][monthStartDayIndex[monthIdx]:monthStartDayIndex[monthIdx+1]] {
					globalEnergyResult.BySpaceMonth[spaceIdx][monthIdx].CoolingEnergy += dayLoad[0]
					globalEnergyResult.BySpaceMonth[spaceIdx][monthIdx].HeatingEnergy += dayLoad[1]
					globalEnergyResult.BySpaceMonth[spaceIdx][monthIdx].LightingEnergy += dayLoad[2]
				}
			}

			if exportDaily == 1 && needHourlyCache {
				for dayIdx := 0; dayIdx < 365; dayIdx++ {
					for hourIdx := 0; hourIdx < 24; hourIdx++ {
						globalEnergyResult.BySpaceDay[spaceIdx][dayIdx].CoolingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]
						globalEnergyResult.BySpaceDay[spaceIdx][dayIdx].HeatingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]
						globalEnergyResult.BySpaceDay[spaceIdx][dayIdx].LightingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][2]
					}
				}
			}

			if exportHourly == 1 && needHourlyCache {
				for dayIdx := 0; dayIdx < 365; dayIdx++ {
					for hourIdx := 0; hourIdx < 24; hourIdx++ {
						absHourIdx := dayIdx*24 + hourIdx
						globalEnergyResult.BySpaceHour[spaceIdx][absHourIdx].CoolingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][0]
						globalEnergyResult.BySpaceHour[spaceIdx][absHourIdx].HeatingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][1]
						globalEnergyResult.BySpaceHour[spaceIdx][absHourIdx].LightingEnergy += hourlyLoadCache[spaceIdx][dayIdx][hourIdx][2]
					}
				}
			}
		}
	}
}

// ═════════════════════════════════════════════════════════════
// 气候区判断
// ═════════════════════════════════════════════════════════════

// determineClimateZoneResidential 根据纬度确定居住建筑的气候分区。
// 设置全局变量 summerTemperatureCorrection 和 winterTemperatureCorrection。
func determineClimateZoneResidential(latitude float64) MoosasWeather {
	climateWeather := MoosasWeather{}
	if latitude > 0.74 {
		summerTemperatureCorrection, winterTemperatureCorrection = 3.0, 3.0
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 151, 242
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 293, 99
	} else if latitude > 0.62 {
		summerTemperatureCorrection, winterTemperatureCorrection = 3.0, 3.0
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 140, 262
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 319, 73
	} else if latitude > 0.47 {
		summerTemperatureCorrection, winterTemperatureCorrection = 3.0, 3.0
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 135, 272
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 334, 58
	} else {
		summerTemperatureCorrection, winterTemperatureCorrection = 3.0, 3.0
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 90, 303
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 334, 58
	}
	return climateWeather
}

// determineClimateZonePublic 根据纬度确定公共建筑的气候分区。
// 设置全局变量 weekendCorrectionAlphaT 和 weekendCorrectionAlphaS。
func determineClimateZonePublic(latitude float64) MoosasWeather {
	climateWeather := MoosasWeather{}
	if latitude > 0.74 {
		weekendCorrectionAlphaT, weekendCorrectionAlphaS = -2.34, 1.96
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 151, 242
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 293, 99
	} else if latitude > 0.62 {
		weekendCorrectionAlphaT, weekendCorrectionAlphaS = -1.83, 2.16
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 140, 262
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 319, 73
	} else if latitude > 0.47 {
		weekendCorrectionAlphaT, weekendCorrectionAlphaS = -2.39, 2.39
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 135, 272
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 334, 58
	} else {
		weekendCorrectionAlphaT, weekendCorrectionAlphaS = -2.06, 2.57
		climateWeather.CoolingSeasonStart, climateWeather.CoolingSeasonEnd = 90, 303
		climateWeather.HeatingSeasonStart, climateWeather.HeatingSeasonEnd = 334, 58
	}
	return climateWeather
}

// ═════════════════════════════════════════════════════════════
// 照明能耗计算（仅公共建筑使用）
// ═════════════════════════════════════════════════════════════

func (solarCalc MoosasSolar) calcLightingEnergy(latitude, altitude float64, dayOfYear, hourOfDay int, glazingRatio, interiorZoneArea, perimeterZoneArea, lightingHeatGain float64) float64 {
	if glazingRatio == 0 {
		return lightingHeatGain * (interiorZoneArea + perimeterZoneArea)
	}

	solarCalc.solarDeclination = 23.45 * math.Sin(2*math.Pi*float64(284+dayOfYear)/365)
	solarCalc.daylightHours = 2.0 / 15 * math.Acos(0-math.Tan(latitude)*math.Tan(solarCalc.solarDeclination*math.Pi/180)) * 180 / math.Pi
	solarCalc.sunriseHour = int(12-solarCalc.daylightHours/2) + 1
	solarCalc.sunsetHour = int(12 + solarCalc.daylightHours/2)
	if hourOfDay < solarCalc.sunriseHour || hourOfDay > solarCalc.sunsetHour {
		return lightingHeatGain * (interiorZoneArea + perimeterZoneArea)
	}

	altitudeKm := altitude / 1000
	if altitudeKm >= 2.5 {
		altitudeKm = 2.49
	}
	dayAngle := 2 * math.Pi * float64(dayOfYear) / 365
	solarCalc.extraterrestrialIrrad = SolarConstant * (1.00011 + 0.034221*math.Cos(dayAngle) + 0.00128*math.Sin(dayAngle) + 0.000719*math.Cos(2*dayAngle) + 0.000077*math.Sin(2*dayAngle))
	solarCalc.hottelCoeffA1 = 0.97 * (0.4237 - 0.00821*math.Sqrt(6-altitudeKm))
	solarCalc.hottelCoeffA2 = 0.99 * (0.5055 + 0.00595*math.Sqrt(6.5-altitudeKm))
	solarCalc.hottelCoeffA3 = 1.02 * (0.2711 + 0.01858*math.Sqrt(2.5-altitudeKm))

	solarHourAngleDeg := 15 * (12 - hourOfDay)
	solarAltitudeRad := math.Asin(
		math.Cos(latitude)*math.Cos(solarCalc.solarDeclination*math.Pi/180)*math.Cos(float64(solarHourAngleDeg)*math.Pi/180) +
			math.Sin(latitude)*math.Sin(solarCalc.solarDeclination*math.Pi/180),
	)
	solarZenithAngleDeg := 90 - solarAltitudeRad
	directBeamTransmittance := solarCalc.hottelCoeffA1 + solarCalc.hottelCoeffA2*math.Exp(0-solarCalc.hottelCoeffA3/math.Cos(solarZenithAngleDeg*math.Pi/180))
	diffuseTransmittance := 0.271 - 0.294*directBeamTransmittance
	totalHorizontalIrradiance := solarCalc.extraterrestrialIrrad * (directBeamTransmittance + diffuseTransmittance) / 2.0

	daylightIlluminance := glazingRatio * totalHorizontalIrradiance * 0.5
	if daylightIlluminance < lightingHeatGain {
		return lightingHeatGain*interiorZoneArea*(1.6-glazingRatio) + (lightingHeatGain-daylightIlluminance)*perimeterZoneArea*(1.2-glazingRatio)
	}
	return lightingHeatGain * interiorZoneArea * (1.6 - glazingRatio)
}

// ═════════════════════════════════════════════════════════════
// 辅助计算函数
// ═════════════════════════════════════════════════════════════

// calcNightAverageOutdoorTemp 计算夜间（非运行时段）平均室外温度（仅公共建筑使用）。
func calcNightAverageOutdoorTemp(dayIdx, occupancyStart, occupancyEnd int) float64 {
	tempSum := float64(0)
	for hourIdx := 0; hourIdx < 24; hourIdx++ {
		if hourIdx <= occupancyStart-2 || hourIdx >= occupancyEnd-1 {
			tempSum += globalWeather.HourlyDryBulbTemp[dayIdx*24+hourIdx]
		}
	}
	return tempSum / float64(24-(occupancyEnd-occupancyStart))
}

// calcNightThermalMassCorrection 计算夜间蓄热温差修正（仅公共建筑使用）。
func calcNightThermalMassCorrection(avgEnvelopeK, shapeCoeff, nightAvgTemp, indoorSetpointTemp, occupancyHours, nightVentACH float64) float64 {
	nonOccupancyHours := 24 - occupancyHours
	logArg := absoluteValue(indoorSetpointTemp - nightAvgTemp)
	decayExponent := math.Log(logArg) - (2.985*avgEnvelopeK*shapeCoeff+nightVentACH)*nonOccupancyHours
	tempAtOccupancyStart := signOf(indoorSetpointTemp-nightAvgTemp)*math.Exp(decayExponent) + nightAvgTemp
	tempDriftRate := 0.335 * (indoorSetpointTemp - tempAtOccupancyStart) / ((avgEnvelopeK*shapeCoeff + 0.335*nightVentACH) * nonOccupancyHours)
	return (1 + 0.335*nightVentACH/avgEnvelopeK*shapeCoeff) * nonOccupancyHours / occupancyHours * tempDriftRate
}

// calcOutdoorAirEnthalpy 计算室外空气焓值（仅公共建筑使用）。
func calcOutdoorAirEnthalpy(dryBulbTemp, dewPointTemp float64) float64 {
	return 1.01*dryBulbTemp + (1.84*dryBulbTemp+2500)*dewPointTemp/1000
}

// calcIndoorDesignEnthalpy 计算室内设计工况焓值（仅公共建筑使用）。
func calcIndoorDesignEnthalpy(dryBulbTemp, relativeHumidity float64) float64 {
	saturationPressure := 0.07394*dryBulbTemp*dryBulbTemp*dryBulbTemp - 0.02*dryBulbTemp*dryBulbTemp + 62.49*dryBulbTemp + 581.9
	return 1.01*dryBulbTemp + (2500+1.84*dryBulbTemp)*622*(relativeHumidity*saturationPressure/(101325-relativeHumidity*saturationPressure))/1000
}

// calcEnvelopeHeatTransferLoadPublic 计算公共建筑围护结构传热负荷（含周末修正）。
func calcEnvelopeHeatTransferLoadPublic(space MoosasSpace, tempDiff, groundTempDiff, weekendCorrection float64) float64 {
	envelopeLoad := (space.ExteriorWallArea + space.RoofArea) * space.WallUValue * tempDiff
	envelopeLoad += (space.ExteriorWindowArea + space.SkylightArea) * space.WindowUValue * tempDiff
	envelopeLoad += space.GroundFloorArea * space.WallUValue * groundTempDiff
	return envelopeLoad * weekendCorrection
}

// calcEnvelopeHeatTransferLoadResidential 计算居住建筑围护结构传热负荷（无周末修正）。
func calcEnvelopeHeatTransferLoadResidential(space MoosasSpace, tempDiff, groundTempDiff float64) float64 {
	envelopeLoad := (space.ExteriorWallArea + space.RoofArea) * space.WallUValue * tempDiff
	envelopeLoad += (space.ExteriorWindowArea + space.SkylightArea) * space.WindowUValue * tempDiff
	envelopeLoad += space.GroundFloorArea * space.WallUValue * groundTempDiff
	return envelopeLoad
}

// ═════════════════════════════════════════════════════════════
// 数学工具函数
// ═════════════════════════════════════════════════════════════

func absoluteValue(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

func clampToPositive(x float64) float64 {
	if x < 0 {
		return 0
	}
	return x
}

func signOf(x float64) float64 {
	if x < 0 {
		return -1.0
	} else if x == 0 {
		return 0.0
	}
	return 1.0
}

// ═════════════════════════════════════════════════════════════
// 输出格式化
// ═════════════════════════════════════════════════════════════

func formatEnergyItem(item EnergyItem, buildingArea float64) string {
	return formatEnergyItemWithPrecision(item, buildingArea, 2)
}

func formatEnergyItemWithZone(spaceIdx int, item EnergyItem, buildingArea float64) string {
	return formatEnergyItemWithZonePrecision(spaceIdx, item, buildingArea, 2)
}

func formatEnergyItemWithPrecision(item EnergyItem, buildingArea float64, precision int) string {
	coolingEnergyPerArea := strconv.FormatFloat(item.CoolingEnergy/buildingArea/1000, 'f', precision, 64)
	heatingEnergyPerArea := strconv.FormatFloat(item.HeatingEnergy/buildingArea/1000, 'f', precision, 64)
	lightingEnergyPerArea := strconv.FormatFloat(item.LightingEnergy/buildingArea/1000, 'f', precision, 64)
	return coolingEnergyPerArea + "," + heatingEnergyPerArea + "," + lightingEnergyPerArea + "\n"
}

func formatEnergyItemWithZonePrecision(spaceIdx int, item EnergyItem, buildingArea float64, precision int) string {
	coolingEnergyPerArea := strconv.FormatFloat(item.CoolingEnergy/buildingArea/1000, 'f', precision, 64)
	heatingEnergyPerArea := strconv.FormatFloat(item.HeatingEnergy/buildingArea/1000, 'f', precision, 64)
	lightingEnergyPerArea := strconv.FormatFloat(item.LightingEnergy/buildingArea/1000, 'f', precision, 64)
	return strconv.Itoa(spaceIdx) + "," + coolingEnergyPerArea + "," + heatingEnergyPerArea + "," + lightingEnergyPerArea + "\n"
}
