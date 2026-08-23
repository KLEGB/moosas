"""MoosasPy building geometry and performance-analysis toolkit."""

from ._version import __version__

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
from .rad import positionRadiation
from .sunhour import positionSunHour
from . import daylightFactor
from .geometry import spaceGen
from .weather import includeEpw

# initialize temp directory
from .utils import tools
try:
    tools.path.clean(tools.path.tempDir)
except Exception:
    # Temp cleanup should not block package import.
    pass
del tools
