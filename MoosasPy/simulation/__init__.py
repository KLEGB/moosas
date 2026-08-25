"""Building-performance simulation modules."""

from importlib import import_module

__all__ = [
	"airflow",
	"CommandError",
	"CommandResult",
	"CommandTimeoutError",
	"coupling",
	"energy",
	"radiation",
	"Runner",
	"SimulationResult",
	"weather",
]

_EXPORTS = {
	"airflow": (".airflow", None),
	"CommandError": (".runner", "CommandError"),
	"CommandResult": (".runner", "CommandResult"),
	"CommandTimeoutError": (".runner", "CommandTimeoutError"),
	"coupling": (".coupling", None),
	"energy": (".energy", None),
	"radiation": (".radiation", None),
	"Runner": (".runner", "Runner"),
	"SimulationResult": (".contracts", "SimulationResult"),
	"weather": (".weather", None),
}


def __getattr__(name: str):
	"""Load simulation domains and shared contracts on demand."""
	try:
		module_name, attribute_name = _EXPORTS[name]
	except KeyError as error:
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error

	module = import_module(module_name, __name__)
	value = module if attribute_name is None else getattr(module, attribute_name)
	globals()[name] = value
	return value