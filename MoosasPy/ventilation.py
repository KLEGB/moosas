"""
    Simulating buoyancy effect by contamX based on Mass Flow Balance in Air Flow Network.
    More information can be found in this article:

    To build the *.prj file and *.info zoneInfo file,
    you can call vent.buildPrj(), vent.buildNetworkFile() or vent.buildZoneInfoFile()
"""

import time
from .vent.conread import *
import csv
import random
from .utils.tools import path, callCmd,parseFile
import os

working_dir = os.path.join(path.libDir, r'vent')
FilePath = {
    'contamx': working_dir + r'\contam\contamx3.exe',
    'contamw': working_dir + r'\contam\contamw3.exe',
    'simread': working_dir + r'\contam\simread.exe',
    'response': working_dir + r'\contam\response.txt',
    'roomInfo': path.dataDir + r'\vent\roomInfo.txt',
    'project_dir': path.dataDir + r'\vent\project',
    'contam_dir': working_dir + r'\contam',
    'result_dir': path.dataDir + r'\vent\result',
}
DEFAULT_INDOOR_TEMPERATURE = 298.15


class ZoneResult(object):
    """
        A structure to record the analysis result.
        name: zone name in the prj file
        heat: zone total heat load
        volume: zone space volume
        userName: users define name of the zone, default is MoosasSpace.id
        temperature: a list[float] for temperature result in C. inf if invalid.
        ACH: a list[float] for mass flow result in m3/h. inf if invalid.
    """
    __slots__ = ['name', 'heat', 'volume', 'userName', 'temperature', 'ACH', 'thermalParams']

    def __init__(self, name=None, heat=None, volume=None, userName=None):
        super(ZoneResult, self).__init__()
        self.name = name
        self.heat = float(heat)
        self.volume = volume
        self.userName = userName
        self.temperature: list[float] = []
        self.ACH: list[float] = []


def iterateProjects(prjFiles, zoneInfoFiles, concatResultFile=None, outdoorTemperature=20, maxIteration=10,
                    exitResidual=0.01) -> list[ZoneResult]:
    """
    Enter method for contam_iteration().
    This method allow users to give multi project file for calculation.
    In this way, separated Air Flow Network can be calculated individually to escape from error.
    The result will be merged together finally.
    ---------------------------------

    prjFiles: Contam project files. Initial indoor temperature should be carefully defined in this file.
        Users can use the contamW3.exe to build this file by a GUI.
        Documents about contamX and contamW can be found at:
        https://www.nist.gov/el/energy-and-environment-division-73200/nist-multizone-modeling/software/contam/documentation

    zoneInfoFiles: standard roomInfo files:
        [[prjroomname, roomheatload, userroomname]..[]]
        in which:
            prjroomname: the room name set in the *.prj file, must be the same in every character
            roomheatload: the gross load of the room in (W).
            userroomname: the room name define by the users, and it will occur in the result file.

        The roomInfo file can exclude the roomname and only provide roomInfo, which means that:
        the room heat file can only have 2 columns:
        [[prjroomname,roomheatload]...[]]
        in this case, the roomnome will be the same to the prjroomname

        or 2 columns:
        [[roomheatload,usersroomname]...[]]
        iin this case, the roomInfo data should be in the same sequence of zones in the project file

        or only 1 column:
        [[roomheatload]...[]]
        in this case, the roomheatload data should be in the same sequence of zones in the project file

    concatResultFile: all result will be merged into this file.

    outdoorTemperature: The static outdoor temperature.
        Notice that only the indoor/outdoor temperature difference will be considered in contamX,
        which means that #25 indoor 20 outdoor# is equal to #20 outdoor 15 indoor#.

    maxIteration: how many times contamX should run.
    """
    print('auto contamx iteration for buoyancy ventilation')
    print(f'prj files:{prjFiles}')
    print(f'roomInfo files:{zoneInfoFiles}')
    print('------------------------------')
    if isinstance(prjFiles, str):
        prjFiles = [prjFiles]
    if isinstance(zoneInfoFiles, str):
        zoneInfoFiles = [zoneInfoFiles]
    resultFiles = [os.path.join(path.tempDir, os.path.basename(prj)[:-4] + '_result.csv') for prj in prjFiles]
    if concatResultFile is None:
        concatResultFile = FilePath['result_dir'] + 'concatResult.csv'
    if os.path.exists(FilePath['result_dir']):
        path.clean(FilePath['result_dir'])

    allZones = []
    for prj, heat, res in zip(prjFiles, zoneInfoFiles, resultFiles):
        allZones += contam_iteration(prjFile=prj,
                                     zoneInfoFile=heat,
                                     resultFile=res,
                                     outdoorTemperature=outdoorTemperature, maxIteration=int(maxIteration),
                                     exitResidual=float(exitResidual))

    writeZone(concatResultFile, allZones)
    print('------------------------------')
    print('result in ', concatResultFile)
    return allZones


