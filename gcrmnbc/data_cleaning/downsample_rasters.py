import os
import re

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs


_logger = logs.get_logger(__file__)

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data'
DIR_DATA_CLEAN = os.path.join(DIR_DATA, 'clean')

_DOWNSAMPLE_PCTS = (50, 25)


def downsample_rasters() -> None:
    _logger.info('Downsample rasters')
    filenames = [filename for filename in os.listdir(DIR_DATA_CLEAN) if filename.endswith('.tif')]

    for filename in tqdm(filenames, desc='Downsampling rasters'):
        filepath_in = os.path.join(DIR_DATA_CLEAN, filename)
        resampling = 'bilinear' if re.search('features', filename) else 'nearest'

        for pct in _DOWNSAMPLE_PCTS:
            filepath_out = os.path.join(DIR_DATA, 'downsample_{}'.format(pct), filename)
            if not os.path.exists(os.path.dirname(filepath_out)):
                os.makedirs(os.path.dirname(filepath_out))

            command = 'gdal_translate -outsize {pct}% {pct}% -r {resampling} {path_in} {path_out}'.format(
                pct=pct, resampling=resampling, path_in=filepath_in, path_out=filepath_out)
            gdal_command_line.run_gdal_command(command, _logger)


if __name__ == '__main__':
    downsample_rasters()
