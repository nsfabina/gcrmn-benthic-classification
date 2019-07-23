from argparse import ArgumentParser
import os

from bfgn.data_management import data_core
from bfgn.reporting import reports
from bfgn.experiments import experiments

import shared_configs


_DIR_CONFIGS = 'configs'
_FILENAME_LOCK = 'classify.lock'
_FILENAME_SUCCESS = 'classify.complete'


def run_classification(config_name: str, response_mapping: str, build_only: bool = False) -> None:
    filepath_config = os.path.join(_DIR_CONFIGS, config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # Create directories if necessary
    if not os.path.exists(config.data_build.dir_out):
        os.makedirs(config.data_build.dir_out)
    if not os.path.exists(config.model_training.dir_out):
        os.makedirs(config.model_training.dir_out)

    # Exit early if classification already finished -- assume build is finished too
    filepath_success = os.path.join(config.model_training.dir_out, _FILENAME_SUCCESS)
    if os.path.exists(filepath_success):
        return

    # Exit early if classification in progress
    filepath_lock = os.path.join(config.model_training.dir_out, _FILENAME_LOCK)
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        return

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Create preliminary model report before training
    reporter = reports.Reporter(data_container, experiment, config)
    reporter.create_model_report()
    if build_only:
        return

    # Train model
    experiment.fit_model_with_data_container(data_container)
    reporter.create_model_report()

    # Create success file to avoid rerunning in the future, close and remove lock file
    open(filepath_success, 'w')
    file_lock.close()
    os.remove(filepath_lock)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--build_only', action='store_true')
    args = vars(parser.parse_args())
    run_classification(**args)
