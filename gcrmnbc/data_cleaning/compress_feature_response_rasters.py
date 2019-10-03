import os
import shutil

import gdal

from gcrmnbc.utils import logs, paths


_logger = logs.get_logger(__file__)


def compress_feature_response_rasters() -> None:
    raise AssertionError('This script has not been tested since being updated, be careful')
    _logger.info('Compress rasters')
    filepaths_rasters = [
        os.path.join(paths.DIR_DATA_TRAIN_CLEAN, fn) for fn in os.listdir(paths.DIR_DATA_TRAIN_CLEAN)
        if fn.endswith('.tif')
    ]
    filepath_tmp = os.path.join(paths.DIR_DATA_TRAIN_RAW, 'tmp_compress.tif')
    for idx_filepath, filepath_clean in enumerate(filepaths_rasters):
        _logger.debug('Compressing raster {} of {}:  {}'.format(
            1+idx_filepath, len(filepaths_rasters), filepath_clean))
        options_translate = gdal.TranslateOptions(creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
        gdal.Translate(filepath_tmp, filepath_clean, options=options_translate)
        shutil.copy(filepath_tmp, filepath_clean)
        os.remove(filepath_tmp)


if __name__ == '__main__':
    compress_feature_response_rasters()
