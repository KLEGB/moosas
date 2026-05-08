# MOOSAS+
Moosas is a SketchUp plugin program working on **building performance anaylsis 
and optimization for the building sketch design stage**. 
Most of the detail settings and geometrical representations transforming, 
which are always confusing to architects, will be solved behind the interface. 
The core of MOOSAS is built on ruby, the interface is built on javascript & html, 
and the extensions are built on python and golong including *.epw transformation, 
*.geo\*.obj transformation, wind pressure prediction, etc.
<br> Moosas+ is the **plug-in version** for moosas, 
which is detached from sketchUp for better compatibility of any other software.
<br> In this package we have provided a isolated python environment in pythonDict, 
which allow any users to call Moosas function without installation of python as well as 
have better stability while using Moosas.

## Installation of the plugin
Document all the file you get from the git into:<br>
**pkpm_moosas/<br>**
Write following strings by notepad and save as **pkpm_moosas.rb**<br>
Sketchup::require "pkpm_moosas/MoosasMain"  
zip the directory and the pkpm_moosas.rb into a zip file and rename it as **pkpm_moosas.rbz**
- pkpm_moosas.rb
- pkpm_moosas/
- |- python
- |- src
- |- db
- ...

...***OR***...You can run to_rbz.bat, and get a clean **pkpm_moosas.rbz** directly.  
Besides, if you want to try CFD in Moosas, you need to download blueCFD 2017-1 from [here](https://github.com/blueCFD/Core/releases/download/blueCFD-Core-2017-1/blueCFD-Core-2017-1-win64-setup.exe).
Don't change the default directory of blueCFD!

## Credits and acknowledgements
Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.
<br> All Right Reserved.
<br> For collaboration, Please contact:
<br> linbr@mails.tsinghua.edu.cn
<br> If you have any technical problems, Please reach to:
<br> junx026@gmail.com

