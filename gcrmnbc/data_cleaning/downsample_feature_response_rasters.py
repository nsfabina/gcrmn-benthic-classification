import os
import re

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def downsample_rasters() -> None:
    _logger.info('Downsample rasters')
    dir_out = os.path.join(paths.DIR_DATA_TRAIN, 'downsample_50')
    dir_out_mp = os.path.join(paths.DIR_DATA_TRAIN, 'millennium_project_downsample_50')
    for dir_ in (dir_out, dir_out_mp):
        try:
            os.makedirs(dir_)
        except:
            pass

    filepaths = list()
    # Aggregate feature and UQ files
    for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN):
        if not filename.endswith('.tif'):
            continue
        filepath_in = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename)
        filepath_out = os.path.join(dir_out, filename)
        filepaths.append((filepath_in, filepath_out))
    # Aggregate MP files
    for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN_MP)[:10]:
        if not filename.endswith('L3_CODE.tif') or not filename.endswith('L4_CODE.tif'):
            continue
        filepath_in = os.path.join(paths.DIR_DATA_TRAIN_CLEAN_MP, filename)
        filepath_out = os.path.join(dir_out_mp, filename)
        filepaths.append((filepath_in, filepath_out))

    for filepath_in, filepath_out in tqdm(filepaths, desc='Downsampling rasters'):
        filepath_lock = filepath_in + '.lock'
        if os.path.exists(filepath_out) or os.path.exists(filepath_lock):
            continue
        try:
            file_lock = open(filepath_lock, 'x')
        except OSError:
            continue

        try:
            is_features = filepath_in.endswith('features.tif')
            response_suffixes = ('model_class.tif', 'land.tif', 'water.tif', 'L3_code.tif', 'L4_code.tif')
            is_responses = re.search('responses', filepath_in) or \
                           any([filepath_in.endswith(suffix) for suffix in response_suffixes])
            assert is_features or is_responses, 'Unknown file type:  {}'.format(filename)

            resampling = 'bilinear' if is_features else 'nearest'
            command = 'gdal_translate -outsize 50% 50% -r {resampling} {filepath_in} {filepath_out}'.format(
                resampling=resampling, filepath_in=filepath_in, filepath_out=filepath_out)
            gdal_command_line.run_gdal_command(command, _logger)
        except Exception as error_:
            raise error_
        finally:
            file_lock.close()
            os.remove(filepath_lock)


if __name__ == '__main__':
    downsample_rasters()

