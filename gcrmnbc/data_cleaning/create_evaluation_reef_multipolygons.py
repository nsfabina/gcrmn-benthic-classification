from collections import OrderedDict
import os

import fiona
import fiona.crs
import shapely.geometry
import shapely.ops

from gcrmnbc.utils import logs


_logger = logs.get_logger(__file__)

DIR_EVAL_DATA = '/scratch/nfabina/gcrmn-benthic-classification/evaluation_data'
PATH_REEF_FEATURES = 'clean/reef_outline.shp'
PATH_REEF_MULTIPOLY = 'clean/reef_outline_union.shp'

SHAPEFILE_DRIVER = 'ESRI Shapefile'
SHAPEFILE_EPSG = 3857
SHAPEFILE_SCHEMA = {'geometry': 'Polygon', 'properties': OrderedDict([('class_code', 'int')])}


def create_uq_reef_multipolygons_for_model_evaluation() -> None:
    _logger.info('Create UQ reef multipolygons for model evaluation')
    dirs_reefs = sorted(os.listdir(DIR_EVAL_DATA))
    crs = fiona.crs.from_epsg(3857)
    for dir_reef in dirs_reefs:
        _logger.debug('Create multipolygon for reef {}'.format(dir_reef))
        filepath_out = os.path.join(DIR_EVAL_DATA, dir_reef, PATH_REEF_MULTIPOLY)
        if os.path.exists(filepath_out):
            _logger.debug('Multipolygon already exists at {}, skipping'.format(filepath_out))
        features = fiona.open(os.path.join(DIR_EVAL_DATA, dir_reef, PATH_REEF_FEATURES))
        reef = shapely.ops.unary_union([shapely.geometry.shape(feature['geometry']) for feature in features])
        _logger.debug('Writing multipolygon to file at {}'.format(filepath_out))
        with fiona.open(filepath_out, 'w', driver=SHAPEFILE_DRIVER, crs=crs, schema=SHAPEFILE_SCHEMA) as file_:
            file_.write({'geometry': shapely.geometry.mapping(reef), 'properties': {'class_code': 1}})


if __name__ == '__main__':
    create_uq_reef_multipolygons_for_model_evaluation()
