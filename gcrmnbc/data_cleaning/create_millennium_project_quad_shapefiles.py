from collections import OrderedDict
import os
from typing import List

import fiona.crs
from tqdm import tqdm

from gcrmnbc.utils import encodings_mp, logs, mosaic_quads, paths


_logger = logs.get_logger(__file__)


FILEPATH_QUAD_POLY = os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, '{}_responses.shp')
FILEPATH_QUAD_RASTER = os.path.join(paths.DIR_DATA_TRAIN_CLEAN_MP, '{}_responses.tif')

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

    def __init__(self) -> None:
        self._features_by_quad = dict()
        self._last_updated_by_quad = dict()

    def add_feature_to_quad(self, feature, quad, idx_feature) -> None:
        self._features_by_quad.setdefault(quad, list()).append(feature)
        self._last_updated_by_quad[quad] = idx_feature

    def write_quad_shapefiles(self, idx_feature, force_write=None) -> None:
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


def create_millennium_project_quad_rasters() -> None:
    _logger.info('Create Millennium Project response quads')
    _create_quad_shapefiles()
    _create_quad_rasters()


def _create_quad_shapefiles() -> None:
    filepaths_raw_polys = [
        os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, filename) for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW_MP)
        if filename.endswith('.shp') and not filename.endswith('responses.shp')
    ]
    quad_features = QuadFeatures()
    for idx_feature, filepath_raw in tqdm(enumerate(filepaths_raw_polys)):
        features = fiona.open(filepath_raw)
        for feature in features:
            feature = _fix_feature_code_collisions(feature)
            quads = mosaic_quads.determine_mosaic_quads_for_geometry(feature['geometry'])
            assert quads, 'No quads found for feature {} in file {}'.format(idx_feature, filepath_raw)
            for quad in quads:
                quad_features.add_feature_to_quad(feature, quad, idx_feature)
                quad_features.write_quad_shapefiles(idx_feature, force_write=False)
    quad_features.write_quad_shapefiles(idx_feature, force_write=True)
    remaining_features = sum([len(f) for f in quad_features._features_by_quad.values()])
    assert not remaining_features, 'Found {} remaining features'.format(remaining_features)


def _fix_feature_code_collisions(feature: dict) -> dict:
    code_collision = 2
    attr_collided = 'bay exposed fringing'
    code = feature['properties']['L4_CODE']
    attr = feature['properties']['L4_ATTRIB']
    if code == code_collision and attr == attr_collided:
        new_code = [v for k, v in encodings_mp.MAPPINGS_L4.items() if k == attr_collided][0]
        feature['properties']['L4_CODE'] = new_code
    return feature


def _write_features_to_quad_shapefile(features: List[dict], quad: str) -> None:
    # Get response quad filepath and determine whether we're writing a new file or appending to an existing file
    filepath = FILEPATH_QUAD_POLY.format(quad)
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))
    if os.path.exists(filepath):
        _logger.debug('Append to existing shapefile at {}'.format(filepath))
        with fiona.open(filepath, 'a') as file_:
            for feature in features:
                file_.write(feature)
    else:
        _logger.debug('Create new shapefile at {}'.format(filepath))
        crs = fiona.crs.from_epsg(SHAPEFILE_EPSG)
        with fiona.open(filepath, 'w', driver=SHAPEFILE_DRIVER, crs=crs, schema=SHAPEFILE_SCHEMA) as file_:
            for feature in features:
                file_.write(feature)


if __name__ == '__main__':
    create_millennium_project_quad_rasters()
