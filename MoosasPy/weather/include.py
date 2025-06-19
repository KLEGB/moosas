import os

import numpy as np
import re
from ..utils.tools import path, callCmd
from .dest import Location, temp_dic, weather_dic, stationInfo

epw2wea_exe = os.path.join(path.libDir, 'weather/epw2wea.exe')
gendaymtx_exe = os.path.join(path.libDir, 'weather/gendaymtx.exe')
sun_position = os.path.join(path.libDir, r'weather\sun_position.csv')

TREGENZA_COEFFICIENTS = \
    [0.0435449227, 0.0416418006, 0.0473984151, 0.0406730411, 0.0428934136,
     0.0445221864, 0.0455168385, 0.0344199465]
TREGENZA_PATCHES_PER_ROW = [30, 30, 24, 24, 18, 12, 6, 1]


def epw2location(epw_file):
    '''
    epw文件格式:
    https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html
    :param epw_file: epw文件
    :return: loc: dest_station.csv存储词条
    '''
    with open(epw_file) as f:
        LOCATION = str(f.readline()).strip('\n').split(',')
        for i in range(7): f.readline()
        climate_data = np.array([f.readline().strip('\n').split(',') for i in range(8760)])
        loc = Location(
            LOCATION[5],  # 气象站编号
            LOCATION[1],  # 城市
            LOCATION[2],  # 省份
            LOCATION[6],  # 纬度
            LOCATION[7],  # 经度
            LOCATION[9],  # 海拔
            str(np.mean(climate_data[:, 9].astype(float)))  # 平均大气压
        )  # dest_station.csv存储气象文件
        return loc


def epw2csv(epw_file):
    '''
    epw与DeST气象数据转换
    epw文件格式:
    https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html
    DeST文件格式:
    http://166.111.120.118/cxdrmp/format/release/AlmaMmisdTest?mmsid=991012332769703966&&srchType=Mmsid （清华大学内网访问）
    MOOSAS文件格式转换自DeST:
    # 气象站编号
    # 无用，0
    # 小时数 int,0-8760
    # 空气温度 Dry Bulb Temperature
    # 空气含湿量 Humidity Ratio
    # 地面水平总辐射量 Global Horizontal Radiation
    # 地面水平散射辐射量 Diffuse Horizontal Radiation
    # 0.5m地面温度，按月平均拓展 Ground Temperature record in month
    # 天空有效温度 Effective Sky (Radiating) Temperature
    # 风速
    # 风向 C=0,NE=1,E=2....NW=15,N=16
    # 站点大气压 Atmospheric Station Pressure
    # ！未知数据,9999999
    所有数值精确到两位数
    :param epw_file: epw文件路径
    :return:weather:np.array格式csv文件
    '''
    with open(epw_file) as f:
        LOCATION = str(f.readline()).strip('\n').split(',')

        for i in range(2): f.readline()
        T_ground = str(f.readline()).strip('\n').split(',')[6:18]
        T_ground = [
            [T_ground[0]] * 31 * 24,
            [T_ground[1]] * 28 * 24,
            [T_ground[2]] * 31 * 24,
            [T_ground[3]] * 30 * 24,
            [T_ground[4]] * 31 * 24,
            [T_ground[5]] * 30 * 24,
            [T_ground[6]] * 31 * 24,
            [T_ground[7]] * 31 * 24,
            [T_ground[8]] * 30 * 24,
            [T_ground[9]] * 31 * 24,
            [T_ground[10]] * 30 * 24,
            [T_ground[11]] * 31 * 24,
        ]
        T_ground = [hr for mon in T_ground for hr in mon]

        for i in range(4): f.readline()
        climate_data = np.array([f.readline().strip('\n').split(',') for i in range(8760)])

        td = climate_data[:, 7].astype(float)
        # 含湿量计算，5次多项式拟合经验公式
        # ASHRAE. (2013). ASHRAE Handbook Fundamentals SI Edition
        # 林忠平. (2012). 不同地域特色村镇住宅生物质能利用技术与节能评价方法
        d = 3.703 + 0.286 * td + 9.164 * pow(0.1, 3) * pow(td, 2) + 1.446 * pow(0.1, 4) * pow(td, 3) + 1.741 * pow(0.1,
                                                                                                                   6) * pow(
            td, 4) + 5.195 * pow(0.1, 8) * pow(td, 5)

        # 天空有效温度计算
        # 刘森元,黄远锋.(1983). 天空有效温度的探讨
        HIR = climate_data[:, 12].astype(float)  # 天空水平红外辐射量 W/m2
        o_ = 5.67 * pow(10, -8)  # 斯特藩-玻尔兹曼常数
        T_sky = pow(HIR / o_, 0.25)

        # 风速转换
        vs = climate_data[:, 21].astype(float)
        vd = climate_data[:, 20].astype(float)
        for i in range(8760):
            if vd[i] == 999: vd[i] = 0
            vd[i] = np.round(vd[i] / 360 * 16, 0)
            if vs[i] != 0 and vd[i] == 0:
                vd[i] = 16

        weather = [
            [LOCATION[5][0:-1]] * 8760,  # 气象站编号
            [0] * 8760,  # 无用，0
            np.arange(8760),  # 小时数
            climate_data[:, 6].astype(float).round(2),  # 空气温度 Dry Bulb Temperature
            np.array(d).round(2),  # 空气含湿量 Humidity Ratio
            climate_data[:, 13].astype(float).round(2),  # 地面水平总辐射量 Global Horizontal Radiation
            climate_data[:, 15].astype(float).round(2),  # 地面水平散射辐射量 Diffuse Horizontal Radiation
            np.array(T_ground).astype(float).round(2),  # 0.5m地面温度，按月平均拓展 Ground Temperature record in month
            np.array(T_sky).astype(float).round(2),  # 天空有效温度 Effective Sky (Radiating) Temperature
            np.array(vs).astype(float).round(2),  # 风速
            np.array(vd).astype(int),  # 风向 C=0,NE=1,E=2....NW=15,N=16
            climate_data[:, 9].astype(float).round(2),  # 大气压 Atmospheric Station Pressure
            [9999999] * 8760  # ！未知数据
        ]
        return weather


