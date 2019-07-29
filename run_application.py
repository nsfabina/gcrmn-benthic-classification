from argparse import ArgumentParser
from logging import Logger
import os
import re
from typing import List

from bfgn.data_management import apply_model_to_data, data_core
from bfgn.experiments import experiments
from bfgn.utils import logging

import shared_configs


_DIR_CONFIGS = 'configs'
_DIR_APPLY_BASE = '/scratch/nfabina/gcrmn-benthic-classification'

_SUBDIR_MOSAIC_IN = 'visual_mosaic_v1'
_SUBDIR_MOSAIC_OUT = 'visual_mosaic_v1_applied/{}/{}'
_DIR_MOSAIC_IN = os.path.join(_DIR_APPLY_BASE, _SUBDIR_MOSAIC_IN)

_SUBDIR_TRAINING_IN = 'training_data'
_SUBDIR_TRAINING_OUT = 'training_data_applied/{}/{}'
_DIR_TRAINING_IN = os.path.join(_DIR_APPLY_BASE, _SUBDIR_TRAINING_IN)
_FILENAME_IN = 'features.vrt'

_FILENAME_SUFFIX_OUT = '_applied.tif'


def run_application_to_training_data(config_name: str, response_mapping: str) -> None:
    filepath_config = os.path.join(_DIR_CONFIGS, config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # Get paths and logger
    log_out = os.path.join(_DIR_APPLY_BASE, _SUBDIR_TRAINING_OUT.format(config_name, response_mapping), 'log.out')
    if not os.path.exists(os.path.dirname(log_out)):
        os.makedirs(os.path.dirname(log_out))
    logger = logging.get_root_logger(log_out)

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Apply model
    filepaths_apply = _get_application_raster_filepaths_for_training_data(logger)
    subdir_out = _SUBDIR_TRAINING_OUT.format(config_name, response_mapping)
    for idx_filepath, filepath_apply in enumerate(filepaths_apply):
        dir_out = os.path.dirname(os.path.dirname(re.sub(_SUBDIR_TRAINING_IN, subdir_out, filepath_apply)))
        filename_out = 'responses_{}'.format(response_mapping) + _FILENAME_SUFFIX_OUT
        filepath_out = os.path.join(dir_out, filename_out)
        if not os.path.exists(os.path.dirname(filepath_out)):
            os.makedirs(os.path.dirname(filepath_out))
        logger.debug('Applying model to raster {} of {}; input and output filepaths are {} and {}'.format(
            idx_filepath+1, len(filepath_apply), filepath_apply, filepath_out))
        _apply_to_raster(experiment, data_container, filepath_apply, filepath_out, logger)


def _get_application_raster_filepaths_for_training_data(logger: Logger) -> List[str]:
    filepaths = list()
    for path, dirnames, filenames in os.walk(_DIR_TRAINING_IN):
        for filename in filenames:
            if filename != _FILENAME_IN:
                continue
            filepaths.append(os.path.join(path, filename))
    logger.debug('Found {} rasters for application'.format(len(filepaths)))
    return sorted(filepaths)


def run_application_to_global_mosaic(config_name: str, response_mapping: str) -> None:
    filepath_config = os.path.join(_DIR_CONFIGS, config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # Get paths and logger
    log_out = os.path.join(_DIR_APPLY_BASE, _SUBDIR_MOSAIC_OUT.format(config_name, response_mapping), 'log.out')
    if not os.path.exists(os.path.dirname(log_out)):
        os.makedirs(os.path.dirname(log_out))
    logger = logging.get_root_logger(log_out)

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Apply model
    filepaths_apply = _get_application_raster_filepaths_for_global_mosaics(logger)
    subdir_out = _SUBDIR_MOSAIC_OUT.format(config_name, response_mapping)
    for idx_filepath, filepath_apply in enumerate(filepaths_apply):
        filepath_out = os.path.splitext(re.sub(_SUBDIR_MOSAIC_IN, subdir_out, filepath_apply))[0] + _FILENAME_SUFFIX_OUT
        if not os.path.exists(os.path.dirname(filepath_out)):
            os.makedirs(os.path.dirname(filepath_out))
        logger.debug('Applying model to raster {} of {}; input and output filepaths are {} and {}'.format(
            idx_filepath+1, len(filepath_apply), filepath_apply, filepath_out))
        _apply_to_raster(experiment, data_container, filepath_apply, filepath_out, logger)


def _get_application_raster_filepaths_for_global_mosaics(logger: Logger) -> List[str]:
    filepaths = list()
    for path, dirnames, filenames in os.walk(_DIR_MOSAIC_IN):
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
        apply_model_to_data.apply_model_to_site(
            experiment.model, data_container, [filepath_apply], basename_out, exclude_feature_nodata=True)
        logger.debug('Application success, removing lock file')
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)
        logger.debug('Lock file removed')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--response_mapping', required=True)
    args = parser.parse_args()
    if args.target == 'training_data':
        run_application_to_training_data(args.config_name, args.response_mapping)
    elif args.target == 'global_mosaic':
        run_application_to_global_mosaic(args.config_name, args.response_mapping)
    else:
        raise AssertionError('target must be either training or mosaic')
