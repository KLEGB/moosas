package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const (
	hoursPerYear = 8760
)

var monthDays = [12]int{31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}

func main() {
	inputPath, outputPath, err := parseArgs(os.Args[1:])
	if err != nil {
		if err.Error() == "help requested" {
			printUsage()
			os.Exit(0)
		}
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
		}
		printUsage()
		os.Exit(2)
	}

	if outputPath == "" {
		ext := filepath.Ext(inputPath)
		outputPath = strings.TrimSuffix(inputPath, ext) + ".csv"
	}

	if err := convertEPWToCSV(inputPath, outputPath); err != nil {
		log.Fatalf("epw2csv failed: %v", err)
	}
}

func parseArgs(args []string) (string, string, error) {
	var inputPath string
	var outputPath string

	for i := 0; i < len(args); i++ {
		arg := args[i]
		switch arg {
		case "-h", "-help", "--help":
			return "", "", fmt.Errorf("help requested")
		case "-o", "-output", "--output":
			if i+1 >= len(args) {
				return "", "", fmt.Errorf("missing value for %s", arg)
			}
			outputPath = args[i+1]
			i++
		default:
			if strings.HasPrefix(arg, "-") {
				return "", "", fmt.Errorf("unknown option: %s", arg)
			}
			if inputPath != "" {
				return "", "", fmt.Errorf("multiple input files provided: %s and %s", inputPath, arg)
			}
			inputPath = arg
		}
	}

	if inputPath == "" {
		return "", "", fmt.Errorf("missing input EPW file")
	}
	return inputPath, outputPath, nil
}

func printUsage() {
	fmt.Fprintf(os.Stderr, "Usage: %s [options] input.epw\n", filepath.Base(os.Args[0]))
	fmt.Fprintln(os.Stderr, "Options:")
	fmt.Fprintln(os.Stderr, "  -o, -output <path>   output csv path")
	fmt.Fprintln(os.Stderr, "  -h, -help            print help")
}

func convertEPWToCSV(inputPath, outputPath string) error {
	inFile, err := os.Open(inputPath)
	if err != nil {
		return fmt.Errorf("open input file: %w", err)
	}
	defer inFile.Close()

	reader := csv.NewReader(inFile)
	reader.FieldsPerRecord = -1
	reader.ReuseRecord = true

	locationRow, err := reader.Read()
	if err != nil {
		return fmt.Errorf("read EPW location header: %w", err)
	}
	if len(locationRow) < 10 {
		return fmt.Errorf("invalid EPW location header: expected at least 10 fields, got %d", len(locationRow))
	}
	locationRow[0] = strings.TrimPrefix(locationRow[0], "\ufeff")
	stationID := trimLastChar(strings.TrimSpace(locationRow[5]))

	if _, err := reader.Read(); err != nil {
		return fmt.Errorf("skip EPW header line 2: %w", err)
	}
	if _, err := reader.Read(); err != nil {
		return fmt.Errorf("skip EPW header line 3: %w", err)
	}

	groundRow, err := reader.Read()
	if err != nil {
		return fmt.Errorf("read EPW ground temperature header: %w", err)
	}
	if len(groundRow) < 18 {
		return fmt.Errorf("invalid EPW ground temperature header: expected at least 18 fields, got %d", len(groundRow))
	}
	groundTempsMonthly, err := parseMonthlyValues(groundRow[6:18])
	if err != nil {
		return fmt.Errorf("parse monthly ground temperatures: %w", err)
	}
	groundTemps := expandMonthlyGroundTemps(groundTempsMonthly)

	for i := 0; i < 4; i++ {
		if _, err := reader.Read(); err != nil {
			return fmt.Errorf("skip EPW header line %d: %w", 5+i, err)
		}
	}

	outFile, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("create output file: %w", err)
	}
	defer outFile.Close()

	writer := csv.NewWriter(outFile)
	defer writer.Flush()

	for hourIdx := 0; hourIdx < hoursPerYear; hourIdx++ {
		row, readErr := reader.Read()
		if readErr != nil {
			if readErr == io.EOF {
				return fmt.Errorf("EPW file ended early: expected %d hourly records, got %d", hoursPerYear, hourIdx)
			}
			return fmt.Errorf("read EPW hourly record %d: %w", hourIdx, readErr)
		}
		if len(row) < 22 {
			return fmt.Errorf("invalid EPW hourly record %d: expected at least 22 fields, got %d", hourIdx, len(row))
		}

		dryBulb, err := parseFloatField(row, 6, hourIdx, "dry bulb temperature")
		if err != nil {
			return err
		}
		dewPoint, err := parseFloatField(row, 7, hourIdx, "dew point temperature")
		if err != nil {
			return err
		}
		globalRad, err := parseFloatField(row, 13, hourIdx, "global horizontal radiation")
		if err != nil {
			return err
		}
		diffuseRad, err := parseFloatField(row, 15, hourIdx, "diffuse horizontal radiation")
		if err != nil {
			return err
		}
		hir, err := parseFloatField(row, 12, hourIdx, "horizontal infrared radiation")
		if err != nil {
			return err
		}
		windDir, err := parseFloatField(row, 20, hourIdx, "wind direction")
		if err != nil {
			return err
		}
		windSpeed, err := parseFloatField(row, 21, hourIdx, "wind speed")
		if err != nil {
			return err
		}
		pressure, err := parseFloatField(row, 9, hourIdx, "station pressure")
		if err != nil {
			return err
		}

		humidityRatio := calcHumidityRatio(dewPoint)
		skyTemp := calcSkyTemperature(hir)
		windCode := calcWindDirectionCode(windDir, windSpeed)
		groundTemp := groundTemps[hourIdx]

		record := []string{
			stationID,
			"0",
			strconv.Itoa(hourIdx),
			formatFloat(dryBulb),
			formatFloat(humidityRatio),
			formatFloat(globalRad),
			formatFloat(diffuseRad),
			formatFloat(groundTemp),
			formatFloat(skyTemp),
			formatFloat(windSpeed),
			strconv.Itoa(windCode),
			formatFloat(pressure),
			"9999999",
		}
		if err := writer.Write(record); err != nil {
			return fmt.Errorf("write CSV record %d: %w", hourIdx, err)
		}
	}

	writer.Flush()
	if err := writer.Error(); err != nil {
		return fmt.Errorf("flush CSV writer: %w", err)
	}
	return nil
}

