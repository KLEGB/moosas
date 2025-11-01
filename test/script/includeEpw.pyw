import traceback
try:
	from MoosasPy.weather import includeEpw
	from MoosasPy.utils import path
	import time
	sid=includeEpw(r"C:\EnergyPlusV22-2-0\WeatherData\SGP_Singapore.486980_IWEC.epw","sg")
	with open(path.tempDir+'\sid.txt','w+') as f:
	    f.write(str(sid))
	time.sleep(0.1)
	with open('status.log','w+') as f:
		f.write('1')
except Exception as e:
	print(traceback.format_exc())
	with open('error.log','w+') as f:
		f.write(traceback.format_exc())
	with open('status.log','w+') as f:
		f.write('0')