def epw2wea(location, epw_file):
    '''
    RADIANCE/bin/epw2wea.exe
    SYNOPSIS
    epw2wea file_name.epw file_name.wea
    '''
    wea_file = os.path.join(temp_dic, location.stationId + '.wea')
    if not os.path.exists(temp_dic):
        os.makedirs(temp_dic)
    # command = ' '.join([epw2wea_exe, epw_file, wea_file])
    # os.popen(command)
    callCmd([epw2wea_exe, epw_file, wea_file])
    return wea_file


def cum_sky(location, weatherFile):
    mtx_file = os.path.join(temp_dic, location.stationId + '.mtx')
    # command=' '.join([gendaymtx_exe,'-D',sun_position,'-A -m 1 -c 1 1 1 -n -O1 ',weatherFile,'>',mtx_file])
    # command = ' '.join([gendaymtx_exe, '-A -m 1 -D -n -O1 ', weatherFile, '>', mtx_file])
    # command = ' '.join([gendaymtx_exe, '-m 1 -D -n -O1 ', weatherFile, '>', mtx_file])
    # print(command)
    # os.popen(command)
    callCmd([gendaymtx_exe, '-m 1 -D -n -O1 ', weatherFile, '>', mtx_file])
    mtx = []

    # 读取matrix文件
    with open(mtx_file, encoding='utf-8') as f:
        mtx_data = [f.readline() for i in range(1279114)]
        mtx = mtx_data[8:]
        mtx = [line.strip('\n').split(' ') for line in mtx if len(line.split(' ')) == 3]
        mtx = np.array(mtx).astype(float)

    '''Parse a row of gendaymtx RGB patch data in W/sr/m2 to radiation in kWh/m2.

    This includes aplying broadband weighting to the RGB bands, multiplication
    by the steradians of each patch, and multiplying by the duration of time that
    they sky matrix represents in hours.'''
    # RGB辐照度加权获得全色光平均辐照度
    mtx = np.array([0.265074126 * mtx[:, 0] + 0.670114631 * mtx[:, 1] + 0.064811243 * mtx[:, 2]])
    try:
        mtx = mtx.reshape([145, 8760])
    except:
        mtx = mtx.reshape([146, 8760])[:-1]
    # TREGENZA天空模型系数折算
    coff = np.repeat(TREGENZA_COEFFICIENTS, TREGENZA_PATCHES_PER_ROW).reshape([145, 1]) * 8760 / 1000
    mtx *= coff

    # mtx文件实在是太大了……
    os.remove(mtx_file)

    return mtx


def includeEpw(epw_file, city=None):
    if epw_file[-4:] != '.epw':
        raise Exception(f'******includeEpw wrong file type: {epw_file}')
    location = epw2location(epw_file)
    if city is not None:
        location.city = str(city)
    epw_csv = epw2csv(epw_file)
    epw_wea = epw2wea(location, epw_file)
    mtx = cum_sky(location, epw_wea)
    mtx = fix_rad(mtx, epw_csv[5])
    # 覆盖写入csv
    exist = False
    # print(weather_dic + r'\dest_station.csv')
    with open(stationInfo, 'r+') as wea:
        citys = wea.readlines()
        for line in citys:
            if re.search(location.stationId, line) != None:
                exist = True
    if not exist:
        with open(stationInfo, 'a') as wea:
            wea.write(location.__str__() + '\n')
    with open(weather_dic + '\\' + str(location.stationId) + '.csv', 'w+') as wea:
        epw_csv = np.array(epw_csv).T
        epw_csv = [','.join(line) + '\n' for line in epw_csv]
        wea.writelines(epw_csv)
    with open(weather_dic + r'\..\cum_sky\cumsky_' + str(location.stationId) + '.csv', 'w+') as wea:
        mtx = [','.join(line.astype(str)) + '\n' for line in mtx]
        wea.writelines(mtx)
    print(location.__str__())
    return str(location.stationId)


def fix_rad(calculate: np.ndarray, observe: np.ndarray):
    with open(sun_position, 'r+') as f:
        position = f.read().split('\n')
        position = [li.split(',') for li in position if len(li) > 0]
        position = np.array(position).astype(float)[:, 2]
        caculateGlobalRad = np.sum(calculate.T * position, axis=1)
        fixArr = []
        for c, o in zip(caculateGlobalRad.flatten(), observe.flatten()):
            if c == 0:
                fixArr.append(1.0)
            else:
                fixArr.append(o / c)
        calculate *= np.array(fixArr)
        return calculate
