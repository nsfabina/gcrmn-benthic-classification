import os
import shutil

import gdal

from gcrmnbc.utils import logs


_logger = logs.get_logger(__file__)


DIR_BASE = '/scratch/nfabina/gcrmn-benthic-classification/training_data'
DIR_CLEAN = os.path.join(DIR_BASE, 'clean')
DIR_TMP = os.path.join(DIR_BASE, 'tmp')


def remove_feature_rasters_alpha_band() -> None:
    _logger.info('Remove alpha band from feature rasters')
    filepaths_features = [os.path.join(DIR_CLEAN, fn) for fn in os.listdir(DIR_CLEAN) if fn.endswith('features.tif')]
    filepath_tmp = os.path.join(DIR_TMP, 'tmp_alpha_removed.tif')
    for idx_filepath, filepath_clean in enumerate(filepaths_features):
        _logger.debug('Removing alpha band for raster {} ({} total):  {}'.format(
            idx_filepath, len(filepaths_features), filepath_clean))
        options_translate = gdal.TranslateOptions(bandList=[1, 2, 3], creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
        gdal.Translate(filepath_tmp, filepath_clean, options=options_translate)
        shutil.copy(filepath_tmp, filepath_clean)
        os.remove(filepath_tmp)


if __name__ == '__main__':
    remove_feature_rasters_alpha_band()
