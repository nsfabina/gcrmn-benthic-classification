import os
import re

import gdal

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def remove_feature_rasters_alpha_band() -> None:
    raise AssertionError('This script has not been tested since being updated, be careful')
    _logger.info('Remove alpha band from feature rasters')
    filenames_raw = [filename for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW) if filename.endswith('features.tif')]
    for idx, filename_raw in enumerate(filenames_raw):
        _logger.debug('Removing alpha band for raster {} ({} total):  {}'.format(idx, len(filenames_raw), filename_raw))
        filepath_raw = os.path.join(paths.DIR_DATA_TRAIN_RAW, filename_raw)
        filepath_tmp = os.path.join(paths.DIR_DATA_TRAIN_RAW, re.sub('features.tif', 'features_tmp.tif', filename_raw))
        filepath_clean = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename_raw)
        # Write in nodata values
        command = 'gdal_calc.py -A {filepath_raw} --allBands=A -B {filepath_raw} --B_band=4 ' + \
                  '--outfile={filepath_tmp} --NoDataValue=-9999 --type=Int16 --co=COMPRESS=DEFLATE ' + \
                  '--co=TILED=YES --overwrite --calc="A * (B == 255) + -9999 * (B == 0)"'
        command = command.format(filepath_raw=filepath_raw, filepath_tmp=filepath_tmp)
        gdal_command_line.run_gdal_command(command, _logger)
        # Remove alpha band
        options_removed = gdal.TranslateOptions(
            bandList=[1, 2, 3], outputType=gdal.GDT_Int16, creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'])
        gdal.Translate(filepath_clean, filepath_tmp, options=options_removed)
        os.remove(filepath_tmp)


if __name__ == '__main__':
    remove_feature_rasters_alpha_band()
