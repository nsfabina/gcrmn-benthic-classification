import logging
import os
import sys

import gdal


_logger = logging.getLogger(__name__)
_logger.setLevel('DEBUG')
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.FileHandler(__name__ + '.log')
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)


DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data/clean'


def compress_feature_response_rasters() -> None:
    _logger.info('Compress feature rasters')
    filepaths_features = [os.path.join(DIR_DATA, fn) for fn in os.listdir(DIR_DATA) if fn.endswith('.tif')]
    for idx_filepath, filepath in enumerate(filepaths_features):
        _logger.debug('Compressing raster {} of {}:  {}'.format(
            1+idx_filepath, len(filepaths_features), filepath))
        options_translate = gdal.TranslateOptions(creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
        gdal.Translate(filepath, filepath, options=options_translate)


if __name__ == '__main__':
    compress_feature_response_rasters()
