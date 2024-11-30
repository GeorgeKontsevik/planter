from shapely.geometry import LineString

def flip_geometry(geom):
    if isinstance(geom, LineString):
        # Reverse the coordinates for LineString
        return LineString([(y, x) for x, y in geom.coords])

    return geom  # Return unchanged for other geometry types