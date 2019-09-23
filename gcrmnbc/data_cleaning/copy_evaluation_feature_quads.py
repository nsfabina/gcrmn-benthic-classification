import os
import shutil

import fiona
import gdal
import shapely.geometry

from gcrmnbc.utils import logs, mosaic_quads


_logger = logs.get_logger(__file__)

DIR_TRAINING_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data/clean'
DIR_EVAL_DATA = '/scratch/nfabina/gcrmn-benthic-classification/evaluation_data'
PATH_REEF_MULTIPOLY = 'clean/reef_outline_union.shp'
PATH_REEF_VRT = 'features.vrt'


def copy_evaluation_reef_quads() -> None:
    _logger.info('Copying evaluation quads')
    dirs_reefs = sorted(os.listdir(DIR_EVAL_DATA))
    for dir_reef in dirs_reefs:
        _logger.debug('Copying evaluation quads for reef {}'.format(dir_reef))
        feature = next(iter(fiona.open(os.path.join(DIR_EVAL_DATA, dir_reef, PATH_REEF_MULTIPOLY))))
        geometry = shapely.geometry.shape(feature['geometry'])
        quads_needed = mosaic_quads.determine_mosaic_quads_for_geometry(geometry)
        _logger.debug('Quads needed:  {}'.format(quads_needed))
        vrt_srcs = list()
        for quad in quads_needed:
            filename_quad = quad + '_features.tif'
            filepath_src = os.path.join(DIR_TRAINING_DATA, filename_quad)
            if not os.path.exists(filepath_src):
                continue
            filepath_dest = os.path.join(DIR_EVAL_DATA, dir_reef, filename_quad)
            shutil.copy(filepath_src, filepath_dest)
            vrt_srcs.append(filepath_dest)
        filepath_vrt = os.path.join(DIR_EVAL_DATA, dir_reef, PATH_REEF_VRT)
        gdal.BuildVRT(filepath_vrt, vrt_srcs)


if __name__ == '__main__':
    copy_evaluation_reef_quads()
