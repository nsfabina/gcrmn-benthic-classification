from argparse import ArgumentParser
import os

from rsCNN.data_management import data_core
from rsCNN.reporting import reports
from rsCNN.experiments import experiments

import shared_configs


def run_classification(filepath_config: str, response_mapping: str, build_only: bool = False) -> None:
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # Create directories if necessary
    if not os.path.exists(config.data_build.dir_out):
        os.makedirs(config.data_build.dir_out)
    if not os.path.exists(config.model_training.dir_out):
        os.makedirs(config.model_training.dir_out)

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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--filepath_config', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--build_only', action='store_true')
    args = vars(parser.parse_args())
    run_classification(**args)