def contam_iteration(prjFile, zoneInfoFile, resultFile=None, outdoorTemperature=25, maxIteration=50,
                     exitResidual=0.01) -> list[ZoneResult]:
    """
    Simulating buoyancy effect by contamx based on Mass Flow Balance in Air Flow Network.
    More information can be found in this article:

    -----------------------------------------
    prjFile: single contam project file. Initial indoor temperature should be carefully defined in this file.
        Users can use the contamW3.exe to build this file by a GUI.
        Documents about contamX and contamW can be found at:
        https://www.nist.gov/el/energy-and-environment-division-73200/nist-multizone-modeling/software/contam/documentation

    zoneInfoFile: a standard roomInfo file or roomInfo data should be given here:
        [[prjroomname, roomheatload, userroomname]..[]]
        in which:
            prjroomname: the room name set in the *.prj file, must be the same in every character
            roomheatload: the gross load of the room in (W).
            userroomname: the room name define by the users, and it will occur in the result file.

        The roomInfo file can exclude the roomname and only provide roomInfo, which means that:

        the room heat file can only have 2 columns:
        [[prjroomname,roomheatload]...[]]
        in this case, the roomnome will be the same to the prjroomname

        or 2 columns:
        [[roomheatload,usersroomname]...[]]
        iin this case, the roomInfo data should be in the same sequence of zones in the project file

        or only 1 column:
        [[roomheatload]...[]]
        in this case, the roomheatload data should be in the same sequence of zones in the project file

        Of course, you can get a roomInfo series by MoosasModel.buildRoomHeat() method, then directly send as this argument

    resultFile: the iteration result path, will be coded into csv.
        In this file, the temperature changes and Volume Metric Flow Rate in ACH will be recorded.
        You can find all processing prj file in FilePath['project_dir'] and read the Air Flow Network by contamW.

    outdoorTemperature: The static outdoor temperature.
        Notice that only the indoor/outdoor temperature difference will be considered in contamX,
        which means that #25 indoor 20 outdoor# is equal to #20 outdoor 15 indoor#.

    maxIteration: The max iterations contamX should run.

    exitResidual: Stop iteration if overall Residual is smaller than this value
    """
    iteration = 0
    residual = 100.0

    """preparing the file"""
    FilePath['roomInfo'] = zoneInfoFile
    FilePath['project_file'] = prjFile
    if not test_exist():
        raise Exception('Error occurred while checking files.')
    path.clean(FilePath['project_dir'])
    FilePath['current_file'] = FilePath['project_file'][:-4] + str(iteration) + '.prj'
    FilePath['current_file'] = os.path.normpath(
        os.path.join(FilePath['project_dir'], os.path.basename(FilePath['current_file'])))
    callCmd(['copy',
             "\"" + os.path.normpath(FilePath['project_file']) + "\"",
             "\"" + FilePath['current_file'] + "\""
             ])

    """build zone series"""
    tempResult, ACHresult = [], []
    zones = readZoneInfo(FilePath['project_file'], FilePath['roomInfo'])
    invalidRoom = np.array([False] * len(zones))

    """start iteration"""
    while iteration <= maxIteration and residual > exitResidual:
        iteration += 1

        """copy prj file"""
        file0 = FilePath['current_file']
        FilePath['current_file'] = FilePath['project_file'][:-4] + str(iteration) + '.prj'
        FilePath['current_file'] = os.path.normpath(
            os.path.join(FilePath['project_dir'], os.path.basename(FilePath['current_file'])))
        callCmd(['copy',
                 "\"" + file0 + "\"",
                 "\"" + FilePath['current_file'] + "\""
                 ])
        print('------------------------------')
        print("Iteration", iteration, FilePath['current_file'])

        """run contamx.exe"""
        run_contam(exe=FilePath['contamx'], file=os.path.join(FilePath['project_dir'], FilePath['current_file']))

        """run simread.exe"""
        exe_simread(simread_path=FilePath['simread'], file_path=FilePath['current_file'],
                    responseFile=FilePath['response'])

        """build AirFlowNetwork matrix, in which zone_length includes outdoor"""
        try:
            AFN = build_matrix(file_path=FilePath['current_file'])
            # with open('temp.csv','w+') as f:
            #    f.write('\n'.join([','.join(li) for li in AFN.astype(str)]))

            """calculating the room indoor temperature"""
            temperature = change_temperature(AFN=AFN, roomInfo=np.array([z.heat for z in zones]), t0=outdoorTemperature)
            tempIteration = (np.array(temperature) - 273.15).flatten().tolist() + [outdoorTemperature]
            for i in range(temperature.shape[1]):
                if temperature[0, i] < 200 or temperature[0, i] > 375:
                    invalidRoom[i] = True
                    temperature[0, i] = DEFAULT_INDOOR_TEMPERATURE
                    tempIteration[i] = 'inf'
                    print(
                        '\033[40m' + f'Warrning: irregular temperature will be fix to 27C and inf in result' + '\033[0m')

            achIteration = [max(x, y) for x, y in zip(AFN[-1], AFN[:, -1])]
            tempResult.append(tempIteration)
            ACHresult.append(achIteration)
            for i in range(len(zones)):
                zones[i].temperature.append(tempIteration[i])
                zones[i].ACH.append(achIteration[i])

            """calculating residual on temperature and flow rate"""
            if len(tempResult) > 1:
                thisResult = [tempResult[-1][i] for i in range(len(tempResult[-1]) - 1) if not invalidRoom[i]]
                lastResult = [tempResult[-2][i] for i in range(len(tempResult[-2]) - 1) if not invalidRoom[i]]
                zoneNames = [zones[i].userName for i in range(len(tempResult[-1]) - 1) if not invalidRoom[i]]
                print()
                print('\t'.join(['Residual:'] + zoneNames))
                residual1 = [(thisResult[i] - lastResult[i]) / lastResult[i] for i in range(len(thisResult))]
                print('\t'.join(['Temperature'] + [str(np.abs(np.round(z, 4))) for z in residual1]))
                print(' \t\t\t' + '\t'.join(np.round(thisResult, 2).astype(str)))

                thisResult = [ACHresult[-1][i] for i in range(len(ACHresult[-1]) - 1) if not invalidRoom[i]]
                lastResult = [ACHresult[-2][i] for i in range(len(ACHresult[-2]) - 1) if not invalidRoom[i]]
                print('\t'.join(['Residual:'] + zoneNames))
                residual2 = [(thisResult[i] - lastResult[i]) / lastResult[i] for i in range(len(thisResult))]
                print('\t'.join(['Mass Flow'] + [str(np.abs(np.round(z, 4))) for z in residual2]))
                print(' \t\t\t' + '\t'.join(np.round(thisResult, 1).astype(str)))
                residual = np.mean(np.abs(residual1 + residual2))

            """write the data into prj file"""
            print(f'writing: {prjFile}')
            head, temp, rear = read_file(FilePath['current_file'])
            temp_revise = np.array(
                [re.split(r'[ ]+', li) for li in temp.split('\n')[0:-1]])  # change the temperature info
            temp_revise[:, 9] = temperature
            temp_revise = '\n'.join([' '.join(li) for li in temp_revise]) + '\n'
            write_file(FilePath['current_file'], head, temp_revise, rear)

        except Exception as e:
            print('\033[40m' + f'Error occurred and simulation has collapsed: {e}' + '\033[0m')
            return zones

        finally:
            if resultFile is not None:
                """write the result"""
                print(f'writing: {resultFile}')
                writeZone(resultFile, zones)

    if resultFile is None:
        return writeZone(resultFile, zones)
    print('simulation finished :', resultFile)
    return zones


