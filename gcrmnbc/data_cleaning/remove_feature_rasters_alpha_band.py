import os
import re

import gdal
from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def remove_feature_rasters_alpha_band() -> None:
    filenames_raw = [fn for fn in os.listdir(paths.DIR_DATA_TRAIN_FEATURES_RAW) if fn.endswith('features.tif')]
    for filename_raw in tqdm(filenames_raw, desc='Remove feature rasters alpha band'):
        filepath_lock = os.path.join(paths.DIR_DATA_TRAIN_FEATURES_RAW, filename_raw + '.lock')
        filepath_raw = os.path.join(paths.DIR_DATA_TRAIN_FEATURES_RAW, filename_raw)
        filename_tmp = re.sub('features.tif', 'features_tmp.tif', filename_raw)
        filepath_tmp = os.path.join(paths.DIR_DATA_TRAIN_FEATURES_RAW, filename_tmp)
        filepath_clean = os.path.join(paths.DIR_DATA_TRAIN_FEATURES_CLEAN, filename_raw)
        # Skip if output file already exists or if lock file exists
        if os.path.exists(filepath_clean) or os.path.exists(filepath_lock):
            continue
        try:
            file_lock = open(filepath_lock, 'x')
        except OSError:
            continue

        try:
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
        except Exception as error_:
            raise error_
        finally:
            if os.path.exists(filepath_tmp):
                os.remove(filepath_tmp)
            file_lock.close()
            os.remove(filepath_lock)


if __name__ == '__main__':
    remove_feature_rasters_alpha_band()
