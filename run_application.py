from argparse import ArgumentParser
import errno
import logging
import os
import re
from typing import List

from rsCNN.data_management import apply_model_to_data, data_core
from rsCNN.experiments import experiments

import build_dynamic_config


_logger = logging.getLogger(__name__)


_DIR_BASE = '/scratch/nfabina/gcrmn-benthic-classification'
_SUBDIR_IN = 'visual_mosaic_v1'
_SUBDIR_OUT = 'visual_mosaic_v1_applied'
_DIR_APPLY_IN = os.path.join(_DIR_BASE, _SUBDIR_IN)
_DIR_APPLY_OUT = os.path.join(_DIR_BASE, _SUBDIR_OUT)
_FILE_SUFFIX_OUT = 'applied.tif'
_LOCK_FLAGS = os.O_CREAT | os.O_EXCL | os.O_WRONLY


def run_application(filepath_config: str, response_mapping: str) -> None:
    config = build_dynamic_config.build_dynamic_config(filepath_config, response_mapping)

    # Create directories if necessary
    dir_applied = os.path.join(config.model_training.dir_out, _DIR_APPLY_OUT)
    if not os.path.exists(dir_applied):
        os.makedirs(dir_applied)

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Apply model
    filepaths_apply = _get_application_raster_filepaths()
    for idx_filepath, filepath_apply in enumerate(filepaths_apply):
        filepath_out = os.path.splitext(re.sub(_SUBDIR_IN, _SUBDIR_OUT, filepath_apply))[0] + _FILE_SUFFIX_OUT
        _logger.debug('Applying model to raster {} of {}; input and output filepaths are {} and {}'.format(
            idx_filepath+1, len(filepath_apply), filepath_apply, filepath_out))
        _apply_to_raster(experiment, data_container, filepath_apply, filepath_out)


def _get_application_raster_filepaths() -> List[str]:
    filepaths = list()
    for path, dirnames, filenames in os.walk(_DIR_APPLY_IN):
        for filename in filenames:
            if not filename.endswith('.tif'):
                continue
            filepaths.append(os.path.join(path, filename))
    _logger.debug('Found {} rasters for application'.format(len(filepaths)))
    return sorted(filepaths)


def _apply_to_raster(
        experiment: experiments.Experiment,
        data_container: data_core.DataContainer,
        filepath_apply: str,
        filepath_out: str
) -> None:
    # Return early if application is completed or in progress
    if os.path.exists(filepath_out):
        _logger.debug('Skipping application:  output file already exists at {}'.format(filepath_out))
        return
    basename_out = os.path.splitext(filepath_out)[0]
    filepath_lock = basename_out + '.lock'
    if os.path.exists(filepath_lock):
        _logger.debug('Skipping application:  lock file already exists at {}'.format(filepath_lock))
        return

    # Acquire the file lock or return if we lose the race condition
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        _logger.debug('Skipping application:  lock file acquired by another process at {}'.format(filepath_lock))
        return

    # Apply model to raster and clean up file lock
    try:
        apply_model_to_data.apply_model_to_raster(
            experiment.model, data_container, filepath_apply, basename_out, exclude_feature_nodata=True)
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)
        _logger.debug('Removing lock file after error in application')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--filepath_config', dest='filepath_config', required=True)
    parser.add_argument('--response_mapping', dest='response_mapping', required=True)
    args = vars(parser.parse_args())
    run_application(**args)
