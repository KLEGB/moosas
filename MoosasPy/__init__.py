"""MoosasPy building geometry and performance-analysis toolkit."""

from importlib import import_module

from ._version import __version__

__all__ = [
	"__version__",
	"airflow",
	"energyAnalysis",
	"includeEpw",
	"load_model",
	"model_from_file",
	"positionRadiation",
	"positionSunHour",
	"save_model",
	"spaceGen",
	"transform",
	"utils",
	"weather",
]

_EXPORTS = {
	"utils": (".utils", None),
	"weather": (".simulation.weather", None),
	"airflow": (".simulation.airflow", None),
	"transform": (".transform", "transform"),
	"load_model": (".transform", "load_model"),
	"model_from_file": (".transform", "model_from_file"),
	"save_model": (".transform", "save_model"),
	"energyAnalysis": (".simulation.energy", "energyAnalysis"),
	"positionRadiation": (".simulation.radiation", "positionRadiation"),
	"positionSunHour": (".simulation.radiation", "positionSunHour"),
	"spaceGen": (".transform.geometry", "spaceGen"),
	"includeEpw": (".simulation.weather", "includeEpw"),
}


def __getattr__(name: str):
	"""Load public modules and functions only when they are requested."""
	try:
		module_name, attribute_name = _EXPORTS[name]
	except KeyError as error:
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error

	module = import_module(module_name, __name__)
	value = module if attribute_name is None else getattr(module, attribute_name)
	globals()[name] = value
	return value
