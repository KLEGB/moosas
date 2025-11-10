import traceback
try:
	from MoosasPy.IO import _idf
	_idf.IDF('C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/moosas/data/energy/selection0.idf',epw='C:\EnergyPlusV22-2-0\WeatherData\AUS_NSW.Sydney.947670_IWEC.epw').run()
	with open('status.log','w+') as f:
		f.write('1')
except Exception as e:
	print(traceback.format_exc())
	with open('error.log','w+') as f:
		f.write(traceback.format_exc())
	with open('status.log','w+') as f:
		f.write('0')
	input('******Severe Error******')
