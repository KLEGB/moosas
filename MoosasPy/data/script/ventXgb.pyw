import traceback
try:
	from MoosasPy.vent import callXgb
	callXgb("C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/data/vent/xgb.input","C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/data/vent/xgb.output")
	with open('status.log','w+') as f:
		f.write('1')
except Exception as e:
	print(traceback.format_exc())
	with open('error.log','w+') as f:
		f.write(traceback.format_exc())
	with open('status.log','w+') as f:
		f.write('0')