def readZoneInfo(prjFile, roomInfoFile):
    """
    Build the zone list by combining the data in prjFile and roomInfoFile.
    in this method we will read standard roomInfo file into:
    [[prjroomname,roomheatload,usersroomname]...[]]

    the room heat file can only have 2 columns:
    [[prjroomname,roomheatload]...[]]
    in this case, the roomnome will be the same to the prjroomname

    or 2 columns:
    [[roomheatload,usersroomname]...[]]
    iin this case, the roomInfo data should be in the same sequence of zones in the project file

    or only 1 column:
    [[roomheatload]...[]]
    in this case, the roomInfo data should be in the same sequence of zones in the project file
    """
    if not isinstance(roomInfoFile, str):
        return roomInfoFile
    roomInfo = []
    roomInfodata = parseFile(roomInfoFile)[0]
    for data in roomInfodata:
            if len(data) == 3:
                # zoneName in prjFile, zone heat load, user define zoneName
                roomInfo.append([data[0], float(data[1]), data[2]])
            elif len(data) == 2:
                dig = data[0].split('.')
                if dig[0].isdigit():
                    # zone heat load, user define zoneName
                    roomInfo.append([None, float(data[0]), data[1]])
                else:
                    # zoneName in prjFile, zone heat load
                    roomInfo.append([data[0], float(data[1]), data[0]])
            elif len(data) == 1:
                roomInfo.append([None, float(data[0]), None])
    roomInfo = np.array(roomInfo)
    # read room volume and name in the prj file
    vol, room_name = read_zone(prjFile)

    if None in roomInfo[:, 0].flatten():
        if len(room_name) != len(roomInfo):
            raise Exception('Error in file preparing: roomInfoFile is not in the same len to the project file.')
        roomInfoRoomName = room_name
    else:
        roomInfoRoomName = roomInfo[:, 0].flatten().tolist()
    zones: list[ZoneResult] = []
    for name, vol in zip(np.array(room_name).flatten(), np.array(vol).flatten()):
        if name not in roomInfoRoomName:
            raise Exception(f'Error in file preparing: zone {name} not found in roomInfoFile.')
        info = roomInfo[roomInfoRoomName.index(name)]
        zones.append(ZoneResult(
            name=name,
            volume=vol,
            heat=info[1],
            userName=info[2]
        ))

    return zones


