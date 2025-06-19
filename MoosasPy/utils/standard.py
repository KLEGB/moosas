from .support import os, re
from .tools import path

template = dict({})
'''
    "zone_wallU"=>            #外墙U值
    "zone_winU"=>             #外窗U值
    "zone_win_SHGC"=>         #外窗SHGC值
    "zone_c_temp"=>           #空调控制温度
    "zone_h_temp"=>           #采暖控制温度
    "zone_collingEER"=>       #空调能效比
    "zone_HeatingEER"=>       #空调能效比
    "zone_work_start"=>       #系统开启时间
    "zone_work_end"=>         #系统关闭时间
    "zone_ppsm"=>             #每平米人数
    "zone_pfav"=>             #人均新风量
    "zone_popheat"=>          #人员散热
    "zone_equipment"=>        #设备散热
    "zone_lighting"=>         #灯光散热
    "zone_inflitration"=>     #渗风换气次数
    "zone_nightACH"=>         #夜间换气次数
'''


def loadBuildingTemplate(templateFile)->dict:
    try:
        with open(templateFile, 'r') as f:
            title = f.readline().strip('\n').split(',')
            _key_tab, _value_tab = [], []
            for i in range(len(title)):
                if title[i][:5] != 'zone_':
                    _key_tab.append(i)
                else:
                    _value_tab.append(i)
            _name = [title[i] for i in _value_tab]
            for line in f.readlines():
                arr = line.strip('\n').split(',')
                _key = '_'.join([arr[i] for i in _key_tab])
                _value = [arr[i] for i in _value_tab]
                _template = {_name[i]: _value[i] for i in range(len(_value))}
                template[_key] = _template

    except:
        raise FileNotFoundError('Load Error: building template')

    return template


def searchTemplate(str_list, templatelist=template):
    result = []
    for tag in str_list:
        result += [templatelist[_name] for _name in templatelist.keys() if re.search(tag, _name) is not None]
    return result
