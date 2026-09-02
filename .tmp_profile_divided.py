from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from time import perf_counter

from MoosasPy.model.resources import configure_model_resources
from MoosasPy.transform.pipeline import _load_geometry_source
from MoosasPy.transform.stages.assembly import assemble_model
from MoosasPy.transform.stages.classification import classify_model
from MoosasPy.transform.stages.cleansing import cleanse_model
from MoosasPy.transform.stages.convexification import convexify_model
from MoosasPy.transform.stages.finalization import finalize_model
from MoosasPy.transform.stages.generation import CCRSpaceGeneration
from MoosasPy.transform.stages.splitting import split_wall_intersections
from MoosasPy.utils import np


path = str(Path(sys.argv[1]).resolve())
model = _load_geometry_source(path, "geo")
configure_model_resources(model)


def run(name, function):
    start = perf_counter()
    with redirect_stdout(StringIO()):
        result = function()
    print(name, round(perf_counter() - start, 3), flush=True)
    return result


model = run("classify-1", lambda: classify_model(model, True, True))
model.faceList = np.array(model.faceList)
model.wallList = np.array(model.wallList)
model.glazingList = np.array(model.glazingList)
model, _ = run(
    "cleanse-1",
    lambda: cleanse_model(
        model,
        solve_duplicated=True,
        solve_redundant=True,
        solve_overlap=True,
    ),
)
model = run("split-1", lambda: split_wall_intersections(model, True))
model = run("convexify", lambda: convexify_model(model))
model = run("classify-2", lambda: classify_model(model, True, True))
model.faceList = np.array(model.faceList)
model.wallList = np.array(model.wallList)
model.glazingList = np.array(model.glazingList)
model, _ = run(
    "cleanse-2",
    lambda: cleanse_model(
        model,
        solve_duplicated=True,
        solve_redundant=True,
        solve_overlap=True,
    ),
)
model = run("split-2", lambda: split_wall_intersections(model, True))
model = run("generation", lambda: CCRSpaceGeneration(model))
model = run("assembly", lambda: assemble_model(model, divided_zones=True, solve_overlap=True))
model = run(
    "finalization",
    lambda: finalize_model(
        model,
        break_wall_vertical=True,
        attach_shading=False,
        standardize=False,
    ),
)
print("result", len(model.spaceList), len(model.wallList), flush=True)
