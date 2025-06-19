package main

import (
	"os"
)

func main() {
	input,_:=os.ReadFile("mkdir.input")
	path:=string(input)
	os.RemoveAll(path)
	os.Mkdir(path,os.ModePerm)
	os.Mkdir(path+"0",os.ModePerm)
	os.Mkdir(path+"constant",os.ModePerm)
	os.Mkdir(path+"constant/triSurface",os.ModePerm)
	os.Mkdir(path+"log",os.ModePerm)
	os.Mkdir(path+"system",os.ModePerm)
	os.Create(path+"vent.foam")
}
