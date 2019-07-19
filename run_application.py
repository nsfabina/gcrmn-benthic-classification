from argparse import ArgumentParser
from logging import Logger
import os
import re
from typing import List

from rsCNN.data_management import apply_model_to_data, data_core
from rsCNN.experiments import experiments
from rsCNN.utils import logging

import shared_configs


_DIR_CONFIGS = 'configs'
_DIR_APPLY_BASE = '/scratch/nfabina/gcrmn-benthic-classification'
_SUBDIR_APPLY_IN = 'visual_mosaic_v1'
_SUBDIR_APPLY_OUT = 'visual_mosaic_v1_applied/{}'
_DIR_APPLY_IN = os.path.join(_DIR_APPLY_BASE, _SUBDIR_APPLY_IN)
_LOG_OUT = os.path.join(_DIR_APPLY_BASE, _SUBDIR_APPLY_OUT, 'log.out')
_FILE_APPLY_OUT = '_applied.tif'


def run_application(config_name: str, response_mapping: str) -> None:
    filepath_config = os.path.join(_DIR_CONFIGS, config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # Get paths and logger
    logger = logging.get_root_logger(_LOG_OUT.format(config_name))

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Apply model
    filepaths_apply = _get_application_raster_filepaths(logger)
    subdir_out = _SUBDIR_APPLY_OUT.format(config_name)
    for idx_filepath, filepath_apply in enumerate(filepaths_apply):
        filepath_out = os.path.splitext(re.sub(_SUBDIR_APPLY_IN, subdir_out, filepath_apply))[0] + _FILE_APPLY_OUT
        if not os.path.exists(os.path.dirname(filepath_out)):
            os.makedirs(os.path.dirname(filepath_out))
        logger.debug('Applying model to raster {} of {}; input and output filepaths are {} and {}'.format(
            idx_filepath+1, len(filepath_apply), filepath_apply, filepath_out))
        _apply_to_raster(experiment, data_container, filepath_apply, filepath_out, logger)


def _get_application_raster_filepaths(logger: Logger) -> List[str]:
    filepaths = list()
    for path, dirnames, filenames in os.walk(_DIR_APPLY_IN):
        for filename in filenames:
            if not filename.endswith('.tif'):
                continue
            filepaths.append(os.path.join(path, filename))
    logger.debug('Found {} rasters for application'.format(len(filepaths)))
    return sorted(filepaths)


def _apply_to_raster(
        experiment: experiments.Experiment,
        data_container: data_core.DataContainer,
        filepath_apply: str,
        filepath_out: str,
        logger: Logger
) -> None:
    # Return early if application is completed or in progress
    if os.path.exists(filepath_out):
        logger.debug('Skipping application:  output file already exists at {}'.format(filepath_out))
        return
    basename_out = os.path.splitext(filepath_out)[0]
    filepath_lock = basename_out + '.lock'
    if os.path.exists(filepath_lock):
        logger.debug('Skipping application:  lock file already exists at {}'.format(filepath_lock))
        return

    # Acquire the file lock or return if we lose the race condition
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        logger.debug('Skipping application:  lock file acquired by another process at {}'.format(filepath_lock))
        return

    # Apply model to raster and clean up file lock
    try:
        apply_model_to_data.apply_model_to_raster(
            experiment.model, data_container, filepath_apply, basename_out, exclude_feature_nodata=True)
        logger.debug('Application success, removing lock file')
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)
        logger.debug('Lock file removed')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--response_mapping', required=True)
    args = vars(parser.parse_args())
    run_application(**args)
