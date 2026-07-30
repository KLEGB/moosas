# MoosasRad

`MoosasRad` is a command-line ray-to-geometry intersection engine used by MOOSAS radiation workflows.

The executable reads:

- one geometry file (`.geo`) describing the test meshes;
- one ray file (`.i`) describing ray origins and directions;
- and writes one output file (`.o`) containing one result line for each input ray.

## Command Line

```bash
MoosasRad.exe -g geometry.geo -o result.o input.i
```

Options:

- `-h` / `-help`: print help text
- `-g` / `-geo`: geometry input file
- `-o` / `-output`: output file path

The final positional argument is the ray input file.

## Ray Input File

The ray file is plain text. Each non-empty line defines one ray:

```text
origin_x,origin_y,origin_z,dir_x,dir_y,dir_z
```

Rules:

- values are comma-separated floats;
- one ray per line;
- direction is normalized by the engine when loaded.

Example:

```text
0.50,1.20,3.00,0.00,1.00,0.20
5.00,2.00,1.50,-0.40,0.80,0.45
```

## Geometry Input File

The geometry file uses MOOSAS `.geo`-style face blocks separated by `;`.

Relevant records used by `MoosasRad`:

- `fn,nx,ny,nz`: face normal
- `fv,x,y,z`: face vertex

Example:

```text
f,0,FaceA
fn,0,1,0
fv,0,0,0
fv,10,0,0
fv,10,0,3
fv,0,0,3
fv,0,0,0
;
```

Engine expectations:

- each face block must contain one `fn` line and at least one closed vertex loop;
- the engine treats each block as one polygon face;
- only the outer loop is read by the current implementation;
- holes are not parsed.

## Output File

The output file is plain text with one line per input ray:

```text
hit_x,hit_y,hit_z,reflected_dir_x,reflected_dir_y,reflected_dir_z
```

If a ray does not hit any face, the engine writes:

```text
-1.00,-1.00,-1.00,-1.00,-1.00,-1.00
```

This sentinel means "no intersection".

## Semantics

For each input ray, `MoosasRad`:

1. tests the ray against the provided faces;
2. returns the first valid intersection found by the current scan order;
3. computes and outputs the reflected ray at that hit point.

The current executable is used by MOOSAS as a fast batched ray-hit test. In many workflows, callers only need to distinguish:

- hit: output origin is not `(-1,-1,-1)`
- miss: output origin is `(-1,-1,-1)`

## Notes

- face iteration order affects which hit is returned when multiple faces are intersected;
- output values are formatted to two decimal places by the current Go implementation;
- the current implementation reads regular files only and does not define a streaming API.
