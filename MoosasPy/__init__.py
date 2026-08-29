"""MoosasPy building geometry and performance-analysis toolkit."""

from importlib import import_module

from ._version import __version__

__all__ = [
	"__version__",
	"MoosasModel",
	"TransformOptions",
	"simulation",
	"transform",
]

_EXPORTS = {
	"MoosasModel": (".model", "MoosasModel"),
	"TransformOptions": (".transform", "TransformOptions"),
	"transform": (".transform", None),
	"simulation": (".simulation", None),
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
