from ...utils import shapely
from datetime import datetime
from ...transformation.geometry import Projection


def _meshToRadObject(geos, material, id):
    """
    Convert a mesh geometry to a Radiance object string representation.
    
    Parameters
    ----------
    geos : shapely.Geometry or list of shapely.Geometry
        Input geometry or list of geometries to convert.
    material : str
        Material name to assign to the Radiance object.
    id : str
        Identifier prefix for the generated polygons.
    
    Returns
    -------
    str
        Radiance-formatted string representation of the mesh geometry, including material,
        polygon identifiers, and vertex coordinates. Returns an empty string if no valid
        triangles are generated.
    """
    if isinstance(geos, shapely.Geometry):
        geos = [geos]
    geoStr = []
    for gid,geo in enumerate(geos):
        try:
            proj = Projection.fromPolygon(geo)
        except IndexError as e:
            print("******Warning: GeometryError, invalid projection while writing rad")
            continue
        try:
            geoUV = proj.toUV(geo)
            triangles = shapely.delaunay_triangles(geoUV)
            triangles = [proj.toWorld(tri) for tri in shapely.get_parts(triangles)]
            if len(triangles) == 0:
                return ""
            for trIdx, tri in enumerate(triangles):
                pts = shapely.get_coordinates(tri, include_z=True)
                geoStr += [f"{material} polygon {id}_{gid}_{trIdx} 0 0 {(len(pts)-1) * 3}"]
                for pt in pts[:-1]:
                    geoStr += ["    "+" ".join(pt.astype(str))]
                geoStr += [""]
            return "\n".join(geoStr)+"\n"
        except Exception as e:
            print("GeometryError:",e)
    return "\n".join(geoStr) + "\n"


def _materialLib():
    """
    Return a string containing Radiance material definitions for common building materials.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    str
        A string defining materials (plastic and glass) in Radiance format, including default_floor,
        default_roof, default_wall with specified reflectances, and a base glazing material.
    """
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
    """
    Generate a Radiance sky description string for a given date and location.
    
    Parameters
    ----------
    date : datetime
        The date and time for which the sky is generated, used to determine month, day, and hour.
    skyType : str
        Type of sky model to generate (e.g., "-c" for cloudy, other values for different sky types).
    lat : float or str
        Latitude of the location in degrees, used in the sky generation command.
    lon : float or str
        Longitude of the location in degrees, used in the sky generation command.
    diff : float, optional
        Diffuse solar irradiance value (in W/m虏). Used only if skyType is "-c". Default is 10000.
    
    Returns
    -------
    str
        A formatted string containing the Radiance sky definition commands, including gensky command
        and associated glow and source elements for sky and ground.
    """
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
