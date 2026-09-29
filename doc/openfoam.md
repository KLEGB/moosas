# OpenFOAM volume mesh export

`MoosasPy.model.io.export_openfoam` turns one existing `MoosasGrid` into a
three-dimensional, constant-section prism mesh. It writes an ASCII OpenFOAM
`polyMesh` directly; exporting does not require OpenFOAM or a meshing executable.

```python
from MoosasPy.model.io import export_openfoam
from MoosasPy.transform.geometry.grid import MoosasGrid

# Select a single planar face representing the complete intended footprint.
# If a room has several floor faces, selecting its first face alone will NOT
# represent the whole room. Merge/prepare the intended footprint first.
grid = MoosasGrid(floor_face, gird_size=0.5, grid_offset=0.78)
result = export_openfoam(
    grid,
    "cases/room",
    height=3.0,
    layers=12,
    base_offset=0.0,
    patch_types={"bottom": "wall", "top": "wall", "walls": "wall"},
)
```

## Parameters and output

| Parameter | Meaning |
| --- | --- |
| `grid` | Existing `MoosasGrid` built from one planar source geometry |
| `case_dir` | OpenFOAM case directory; mesh is written under `constant/polyMesh` |
| `height` | Required positive extrusion distance along projected local +Z |
| `layers` | Positive integer number of equal-height layers, default `1` |
| `base_offset` | Signed local Z displacement from the source face, default `0` |
| `patch_types` | Optional types for `bottom`, `top`, `walls`; defaults to `wall` |

`SaveResult.primary_path` is the `polyMesh` directory. `generated_paths` contains
the five mesh files plus the mapping JSON:

```text
constant/
  polyMesh/
    points
    faces
    owner
    neighbour
    boundary
  moosasGrid.json
```

Internal faces come first, with normals pointing from owner to neighbour and
`owner < neighbour`. `neighbour` contains only internal-face entries. Boundary
faces follow in contiguous `bottom`, `top`, `walls` groups, with outward normals.
The exporter follows the existing `Projection.toWorld` coordinates and corrects
face winding when that projection uses a left-handed frame.

The volume starts at local `base_offset`, not `grid.gridOffset`. Thus a floor at
world elevation 10 m, with `grid_offset=0.78`, `base_offset=0`, and `height=3`,
produces a volume from 10 to 13 m for an upward local Z axis. Sampling points
remain at 10.78 m. For inclined or vertical source faces, inspect the grid's
local Z direction; extrusion is not necessarily world-up. All dimensions retain
the source units; prepare coordinates in metres for OpenFOAM.

## Alignment with MoosasGrid

The exporter uses the same UV cell centres and `gridSize`, clips each square
against `UVFace`, then extrudes it. Full interior cells therefore share the
sampling grid's horizontal centres. Boundary-cell centroids generally differ
after clipping. Concave or holed intersections are divided into convex columns;
shared edges are split consistently so neighbouring cells share complete faces.

`MoosasGrid` excludes samples on/outside the footprint boundary. A solver mesh
must still cover that part of the volume: the exporter includes those columns
and, when needed, adds columns beyond the original grid array. It does not
change the source grid, its mask, sampling points, or cached cell polygons.

`constant/moosasGrid.json` contains:

- `grid_shape`, `grid_size`, `grid_offset`: the original grid dimensions/settings.
- `sample_points`: world XYZ coordinates in exactly `grid.gridPoints` order.
- `layer_bounds`: layer interfaces measured in local Z relative to the source plane.
- `cells`: one entry per OpenFOAM cell, in cell-label order.

Each cell entry includes `cell`, `layer` (zero-based), `lattice_index` (row,
column), `grid_index` (original row, column or `null` for an added column), and
`sample_index` (index into valid `grid.gridPoints`, or `null` when no valid sample
exists). Multiple layers and split columns can reference the same grid index.
This is a correspondence map, not an interpolation of CFD values onto samples;
use layer selection and volume-weighted aggregation or OpenFOAM sampling when
reading results.

## Boundaries and supported domains

`bottom` and `top` are the first/last extrusion planes. `walls` includes all
outer perimeter faces and hole walls. Accepted types are `wall`, `patch`,
`symmetry`, and (for bottom/top only) `symmetryPlane`. These are mesh patch types,
not field boundary conditions. For example, making `top` a `patch` does not set
its velocity or pressure. Periodic/coupled patches and two-dimensional `empty`
patches are not supported by this three-dimensional exporter.

The input must describe the complete intended constant-section fluid region.
This function does not infer a complete building domain from a model, connect
separate rooms, resolve glazing/openings, mesh internal objects, or fit sloped
ceilings. Fragmented source geometry is rejected because `MoosasGrid` otherwise
chooses only its largest polygon. Concave outlines and holes in `UVFace` are
supported. Grid construction projects rings separately to preserve source holes.

No solver files (`0/`, `controlDict`, `fvSchemes`, `fvSolution`) are generated.
Existing case setup files are preserved. A nonempty `constant/polyMesh` or an
existing mapping file raises `FileExistsError`; export to a fresh case directory.

## Validation

Run the local regression tests with:

```bash
python -m pytest test/test_openfoam_io.py -q
```

The tests independently parse the files and check cell closure, edge incidence,
positive cell volumes, total volume, boundary ranges, grid correspondence,
coordinate transforms, and invalid inputs. Where `checkMesh` is on PATH, the
optional integration test additionally invokes it on generated example meshes.

Before using a mesh for a simulation, supply the case dictionaries and run:

```bash
checkMesh -case cases/room -allTopology -allGeometry
```

Small clipped boundary cells can have poor aspect ratios or skewness. A valid
topology alone does not establish mesh quality or solution convergence; choose
grid spacing/layer count for the intended case and inspect `checkMesh` results.

Format references: [OpenFOAM mesh description](https://doc.cfd.direct/openfoam/user-guide-v13/mesh-description)
and [mesh files](https://doc.cfd.direct/openfoam/user-guide-v13/mesh-files).
