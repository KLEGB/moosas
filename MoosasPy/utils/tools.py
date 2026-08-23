from __future__ import annotations
import string
import random
import shutil
from .support import os, sys, np, json
from .error import FileError, ShellError


class MoosasPath(object):
    def __init__(self, MoosasPlusDirectory=None):
        """
        Initialize the MoosasPlus environment with directory paths.
        
        Parameters
        ----------
        MoosasPlusDirectory : str, optional
            Root directory for MoosasPlus. If None, defaults to the parent directory
            of the current file's directory. Will be converted to an absolute path.
        
        Returns
        -------
        None
        """
        if MoosasPlusDirectory is None:
            MoosasPlusDirectory = os.path.realpath(os.path.join(os.path.dirname(__file__), r'../'))
        MoosasPlusDirectory = os.path.abspath(MoosasPlusDirectory)
        self.moosasPlusDir = MoosasPlusDirectory
        self.libDir = os.path.join(MoosasPlusDirectory, 'libs')
        self.dataBaseDir = os.path.join(MoosasPlusDirectory, 'db')
        self.dataDir = os.path.join(MoosasPlusDirectory, 'data')
        self.tempDir = os.path.join(MoosasPlusDirectory, '__temp__')

        for thisDir in [self.libDir, self.dataDir, self.dataBaseDir, self.tempDir]:
            if not os.path.exists(thisDir):
                print(thisDir)
                os.mkdir(thisDir)

    @staticmethod
    def clean(dir):
        """
        Clean all files in the specified directory.
        
        Parameters
        ----------
        dir : str
            Path to the directory whose files are to be removed.
        
        Returns
        -------
        list
            A list of removed paths.
        """
        if os.path.exists(dir):
            removed = []
            for dell in os.listdir(dir):
                target = os.path.join(dir, dell)
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                removed.append(target)
            return removed

    @staticmethod
    def checkBuildDir(*dir):
        """
        Check and create build directories if they do not exist.
        
        Parameters
        ----------
        *dir : str
            Variable number of directory paths to check. If a given path is not an existing directory, 
            its parent directory is used instead. For each valid directory path, if it does not exist, 
            it will be created.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        for thisDir in dir:
            if not os.path.isdir(thisDir):
                thisDir = os.path.dirname(thisDir)
            if not os.path.exists(thisDir):
                os.mkdir(thisDir)

with open(os.path.join(os.path.dirname(__file__), '_.pth'), encoding='utf-8') as path_file:
    path = MoosasPath(os.path.join(os.path.dirname(__file__), path_file.read().strip()))

def isFilePath(thePath):
    """
    Check if the given string contains path separators indicating it is a file path.
    
    Parameters
    ----------
    thePath : str
        The string to check for file path separators.
    
    Returns
    -------
    bool
        True if the string contains '\\' or '/', False otherwise.
    """
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
    # from app.core.logger import log_custom
    # log_custom(f'Call cmd: {command}', level='info')
    try:
        # Keep shell command logging opt-in to avoid console flooding in batch runs.
        if os.environ.get("MOOSAS_SHOW_CALL_CMD", "").strip().lower() in {"1", "true", "yes", "on"}:
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
    elif len(mixObject) ==0:
        return None
    return mixObject


def mixItemListToList(*mixObject: list | object) -> list:
    """mix item and list input to a uniform list output np.ndarray"""
    mixList = []
    for obj in mixObject:
        mixList = np.append(mixList, obj)
    return list(np.array(mixList).flatten())


def generate_code(bit_num):
    """
    Generate a random hexadecimal-like code of specified length.
    
    Parameters
    ----------
    bit_num : int
        The number of characters in the generated code (excluding the '0x' prefix).
    
    Returns
    -------
    str
        A string representing the generated code, prefixed with '0x'.
    """
    """
    generate random code in given length.
    """
    all_str = string.digits + string.ascii_lowercase[0:11]
    code = ''.join([random.choice(all_str) for i in range(bit_num)])
    return '0x' + code


def encodeParams(*args) -> str:
    """
    Encode a variable number of integer arguments into a hexadecimal-like string representation.
    
    Parameters
    ----------
    *args : int
        Variable length argument list of integers to be encoded.
    
    Returns
    -------
    str
        A string starting with '0x' followed by encoded characters representing the input integers.
        The encoding uses digits 0-9 and lowercase letters 'a' to 'k' (first 11 ASCII lowercase letters).
    """
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
    Convert an ElementTree XML object to a nested dictionary.
    
    Parameters
    ----------
    etree : xml.etree.ElementTree.Element
        The input ElementTree element to be converted into a dictionary.
        The function recursively processes its children and attributes.
    
    Returns
    -------
    dict or str
        A dictionary representation of the XML structure where each tag becomes a key.
        If an element has no children, its text content is returned as a string.
        Nested elements are represented as nested dictionaries or lists if multiple
        elements with the same tag exist.
    """
    """
        3d objects are not support in shapely.to_geojson.
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
    Parse a file into a nested list structure based on Moosas+ file format.
    
    Parameters
    ----------
    file_path : str
        Path to the input file to be parsed. The file should follow the Moosas+ format
        with blocks separated by ';' and lines separated by '\n'. Lines may contain
        comments starting with '!' and data items separated by commas.
    
    Returns
    -------
    list[list[list[str]]]
        A list of blocks, where each block is a list of lines, and each line is a list of strings
        representing the parsed data items. Empty lines or comment-only lines are excluded.
    """
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
