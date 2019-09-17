import logging
import os
import sys

import gdal


_logger = logging.getLogger(__name__)
_logger.setLevel('DEBUG')
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.FileHandler('compress_feature_rasters.log')
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)


DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data/clean'


def compress_feature_rasters() -> None:
    _logger.info('Compress feature rasters')
    filepaths_features = [os.path.join(DIR_DATA, filename) for filename in os.listdir(DIR_DATA)
                          if filename.endswith('features.tif')]
    for idx_filepath, filepath in enumerate(filepaths_features):
        _logger.debug('Compressing feature raster {} of {}:  {}'.format(
            1+idx_filepath, len(filepaths_features), filepath))
        options_translate = gdal.TranslateOptions(creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
        gdal.Translate(filepath, filepath, options=options_translate)


if __name__ == '__main__':
    compress_feature_rasters()
