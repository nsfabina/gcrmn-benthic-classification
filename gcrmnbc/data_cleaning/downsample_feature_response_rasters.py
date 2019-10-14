import os
import re

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)

_DOWNSAMPLE_PCTS = (50, )
_DIR_OUT = 'downsample_{}'


def downsample_rasters() -> None:
    _logger.info('Downsample rasters')
    for pct in _DOWNSAMPLE_PCTS:
        dir_out = os.path.join(paths.DIR_DATA_TRAIN, _DIR_OUT.format(pct))
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)

    filenames = sorted([filename for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN) if filename.endswith('.tif')])

    for filename in tqdm(filenames, desc='Downsampling rasters'):
        filepath_in = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename)
        is_features = filename.endswith('features.tif')
        is_responses = re.search('responses', filename) or filename.endswith('model_class.tif') \
                       or filename.endswith('land.tif') or filename.endswith('water.tif')
        assert is_features or is_responses, 'Unknown file type:  {}'.format(filename)
        resampling = 'bilinear' if is_features else 'nearest'
        for pct in _DOWNSAMPLE_PCTS:
            filepath_out = os.path.join(paths.DIR_DATA_TRAIN, _DIR_OUT.format(pct), filename)
            if os.path.exists(filepath_out):
                continue
            command = 'gdal_translate -outsize {pct}% {pct}% -r {resampling} {path_in} {path_out}'.format(
                pct=pct, resampling=resampling, path_in=filepath_in, path_out=filepath_out)
            gdal_command_line.run_gdal_command(command, _logger)


if __name__ == '__main__':
    downsample_rasters()
