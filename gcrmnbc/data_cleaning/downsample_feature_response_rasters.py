import argparse
import os
import re

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)

DOWNSAMPLE_PCTS = (25, 50)


def downsample_rasters() -> None:
    _logger.info('Downsample rasters')
    _logger.debug('Downsample features')
    _downsample_dir(paths.DIR_DATA_TRAIN_FEATURES_CLEAN)
    _logger.debug('Downsample MP responses')
    _downsample_dir(paths.DIR_DATA_TRAIN_MP_CLEAN)
    _logger.debug('Downsample MP supplemental responses')
    _downsample_dir(paths.DIR_DATA_TRAIN_MP_SUPP_CLEAN)


def _downsample_dir(dir_src: str) -> None:
    filenames_srcs = [fn for fn in os.listdir(dir_src) if fn.endswith('.tif')]
    for filename_src in tqdm(filenames_srcs, desc='Downsampling rasters'):
        filepath_src = os.path.join(dir_src, filename_src)
        filepath_lock = os.path.join(dir_src, filename_src + '.lock')
        try:
            file_lock = open(filepath_lock, 'x')
        except OSError:
            continue

        try:
            for pct in DOWNSAMPLE_PCTS:
                dir_dest = os.path.join(os.path.dirname(dir_src), paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format(pct))
                filename_dest = re.sub('.tif', '_{}.tif'.format(pct), filename_src)
                filepath_dest = os.path.join(dir_dest, filename_dest)
                if os.path.exists(filepath_dest):
                    continue
                if not os.path.exists(dir_dest):
                    try:
                        os.makedirs(dir_dest)
                    except:
                        pass
                command = 'gdal_translate -outsize {pct}% {pct}% -r nearest {filepath_src} {filepath_dest}'.format(
                    pct=pct, filepath_src=filepath_src, filepath_dest=filepath_dest)
                gdal_command_line.run_gdal_command(command, _logger)
        except Exception as error_:
            raise error_
        finally:
            file_lock.close()
            os.remove(filepath_lock)


if __name__ == '__main__':
    downsample_rasters()

