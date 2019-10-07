import os

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


_DOWNSAMPLE_PCT = 50
_FILENAME_PREFIX = 'down{}'.format(_DOWNSAMPLE_PCT)


def downsample_global_rasters() -> None:
    _logger.info('Downsample rasters')
    filenames = sorted([fn for fn in os.listdir(paths.DIR_DATA_GLOBAL) 
                        if not fn.startswith(_FILENAME_PREFIX) and fn.endswith('.tif')])

    for filename in tqdm(filenames, desc='Downsampling rasters'):
        filepath_in = os.path.join(paths.DIR_DATA_GLOBAL, filename)
        filepath_out = os.path.join(paths.DIR_DATA_GLOBAL, _FILENAME_PREFIX + filename)
        command = 'gdal_translate -outsize {pct}% {pct}% -r bilinear {path_in} {path_out}'.format(
            pct=_DOWNSAMPLE_PCT, path_in=filepath_in, path_out=filepath_out)
        gdal_command_line.run_gdal_command(command, _logger)
        os.remove(filepath_in)


if __name__ == '__main__':
    downsample_global_rasters()
