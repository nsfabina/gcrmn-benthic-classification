from argparse import ArgumentParser
import os
import re

from bfgn.data_management import data_core, sequences
from bfgn.reporting import reports
from bfgn.experiments import experiments

from gcrmnbc.utils import logs, shared_configs


_DIR_CONFIGS = '../configs'
_DIR_MODELS = '../models'
FILENAME_LOCK = 'classify.lock'
FILENAME_COMPLETE = 'classify.complete'


def run_classification_downsample_experiment(
        config_name: str,
        response_mapping: str,
        downsample_pct: int,
        build_only: bool = False
) -> None:
    filepath_config = os.path.join(_DIR_CONFIGS, config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # ------------------------------------------------------------------------------------------------------------------
    # Modify config for downsample
    config.raw_files.feature_files = [
        [re.sub('clean', 'downsample_{}'.format(downsample_pct), ff[0])] for ff in config.raw_files.feature_files]
    config.raw_files.response_files = [
        [re.sub('clean', 'downsample_{}'.format(downsample_pct), rf[0])] for rf in config.raw_files.response_files]
    config.data_build.dir_out = '/scratch/nfabina/gcrmn-benthic-classification/built_lwr_downsample_{}'.format(
        downsample_pct)
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name, 'downsample_{}'.format(downsample_pct))
    # ------------------------------------------------------------------------------------------------------------------

    logger = logs.get_model_logger(config_name, response_mapping, 'log_run_classification.log')

    # Create directories if necessary
    if not os.path.exists(config.data_build.dir_out):
        os.makedirs(config.data_build.dir_out)
    if not os.path.exists(config.model_training.dir_out):
        os.makedirs(config.model_training.dir_out)

    # Exit early if classification already finished -- assume build is finished too
    filepath_complete = os.path.join(config.model_training.dir_out, FILENAME_COMPLETE)
    if os.path.exists(filepath_complete):
        return

    # Exit early if classification in progress
    filepath_lock = os.path.join(config.model_training.dir_out, FILENAME_LOCK)
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        return

    try:
        # Build dataset
        data_container = data_core.DataContainer(config)
        data_container.build_or_load_rawfile_data()
        data_container.build_or_load_scalers()
        # custom_augmentations = sequences.sample_custom_augmentations_constructor(1, config.data_build.window_radius)
        data_container.load_sequences()  #custom_augmentations)

        # Build experiment
        experiment = experiments.Experiment(config)
        experiment.build_or_load_model(data_container)

        # Create preliminary model report before training
        reporter = reports.Reporter(data_container, experiment, config)
        reporter.create_model_report()
        if build_only:
            open(filepath_complete, 'w')
            return

        # Train model
        experiment.fit_model_with_data_container(data_container, resume_training=True)
        reporter.create_model_report()

        # Create complete file to avoid rerunning in the future, close and remove lock file
        open(filepath_complete, 'w')
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--downsample_pct', type=int, required=True)
    parser.add_argument('--build_only', action='store_true')
    args = vars(parser.parse_args())
    run_classification_downsample_experiment(**args)
