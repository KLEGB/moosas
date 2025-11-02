"""
    Simulating buoyancy effect by contamX based on Mass Flow Balance in Air Flow Network.
    More information can be found in this article:

    To build the *.prj file and *.info zoneInfo file,
    you can call vent.buildPrj(), vent.buildNetworkFile() or vent.buildZoneInfoFile()
"""

import time
from .conread import *
import csv
import random
from ..utils.tools import path, callCmd,parseFile
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
        """
        Initialize a ZoneResult instance with optional parameters.
        
        Parameters
        ----------
        name : str, optional
            Name of the zone. Default is None.
        heat : float, optional
            Heat value associated with the zone. Will be converted to float. Default is None.
        volume : float, optional
            Volume of the zone. Default is None.
        userName : str, optional
            User-defined name for the zone. Default is None.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
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
    Iterate over multiple CONTAM project files to perform buoyancy ventilation simulations and merge results.
    
    Parameters
    ----------
    prjFiles : str or list of str
        Path(s) to CONTAM project file(s) (.prj). If a string is provided, it will be converted to a list.
        Initial indoor temperature must be defined in these files.
    zoneInfoFiles : str or list of str
        Path(s) to zone information file(s), each containing room-specific data. Each file should contain
        one or more of the following formats:
        - [[prjroomname, roomheatload, userroomname], ...]
        - [[prjroomname, roomheatload], ...] (userroomname defaults to prjroomname)
        - [[roomheatload, userroomname], ...] (order matches zones in .prj)
        - [[roomheatload], ...] (order matches zones in .prj)
    concatResultFile : str, optional
        Path to the output CSV file where all merged results will be saved. If not provided, defaults to
        'concatResult.csv' in the result directory.
    outdoorTemperature : float, default 20
        Static outdoor temperature in degrees Celsius. Only the temperature difference between indoor and
        outdoor is considered in the simulation.
    maxIteration : int, default 10
        Maximum number of iterations for the CONTAM simulation.
    exitResidual : float, default 0.01
        Convergence criterion; simulation stops when residual falls below this value.
    
    Returns
    -------
    list of ZoneResult
        A list of ZoneResult objects, each representing the simulation result for a zone.
    """
    """
    Enter method for iterateFile().
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
        allZones += iterateFile(prjFile=prj,
                                zoneInfoFile=heat,
                                resultFile=res,
                                outdoorTemperature=outdoorTemperature, maxIteration=int(maxIteration),
                                exitResidual=float(exitResidual))

    writeZone(concatResultFile, allZones)
    print('------------------------------')
    print('result in ', concatResultFile)
    return allZones


def iterateFile(prjFile, zoneInfoFile, resultFile=None, outdoorTemperature=25, maxIteration=50,
                exitResidual=0.01) -> list[ZoneResult]:
    """
    Simulate buoyancy-driven airflow in a building using CONTAMX based on mass flow balance in an air flow network.
    
    Parameters
    ----------
    prjFile : str
        Path to the CONTAM project file (.prj). The initial indoor temperature must be defined in this file.
        This file can be created using CONTAMW3 GUI. See NIST documentation for details.
    zoneInfoFile : str or list[list]
        Path to a room information file or direct data in list format. Each entry contains zone-specific data:
        [prjroomname, roomheatload, userroomname] or variations with 1-2 columns as described below:
        
        - 3 columns: [prjroomname (str), roomheatload (float), userroomname (str)]
        - 2 columns: [prjroomname, roomheatload] → userroomname defaults to prjroomname
        - 2 columns: [roomheatload, userroomname] → assumes order matches zones in .prj file
        - 1 column: [roomheatload] → values assigned sequentially to zones in .prj file
        
        Alternatively, output from `MoosasModel.buildRoomHeat()` can be passed directly.
    resultFile : str, optional
        Path to save iteration results as CSV. Records indoor temperature (°C) and ACH over iterations.
        If None, results are not saved to file. Default is None.
    outdoorTemperature : float, default=25
        Outdoor air temperature in °C. Only temperature difference between indoor and outdoor affects simulation.
    maxIteration : int, default=50
        Maximum number of iterations before stopping, regardless of convergence.
    exitResidual : float, default=0.01
        Convergence threshold. Iteration stops when mean absolute residual (temperature and airflow) falls below this value.
    
    Returns
    -------
    list[ZoneResult]
        List of ZoneResult objects containing per-zone results including:
        - temperature history (in °C)
        - air change rate (ACH) history
        - zone names (project and user-defined)
        - heat loads
        Each object corresponds to a zone in the project file.
    """
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

        Of course, you can get a roomInfo series by MoosasModel.buildRoomHeat() method, then directly send as the argument

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
        execContam(exe=FilePath['contamx'], file=os.path.join(FilePath['project_dir'], FilePath['current_file']))

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
    callCmd(['copy',
             "\"" + FilePath['current_file'] + "\"",
             "\"" + prjFile[:-4]+'_final.prj' + "\""
             ])
    return zones

def runFile(prjFiles):
    """run and read the AirFlowNetwork result of a *.prj file.

    -----------------------------------------
    prjFile: path of the prj file. the *.lfr file should be in the same directory and has same basename

    return: None
    """
    if isinstance(prjFiles, str):
        prjFiles = [prjFiles]
    for prjFile in prjFiles:
        execContam(exe=FilePath['contamx'], file=prjFile)

        """run simread.exe"""
        exe_simread(simread_path=FilePath['simread'], file_path=prjFile,
                    responseFile=FilePath['response'])



def readZoneInfo(prjFile, roomInfoFile):
    """
    Build a list of ZoneResult objects by combining zone data from project and room info files.
    
    Parameters
    ----------
    prjFile : str
        Path to the project file containing zone names and volumes.
    roomInfoFile : str or list of lists
        Path to the room information file or a pre-parsed list of lists containing room heat load data.
        The file can have one of the following formats:
        - 3 columns: [prjroomname, roomheatload, usersroomname]
        - 2 columns: [prjroomname, roomheatload] (usersroomname defaults to prjroomname)
        - 2 columns: [roomheatload, usersroomname] (must match project zone order)
        - 1 column: [roomheatload] (must match project zone order)
    
    Returns
    -------
    list of ZoneResult
        A list of ZoneResult objects containing zone name, volume, heat load, and user-defined name.
    """
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


def execContam(exe, file):
    """
    Execute CONTAM simulation using the specified executable and input file.
    
    Parameters
    ----------
    exe : str
        Path to the CONTAMX executable file.
    file : str
        Path to the input project file for the simulation.
    
    Returns
    -------
    bool
        True if the execution command was successfully called, False if either the executable or input file does not exist.
    """
    if not os.path.exists(exe):
        print('error: contamx.exe not found')
        return False
    if not os.path.exists(file):
        print('error: ' + file + ' not found')
        return False
    callCmd([exe, file])
    return True

def readPathResult(prjFile,netFile=None):
    """read *.lfr file and translate the mass flow to volumetric flow

    -----------------------------------------
    prjFile: path of the prj file. the *.lfr file should be in the same directory and has same basename

    netFile: optional network file to name the zones and paths

    return: dict{
                #{pathName or pathIndex}:{
                    'from':#{zoneName or zoneIndex},'to':#{zoneName or zoneIndex}',flow:#{volumetric flow m3/h}
                }
            }
    """

    airflow = read_flowpath(prjFile[:-4] + '.lfr') * 3600.0 / AIR_DENSITY
    topology = read_topology(prjFile)
    if netFile:
        zoneName,pathName = [],[]
        strs = parseFile(netFile)
        zoneStr = strs[0]
        pathStr = strs[1]
        zoneName = [line[0] for line in zoneStr if len(line) > 1]
        pathName = [line[0] for line in pathStr if len(line) > 1]
        zoneName=['ambient']+zoneName
        topology = [[max(flow[0],0),max(flow[1],0)] for flow in topology]
        topology = {pathName[i]:{'from':zoneName[topology[i][0]],"to":zoneName[topology[i][1]],'flow':airflow[i][0]+airflow[i][1]} for i in range(len(topology))}

    else:
        topology = {i: {'from': topology[i][0], "to":topology[i][1],'flow': airflow[i][0] + airflow[i][1]} for i in range(len(topology))}
    return topology


def change_temperature(AFN: np.ndarray, roomInfo: np.ndarray, t0):
    """
    Calculate indoor temperatures using mass flow balance in an air flow network.
    
    Parameters
    ----------
    AFN : numpy.ndarray
        The clean matrix of Air Flow Network, including outdoor air connections.
        Modified in-place to adjust diagonal elements and off-diagonal zero entries.
    roomInfo : numpy.ndarray
        Room-specific information array with length matching the number of rooms.
        Represents internal heat data or similar room properties.
    t0 : float or int
        Outdoor temperature in degrees Celsius, used to compute heat exchange
        from outside air.
    
    Returns
    -------
    numpy.ndarray
        Array of indoor temperatures in Kelvin, calculated based on energy balance.
        The result is obtained by solving a linear system derived from the modified
        AFN matrix and adjusted room heat gains, then converting from Celsius to Kelvin.
    """
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
    """
    Check existence and set up necessary directories and files for the project.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    bool
        True if all required paths exist (or are created successfully), False otherwise.
    """
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
    """
    Wait for a file to exist by checking at regular intervals.
    
    Parameters
    ----------
    file : str
        The path of the file to wait for.
    
    Returns
    -------
    bool
        True if the file exists within the waiting period.
    """
    for i in range(100):
        if os.path.exists(file):
            return True
        else:
            print('waiting:', file)
            time.sleep(0.1)
    raise Exception('Return file error:', file)


def writeZone(resultFile, zones):
    """
    Write zone data to a CSV file and return it as a formatted string.
    
    Parameters
    ----------
    resultFile : str or None
        Path to the output CSV file. If None, the data is not written to a file.
    zones : list of object
        List of zone objects, each having attributes `name`, `heat`, `volume`, 
        `userName`, `ACH` (list), and `temperature` (list).
    
    Returns
    -------
    str
        A string representation of the CSV data, with rows separated by newlines
        and columns separated by commas.
    """
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
    # iterateFile(r'C:\Users\Lenovo\PycharmProjects\ComtamW\data\kunming_old.prj',r'C:\Users\Lenovo\PycharmProjects\ComtamW\data\roomInfo_old.txt')
    # iterateFile(r'.\data\ttt.prj', r'.\data\roomInfottt.txt')
    iterateFile(prjfile,
                roomInfo_file)
