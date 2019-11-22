from collections import OrderedDict
import functools
import os

import fiona
import fiona.crs
import pyproj
import shapely.geometry
import shapely.ops

from gcrmnbc.utils import EPSG_DEST
from gcrmnbc.utils import logs, paths


_logger = logs.get_logger(__file__)

PATH_REEF_FEATURES = 'clean/reef_outline.shp'
PATH_REEF_MULTIPOLY = 'clean/reef_outline_union.shp'

SHAPEFILE_DRIVER = 'ESRI Shapefile'
SHAPEFILE_SCHEMA = {'geometry': 'Polygon', 'properties': OrderedDict([('class_code', 'int')])}


def create_evaluation_reef_multipolygons() -> None:
    raise AssertionError('This script has not been tested since being updated, be careful')
    _logger.info('Create UQ reef multipolygons for model evaluation')
    dirs_reefs = sorted(os.listdir(paths.DIR_DATA_EVAL))
    crs = fiona.crs.from_epsg(EPSG_DEST)
    for dir_reef in dirs_reefs:
        _logger.debug('Create multipolygon for reef {}'.format(dir_reef))
        filepath_out = os.path.join(paths.DIR_DATA_EVAL, dir_reef, PATH_REEF_MULTIPOLY)
        if os.path.exists(filepath_out):
            _logger.debug('Multipolygon already exists at {}, skipping'.format(filepath_out))
        features = fiona.open(os.path.join(paths.DIR_DATA_EVAL, dir_reef, PATH_REEF_FEATURES))
        reef_4326 = shapely.ops.unary_union([shapely.geometry.shape(feature['geometry']) for feature in features])
        reef_new = _reproject_geometry(reef_4326)
        _logger.debug('Writing multipolygon to file at {}'.format(filepath_out))
        with fiona.open(filepath_out, 'w', driver=SHAPEFILE_DRIVER, crs=crs, schema=SHAPEFILE_SCHEMA) as file_:
            file_.write({'geometry': shapely.geometry.mapping(reef_new), 'properties': {'class_code': 1}})


def _reproject_geometry(geometry: shapely.geometry.base.BaseGeometry) -> shapely.geometry.base.BaseGeometry:
    return shapely.ops.transform(
        functools.partial(
            pyproj.transform,
            pyproj.Proj(init='EPSG:4326'),
            pyproj.Proj(init='EPSG:{epsg}'.format(EPSG_DEST)),
        ),
        geometry
    )


if __name__ == '__main__':
    create_evaluation_reef_multipolygons()
