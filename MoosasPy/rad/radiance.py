from ..utils import pygeos
from datetime import datetime
from ..geometry import Projection


def _meshToRadObject(geo: pygeos.Geometry, material, id):
    try:
        proj = Projection.fromPolygon(geo)
        geoUV = proj.toUV(geo)
        triangles = pygeos.delaunay_triangles(geoUV)
        triangles = [proj.toWorld(tri) for tri in pygeos.get_parts(triangles)]

        if len(triangles) == 0:
            return ""
        geoStr = []
        for trIdx, tri in enumerate(triangles):
            pts = pygeos.get_coordinates(tri, include_z=True)
            geoStr += [f"{material} polygon {id}_{trIdx} 0 0 {(len(pts)-1) * 3}"]
            for pt in pts[:-1]:
                geoStr += ["    "+" ".join(pt.astype(str))]
            geoStr += [""]
        return "\n".join(geoStr)+"\n"
    except Exception as e:
        print(e)
        return ""


def _materialLib():
    """
            Visible Light Transmittance (VLT) : Tn
        =>    void glass sketch_win 0 0 3 tn tn tn
        =>    tn =  (Math.sqrt(0.8402528435+0.0072522239*Tn*Tn)-0.9166530661)/0.0036261119/Tn
        => VLT : 0.737, tn = 0.803
        => VLT : 0.803, tn = 0.874
        => VLT : 0.915, tn = 0.996
    """
    matStr = """
####Materials
void plastic default_floor
0
0
5 0.3 0.3 0.3 0 0
void plastic default_roof
0
0
5 0.75 0.75 0.75 0 0
void plastic default_wall
0
0
5 0.6 0.6 0.6 0 0
void glass glazing_
0
0
3 0.78 0.78 0.78

####Materials
"""
    return matStr


def _getSky(date: datetime, skyType, lat, lon, diff=10000):
    skyStr = f"!gensky {str(date.month).zfill(2)} {str(date.day).zfill(2)} {str(date.hour).zfill(2)} {skyType} -a {lat} -o {lon} -g 0.200"
    if skyType == "-c":
        skyStr += f" -B {diff / 179.0}"
    skyStr += "\n"
    skyStr += """skyfunc glow sky_mat
0
0
4
    1 1 1 0
sky_mat source sky
0
0
4
    0 0 1 180
skyfunc glow ground_glow
0
0
4
    1 .8 .5 0
ground_glow source ground
0
0
4
    0 0 -1 180"""
    return skyStr
