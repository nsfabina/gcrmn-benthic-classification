import functools

import pyproj
import shapely.geometry
import shapely.ops


EPSG_DEST = 3857


def reproject_geometry(
        geometry: shapely.geometry.base.BaseGeometry,
        epsg_src: int,
        epsg_dest: int
) -> shapely.geometry.base.BaseGeometry:
    return shapely.ops.transform(
        functools.partial(
            pyproj.transform,
            pyproj.Proj(init='EPSG:{}'.format(epsg_src)),
            pyproj.Proj(init='EPSG:{}'.format(epsg_dest)),
        ),
        geometry
    )