func parseMonthlyValues(values []string) ([12]float64, error) {
	var out [12]float64
	for i, raw := range values {
		v, err := strconv.ParseFloat(strings.TrimSpace(raw), 64)
		if err != nil {
			return out, fmt.Errorf("month %d: %w", i+1, err)
		}
		out[i] = v
	}
	return out, nil
}

func expandMonthlyGroundTemps(monthly [12]float64) [hoursPerYear]float64 {
	var hourly [hoursPerYear]float64
	hourIdx := 0
	for monthIdx, days := range monthDays {
		monthValue := monthly[monthIdx]
		for i := 0; i < days*24; i++ {
			hourly[hourIdx] = monthValue
			hourIdx++
		}
	}
	return hourly
}

func parseFloatField(row []string, idx, hourIdx int, name string) (float64, error) {
	if idx >= len(row) {
		return 0, fmt.Errorf("hour %d: missing %s field at column %d", hourIdx, name, idx)
	}
	v, err := strconv.ParseFloat(strings.TrimSpace(row[idx]), 64)
	if err != nil {
		return 0, fmt.Errorf("hour %d: parse %s at column %d: %w", hourIdx, name, idx, err)
	}
	return v, nil
}

func trimLastChar(s string) string {
	if len(s) == 0 {
		return s
	}
	return s[:len(s)-1]
}

func calcHumidityRatio(dewPoint float64) float64 {
	d := 3.703 + 0.286*dewPoint + 9.164*math.Pow(10, -3)*math.Pow(dewPoint, 2) + 1.446*math.Pow(10, -4)*math.Pow(dewPoint, 3) + 1.741*math.Pow(10, -6)*math.Pow(dewPoint, 4) + 5.195*math.Pow(10, -8)*math.Pow(dewPoint, 5)
	return d
}

func calcSkyTemperature(horizontalInfrared float64) float64 {
	const stefanBoltzmann = 5.67e-8
	return math.Pow(horizontalInfrared/stefanBoltzmann, 0.25)
}

func calcWindDirectionCode(windDir, windSpeed float64) int {
	if windDir == 999 {
		return 0
	}
	code := int(math.Round(windDir / 360.0 * 16.0))
	if windSpeed != 0 && code == 0 {
		code = 16
	}
	return code
}

func formatFloat(v float64) string {
	return strconv.FormatFloat(math.Round(v*100)/100, 'f', 2, 64)
}
