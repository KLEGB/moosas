from __future__ import annotations
import string
import random
from .support import os, sys, np, json
from .error import FileError, ShellError


class MoosasPath(object):
    def __init__(self, MoosasPlusDirectory=None):
        if MoosasPlusDirectory is None:
            MoosasPlusDirectory = os.path.realpath(os.path.join(os.path.dirname(__file__), r'../'))
        MoosasPlusDirectory = os.path.abspath(MoosasPlusDirectory)
        self.moosasPlusDir = MoosasPlusDirectory
        self.libDir = os.path.join(MoosasPlusDirectory, 'libs')
        self.dataBaseDir = os.path.join(MoosasPlusDirectory, 'db')
        self.htmlDir = os.path.join(MoosasPlusDirectory, 'view')
        self.dataDir = os.path.join(MoosasPlusDirectory, 'data')
        self.tempDir = os.path.join(MoosasPlusDirectory, '__temp__')

        for thisDir in [self.libDir, self.dataDir, self.dataBaseDir, self.htmlDir, self.tempDir]:
            if not os.path.exists(thisDir):
                print(thisDir)
                os.mkdir(thisDir)

    @staticmethod
    def clean(dir):
        if os.path.exists(dir):
            remove = [os.remove(os.path.join(dir, dell)) for dell in os.listdir(dir)]
            return remove

    @staticmethod
    def checkBuildDir(*dir):
        for thisDir in dir:
            if not os.path.isdir(thisDir):
                thisDir = os.path.dirname(thisDir)
            if not os.path.exists(thisDir):
                os.mkdir(thisDir)

curPath = os.path.abspath('.')
os.chdir(os.path.dirname(__file__))
path = MoosasPath(open(r'_.pth').read().strip())
os.chdir(curPath)

def isFilePath(thePath):
    if "\\" in thePath or "/" in thePath:
        return True


def callCmd(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, block=True, cwd=None, _raise=False, **kwargs):
    """
    This method call the cmd using given args.

    stdin: change the standard input sys.stdin. You can send other input var stdin.write().
        however we suggest other way to do that: you can add '\n' in your args to run os like a bf batch file (*.bat).

    stdout: change the standard out sys.stdout. The message return from shell will be writen into this stdout by stdout.write()
        to write the message in a file, you can: with open(file.txt ,'w+') as f: callCmd(args,stdout=f)
        to ban the message from shell you can give None to stdout: callCmd(args,stdout=None)

    stderr: error will be skipped in this method. You can write the standard error by change the stderr to any file stream:
        with open(file.txt , 'w+') as f: callCmd(args,stderr=f)
        Otherwise the error will be print to console directly.

    block: decide whether to wait the shell until it finished. you can create a parallel program by setting this to False.
        however, reading the return from shell need to block the program,
        which means that you can get the return from cmd only if block==True

    cwd: on which dir the cmd call.

    kwargs: other arguments for os.popen()
    """
    if isinstance(args, str):
        args = [args]
    for i, arg in enumerate(args):
        if isFilePath(arg):
            args[i] = f"\"{arg}\""
    oldcwd = os.getcwd()
    oldstdin, oldstdout, oldstderr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin, sys.stdout, sys.stderr = stdin, stdout, stderr
    command = ' '.join(args)
    if cwd is not None:
        os.chdir(cwd)
    result = None
    try:
        print(f'Call:{command}')
        result = os.popen(command, **kwargs)
    except Exception as e:
        if not _raise:
            stderr.write(str(e))
            print('\033[40m' + f'Error occurred in shell:\n{command}:\n{e}' + '\033[0m')
            return -1
        else:
            raise ShellError(command.split(' ')[0], e)
    finally:
        os.chdir(oldcwd)
        sys.stdin, sys.stdout, sys.stderr = oldstdin, oldstdout, oldstderr
        if block and result is not None:
            s = result.read()
            return s


