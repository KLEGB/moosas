import traceback
try:
	from MoosasPy import transform,saveModel
	model = transform('C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.geo','C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.xml',geo_path='C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0_out.geo',solve_duplicated=True,solve_redundant=True,solve_contains=True,break_wall_vertical=True,break_wall_horizontal=True,attach_shading=False)
	saveModel(model,'C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0..owl')
	with open('status.log','w+') as f:
		f.write('1')
except Exception as e:
	print(traceback.format_exc())
	with open('error.log','w+') as f:
		f.write(traceback.format_exc())
	with open('status.log','w+') as f:
		f.write('0')
