from typing import List

import numpy as np
import rasterio as rio
from rasterio.features import geometry_mask
import shapely.geometry


MOSAIC_LEVEL = 15
MOSAIC_TILE_SIZE = 4096
WEBM_EARTH_RADIUS = 6378137.0
WEBM_ORIGIN = -np.pi * WEBM_EARTH_RADIUS


def determine_mosaic_quads_for_geometry(geometry: dict) -> List[str]:
    # Parameters
    width = MOSAIC_TILE_SIZE * 2 * abs(WEBM_ORIGIN) / (2**MOSAIC_LEVEL * 256)
    num_tiles = int(2.0**MOSAIC_LEVEL * 256 / MOSAIC_TILE_SIZE)
    # Generate a grid where values are True if the geometry is present and False otherwise
    transform = rio.transform.from_origin(WEBM_ORIGIN, -WEBM_ORIGIN, width, width)
    shape = shapely.geometry.shape(geometry)
    grid = np.flipud(geometry_mask([shape], (num_tiles, num_tiles), transform, all_touched=True, invert=True))
    # Get quad labels
    quads = list()
    norths, easts = np.where(grid)
    for north, east in zip(norths, easts):
        quads.append('L15-{:04d}E-{:04d}N'.format(east, north))
    return quads
