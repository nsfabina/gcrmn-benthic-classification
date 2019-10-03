import os
import shutil

import fiona
import gdal
import shapely.geometry

from gcrmnbc.utils import logs, mosaic_quads, paths


_logger = logs.get_logger(__file__)

PATH_REEF_MULTIPOLY = 'clean/reef_outline_union.shp'
PATH_REEF_VRT = 'features.vrt'


def copy_evaluation_reef_quads() -> None:
    _logger.info('Copying evaluation quads')
    dirs_reefs = sorted(os.listdir(paths.DIR_DATA_EVAL))
    dirs_data_variant = sorted(os.listdir(paths.DIR_DATA_TRAIN))
    for dir_reef in dirs_reefs:
        _logger.debug('Copying evaluation quads for reef {}'.format(dir_reef))
        feature = next(iter(fiona.open(os.path.join(paths.DIR_DATA_EVAL, dir_reef, PATH_REEF_MULTIPOLY))))
        geometry = shapely.geometry.shape(feature['geometry'])
        quads_needed = mosaic_quads.determine_mosaic_quads_for_geometry(geometry)
        _logger.debug('Quads needed:  {}'.format(quads_needed))
        vrt_srcs = list()
        for dir_variant in dirs_data_variant:
            if dir_variant == 'tmp':
                continue
            for quad in quads_needed:
                filename_quad = quad + '_features.tif'
                filepath_src = os.path.join(paths.DIR_DATA_TRAIN, dir_variant, filename_quad)
                if not os.path.exists(filepath_src):
                    continue
                filepath_dest = os.path.join(paths.DIR_DATA_EVAL, dir_reef, dir_variant, filename_quad)
                shutil.copy(filepath_src, filepath_dest)
                vrt_srcs.append(filepath_dest)
            filepath_vrt = os.path.join(paths.DIR_DATA_EVAL, dir_reef, dir_variant, PATH_REEF_VRT)
            gdal.BuildVRT(filepath_vrt, vrt_srcs)


if __name__ == '__main__':
    copy_evaluation_reef_quads()
