"""
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

Moosas+ is reform in ***python/golang/javascript***.
We kindly invite contributions to the python package MoosasPy for better performance.
- ***.\pythonDict:*** the python environment
  - ***.\pythonDict\MoosasPy:*** the MoosasPy package
- ***.\libs:*** the core execution for energy, radiation, and ventilation analysis
  - ***.\libs\energy:*** residential/public building energy analysis.
  - ***.\libs\vent:*** pressure based / buoyancy based ventilation analysis by contamX.
  - ***.\libs\rad:*** fast ray-face test module for radiation analysis.
- ***.\db:*** the database for building templates, materials and weather file.
- ***.\view:*** Moosas+ interface coded in html / javascript. currently is not functioned.
- ***.\data:*** Some of the input files and analysis result (like ventilation) can be found here
- ***.\temp:*** Files will be clean here when start moosas+ ro import MoosasPy.
"""

# subpackages
from . import geometry
from . import utils
from . import weather
from . import vent
from . import IO
from . import encoding

# simulation functions
from .transformation import transform,loadModel,saveModel
from .energy import energyAnalysis
from .ventilation import iterateProjects,contam_iteration
from .rad import positionRadiation
from .sunhour import positionSunHour
from . import daylightFactor
from .geometry import spaceGen

# initialize temp directory
from .utils import tools
tools.path.clean(tools.path.tempDir)
del tools