def mixItemListToObject(*itemOrList: list | object) -> np.ndarray | object:
    """mix item and list input to a uniform object output np.ndarray | object"""
    mixObject = []
    for itemList in itemOrList:
        mixObject = np.append(mixObject, np.array(itemList))
    if mixObject.size == 1:
        mixObject = mixObject.item()

    return mixObject


def mixItemListToList(*mixObject: list | object) -> list:
    """mix item and list input to a uniform list output np.ndarray"""
    mixList = []
    for obj in mixObject:
        mixList = np.append(mixList, obj)
    return list(np.array(mixList).flatten())


def generate_code(bit_num):
    """
    generate random code in given length.
    """
    all_str = string.digits + string.ascii_lowercase[0:11]
    code = ''.join([random.choice(all_str) for i in range(bit_num)])
    return '0x' + code


def encodeParams(*args) -> str:
    allChars = string.digits + string.ascii_lowercase[0:11]
    return '0x' + ''.join(
        [allChars[(int(a / len(allChars))) % len(allChars)] for a in args] +
        [allChars[int(a) % len(allChars)] for a in args]
    )


def searchBy(attribute: str, searchdata, searchList, earlyEnd=False, asObject=False) -> list:
    """
    search any data of any attribute in any enumerate object.

    ---------------------------------
    attribute: attribute to search, limitted to 1.
    searchdata: any data to match, you can give any type and any number of items.
    searchlist: list to search for the data.
    earlyEnd: if True, the search will end at the first matched element.
    asObject: if True, the search will return objects instead of index.

    returns: list of indexes that match the search data or object (if asObject==True)
    """

    targetlist = []
    if type(searchdata) != list or type(searchdata) != np.ndarray:
        searchdata = np.array([searchdata]).flatten()
    if len(searchdata) == 0:
        return targetlist
    for i in range(len(searchList)):
        if attribute in searchList[i].__dir__():
            if getattr(searchList[i], attribute) in searchdata:
                targetlist.append(i)
                if earlyEnd:
                    break
    if not asObject:
        return targetlist
    else:
        return np.array(searchList)[targetlist]


def to_dictionary(etree):
    """
        3d objects are not support in pygeos.to_geojson.
        in this case we must write the geojson by ourselves using the model.buildGeojson() method
        this method can reform the given elementTree (xml) into dictionary
    """
    children = list(etree)
    if len(children) == 0:
        return etree.text
    else:
        dictionary = {}
        for child in children:
            if child.tag not in dictionary.keys():
                dictionary[child.tag] = []
            dictionary[child.tag].append(to_dictionary(child))
        for key in dictionary.keys():
            if len(dictionary[key]) == 1:
                dictionary[key] = dictionary[key][0]
        return dictionary


def parseFile(file_path: str) -> list[list[list[str]]]:
    """
    General func to process all file in Moosas.
    a typical file should be:
    All input and output files in Moosas+ are encoded in a same file structure:<br>
    '!' means following string are annotations until the end of the line;<br>
    ';' blocks are split by ';'<br>
    '\n' items in a block are split by '\n' <br>
    Empty lines are valid. It will be regraded as an empty data<br>

    ! block 0
    data,data,data,data ! items 0 \n
    data,data,data,data ! items 1 \n
    data,data,data,data ! items 2 \n
    ...
    data,data,data,data ! items n \n
    ;
    ! block 1
    data,data,data,data ! items 0 \n
    data,data,data,data ! items 1 \n
    data,data,data,data ! items 2 \n
    ...
    data,data,data,data ! items n \n
    ;
    ...
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    try:
        blocks = ''
        returnBlocks = []
        with open(file_path, 'r') as f:
            blocks = f.read().split(';')
        for bl in blocks:
            lines = bl.split('\n')
            lines = [li.split('!')[0].strip().split(',') for li in lines]
            lines = [li for li in lines if len(li) > 0]
            lines = [li for li in lines if li[0] != '']
            returnBlocks.append(lines)
        return returnBlocks

    except:
        raise FileError(file_path)
