import os
import re

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


_DOWNSAMPLE_PCTS = (25, 50)


def downsample_global_rasters() -> None:
    _logger.info('Downsample rasters')
    filenames = sorted([fn for fn in os.listdir(paths.DIR_DATA_GLOBAL) if re.search('L15-\d{4}E-\d{4}N.tif', fn)])

    for filename in tqdm(filenames, desc='Downsampling rasters'):
        _logger.debug('Downsample raster: {}'.format(filename))
        filepath_in = os.path.join(paths.DIR_DATA_GLOBAL, filename)
        filepath_lock = filepath_in + '.lock'

        if os.path.exists(filepath_lock) or not os.path.exists(filepath_in) or os.path.exists(filepath_out):
            continue

        try:
            file_lock = open(filepath_lock, 'x')
        except OSError:
            continue

        try:
            for pct in _DOWNSAMPLE_PCTS:
                filename_out = re.sub('.tif', '_{}.tif'.format(pct), filename)
                dir_out = os.path.join(paths.DIR_DATA_GLOBAL, paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format(pct))
                filepath_out = os.path.join(dir_out, filename_out)
                if not os.path.exists(dir_out):
                    try:
                        os.makedirs(dir_out)
                    except OSError:
                        pass
                command = 'gdal_translate -outsize {pct}% {pct}% -r bilinear {path_in} {path_out}'.format(
                    pct=pct, path_in=filepath_in, path_out=filepath_out)
                gdal_command_line.run_gdal_command(command, _logger)
            os.remove(filepath_in)
        except Exception as error_:
            raise error_
        finally:
            file_lock.close()
            os.remove(filepath_lock)


if __name__ == '__main__':
    downsample_global_rasters()
