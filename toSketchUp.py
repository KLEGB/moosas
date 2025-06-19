import platform
import shutil

import requests
import zipfile
import os
moosasPath = os.path.abspath('.')
if not os.path.exists('python'):
       url = {'AMD64': r'https://www.python.org/ftp/python/3.11.3/python-3.11.3-embed-amd64.zip',
              'i386': r'https://www.python.org/ftp/python/3.11.3/python-3.11.3-embed-win32.zip',
              'aarch64': r'https://www.python.org/ftp/python/3.11.3/python-3.11.3-embed-arm64.zip'}
       try:
              url = url[platform.machine()]
       except:
              url = url['AMD64']

       print('Get embedded python from:',url)
       response = requests.get(url)

       if response.status_code == 200:
              print('Success. unzipped:', os.path.abspath('python'))
              zip_path = 'temp.zip'

              with open(zip_path, 'wb') as file:
                     file.write(response.content)

              with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                     zip_ref.extractall('python')
              os.remove(zip_path)


       else:
              raise ConnectionError(f'failed to get embedded python: {response.status_code}.\n '
                                    f'please download your compatible version from https://www.python.org/ftp/python/3.11.3/ \n'
                                    f'then unzip the python to {os.path.abspath("python")}')

print('Deploy python 3.11...')
shutil.copy(r'.\setup\get-pip.py',r'.\python\get-pip.py')
shutil.copy(r'.\setup\python311._pth', r'.\python\python311._pth')
with open(r'python\setupEnv.bat','w+') as f:
       f.write('python get-pip.py\n')
       f.write('.\python.exe -m pip install pydot==4.0.1\n')
       f.write(f'.\python.exe -m pip install -r {os.path.abspath("requirement.txt")} --no-warn-script-location\n')
os.chdir('python')
os.system('setupEnv.bat')

print('Deploy MoosasPy...')
os.chdir(moosasPath)
shutil.copytree('MoosasPy', r'python\Lib\MoosasPy')
with open(r'python\Lib\MoosasPy\utils\_.pth','w+') as f:
       f.write(moosasPath)
for _dir in ['db','doc','libs','data','src']:
       shutil.copytree(rf'python\Lib\MoosasPy\{_dir}', os.path.abspath(_dir))

print('Prepare sketchUp attachment...')
os.chdir('../')
with open('moosas.rb','w+') as f:
       f.write('Sketchup::require "moosas/MoosasMain"')
dels=False
if not os.path.exists('moosas'):
       shutil.copytree(moosasPath, 'moosas')
       dels = True
def zipdir(path, ziph):
       for root, dirs, files in os.walk(path):
              for file in files:
                     ziph.write(os.path.join(root, file))

with zipfile.ZipFile('moosas.zip', 'w') as zipObj:
       zipdir('moosas',zipObj)
       zipObj.write('moosas.rb')

os.rename('moosas.zip','moosas.rbz')
shutil.move('moosas.rbz',rf'{moosasPath}\moosas.rbz')
os.remove('moosas.rb')
if dels:
       shutil.rmtree('moosas')

print('SketchUp plug-in is ready in',os.path.abspath(rf'{moosasPath}\moosas.rbz'))