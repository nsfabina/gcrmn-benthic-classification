from collections import OrderedDict
import json
import os
import re
from typing import List

import fiona.crs
import numpy as np
import rasterio as rio
from rasterio.features import geometry_mask
import shapely.geometry

from gcrmnbc.utils import encodings, logs


_logger = logs.get_logger(__file__)

DIR_TRAINING_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data/'
FILEPATH_RESPONSE_SOURCE = os.path.join(DIR_TRAINING_DATA, 'raw/lwr_3857.geojson')
FILEPATH_RESPONSE_QUAD = os.path.join(DIR_TRAINING_DATA, 'tmp/{}_responses.shp')

SHAPEFILE_DRIVER = 'ESRI Shapefile'
SHAPEFILE_EPSG = 3857
SHAPEFILE_SCHEMA = {
    'geometry': 'Polygon',
    'properties': OrderedDict([
        ('class_code', 'int'),
    ])
}

WRITE_FEATURE_BUFFER = 1000
WRITE_IDX_BUFFER = 10000


class QuadFeatures(object):
    _features_by_quad = None
    _last_updated_by_quad = None

    def __init__(self):
        self._features_by_quad = dict()
        self._last_updated_by_quad = dict()

    def add_feature_to_quad(self, feature, quad, idx_feature):
        self._features_by_quad.setdefault(quad, list()).append(feature)
        self._last_updated_by_quad[quad] = idx_feature

    def write_quad_shapefiles(self, idx_feature, force_write=None):
        quads = sorted(list(self._features_by_quad.keys()))
        for quad in quads:
            features = self._features_by_quad[quad]
            last_updated = self._last_updated_by_quad[quad]
            too_many_features = len(features) > WRITE_FEATURE_BUFFER
            too_many_indexes = (idx_feature - last_updated) > WRITE_IDX_BUFFER
            if not force_write and not too_many_features and not too_many_indexes:
                continue
            _write_features_to_quad_shapefile(features, quad)
            self._features_by_quad.pop(quad)
            self._last_updated_by_quad.pop(quad)


def _raise() -> None:
    raise AssertionError(
        "So... you're running create_response_shapefile_quads again, huh? That's a bummer. You know this takes a " 
        "long time to run, right? Well, the reason I'm raising this error is because I want to remind you how long "
        "it takes to run AND to recommend that you write up something to parse the data more quickly. You should "
        "think about how to make this parsing work in parallel. First, you'll need to implement some sort of "
        "thread-safe generator for the raw geojson or divide the file up based on raw number of lines. Second, "
        "you'll need to be sure that only one thread opens a fiona file at a time (probably with the 'x' flag) "
        "and that other threads are patient when trying to access the same file. This'll be much easier than "
        "setting up multiple jobs to work in parallel and it's better because it'd be overkill to spin up multiple "
        "instances to just parse data from a file and write it to another file. Good luck! This should only take "
        "1-2 hours, so don't worry!"
    )


def create_response_quads() -> None:
    _raise()
    _logger.info('Create response quads')
    quad_features = QuadFeatures()
    idx_feature = 0
    for feature in _yield_features():
        idx_feature += 1
        _logger.debug('Processing feature {}'.format(idx_feature))
        quads = _determine_quads(feature['geometry'])
        if not quads:
            _logger.warning('No quads found for feature {}:  {}'.format(idx_feature, feature))
            continue
        for quad in quads:
            quad_features.add_feature_to_quad(feature, quad, idx_feature)
            quad_features.write_quad_shapefiles(idx_feature, force_write=False)
    quad_features.write_quad_shapefiles(idx_feature, force_write=True)
    remaining_features = sum([len(f) for f in quad_features._features_by_quad.values()])
    _logger.debug('Remaining features:  {}'.format(remaining_features))


def _yield_features() -> dict:
    # The geojson is enormous, so we step through each line looking for geometries
    with open(FILEPATH_RESPONSE_SOURCE) as file_:
        content = ''
        for idx_line, line in enumerate(file_):
            content += line
            # Determine whether the next content chunk includes a full geometry
            match = re.search(r'(?<="geometry": ){[^}]*}', content)
            if not match:
                continue
            # Confirm we did not miss a geometry in the preceding content chunk
            content_preceding_geometry = content[:match.start()]
            if re.match('"coordinates"', content_preceding_geometry):
                _logger.warning('Found "coordinates" in unused content chunk on or near line {}:  {}'.format(
                    idx_line, content_preceding_geometry))
            # Update the content chunk to include only content after the geometry
            content = content[1 + match.end():]
            # Parse the geometry and class and generate the feature
            geometry = json.loads(match.group())
            properties_match = re.search(r'{ "class_name[^}]*}', content_preceding_geometry)
            if not properties_match:
                _logger.warning('No properties found for geometry on or near line {}:  {}'.format(
                    idx_line, content_preceding_geometry))
                continue
            properties = json.loads(properties_match.group())
            class_code = encodings.MAPPINGS[properties['class_name']]
            feature = {
                'properties': OrderedDict([('class_code', class_code)]),
                'geometry': geometry,
            }
            yield feature


def _determine_quads(geometry: dict) -> List[str]:
    # Parameters
    MOSAIC_LEVEL = 15
    MOSAIC_TILE_SIZE = 4096
    WEBM_EARTH_RADIUS = 6378137.0
    WEBM_ORIGIN = -np.pi * WEBM_EARTH_RADIUS
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


def _write_features_to_quad_shapefile(features: List[dict], quad: str) -> None:
    # Get response quad filepath and determine whether we're writing a new file or appending to an existing file
    filepath = FILEPATH_RESPONSE_QUAD.format(quad)
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))
    if os.path.exists(filepath):
        _logger.debug('Append to existing shapefile at {}'.format(filepath))
        with fiona.open(filepath, 'a') as file_:
            for feature in features:
                file_.write(feature)
    else:
        _logger.debug('Create new shapefile at {}'.format(filepath))
        crs = fiona.crs.from_epsg(3857)
        with fiona.open(filepath, 'w', driver=SHAPEFILE_DRIVER, crs=crs, schema=SHAPEFILE_SCHEMA) as file_:
            for feature in features:
                file_.write(feature)


if __name__ == '__main__':
    create_response_quads()
