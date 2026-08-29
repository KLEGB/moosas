"""Geometry-source readers used exclusively by the transform pipeline."""

from .geo import _readGeo
from .obj import _readObj
from .stl import _readStl

__all__ = ["_readGeo", "_readObj", "_readStl"]