def run_contam(exe, file):
    if not os.path.exists(exe):
        print('error: contamx.exe not found')
        return False
    if not os.path.exists(file):
        print('error: ' + file + ' not found')
        return False
    callCmd([exe, file])
    return True


def change_temperature(AFN: np.ndarray, roomInfo: np.ndarray, t0):
    """
    calculate indoor temperature via Mass Flow Balance in the network.

    AFN: the clean matrix of Air Flow Network, include outdoor air.
    roomInfo: roomInfo data, which have the same len to the rooms.
    t0: outdoorTemperature
    """
    AFN = np.asmatrix(AFN)
    roomInfo = np.asmatrix(roomInfo)

    for i in range(len(AFN)):
        AFN[i, i] = -np.sum(AFN[:, i])
        for j in range(len(AFN) - 1):
            if AFN[j, i] == 0: AFN[j, i] = -0.0001
            AFN[j, i] += AFN[j, i] * random.randrange(-100, 100) * 0.01 * 0.001

    Qout = AFN[-1, 0:-1] * (t0 * 1.2 / 3600 * 1005)
    dH = roomInfo + Qout

    AFN *= (1.2 / 3600 * 1005)

    t = -dH * AFN[0:-1, 0:-1].I
    temperature = 273.15 + t
    return temperature


def test_exist():
    # for file in FilePath.keys():
    #    if file != skip and file[-3:]!='dir':
    #        if not os.path.exists(FilePath[file]):
    #            print('File not found:',FilePath[file])
    #            return False
    if os.path.exists(FilePath['project_dir']):
        path.clean(FilePath['project_dir'])
    if not os.path.exists(FilePath['project_dir']):
        os.mkdir(FilePath['project_dir'])
    if not os.path.exists(FilePath['contam_dir']):
        return False
    if not os.path.exists(FilePath['project_file']):
        return False

    if not os.path.exists(FilePath['result_dir']):
        os.mkdir(FilePath['result_dir'])
    return True


def wait(file):
    for i in range(100):
        if os.path.exists(file):
            return True
        else:
            print('waiting:', file)
            time.sleep(0.1)
    raise Exception('Return file error:', file)


def writeZone(resultFile, zones):
    lines = [['!prjZoneName'] + [z.name for z in zones]]
    lines += [['!zoneHeatLoad'] + [z.heat for z in zones]]
    lines += [['!zoneVolume'] + [z.volume for z in zones]]
    lines += [['!ACH'] + [z.userName for z in zones]]
    lines += [[i] + [z.ACH[i] for z in zones] for i in range(len(zones[0].ACH))]
    lines += [['!Temperature'] + [z.userName for z in zones]]
    lines += [[i] + [z.temperature[i] for z in zones] for i in range(len(zones[0].temperature))]
    if resultFile is not None:
        path.checkBuildDir(resultFile)
        with open(resultFile, 'w+', newline='') as f:
            csv.writer(f).writerows(lines)
    return '\n'.join([','.join(np.array(li).astype(str)) for li in lines])


if __name__ == '__main__':
    prjfile = '.\data\\' + [file for file in os.listdir('../data') if file[-3:] == 'prj'][0]
    roomInfo_file = r'../data/roomInfo.txt'
    # contam_iteration(r'C:\Users\Lenovo\PycharmProjects\ComtamW\data\kunming_old.prj',r'C:\Users\Lenovo\PycharmProjects\ComtamW\data\roomInfo_old.txt')
    # contam_iteration(r'.\data\ttt.prj', r'.\data\roomInfottt.txt')
    contam_iteration(prjfile,
                     roomInfo_file)
