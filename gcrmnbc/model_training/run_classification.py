from argparse import ArgumentParser
import os

from bfgn.data_management import data_core, sequences
from bfgn.reporting import reports
from bfgn.experiments import experiments

from gcrmnbc.utils import logs, paths, shared_configs


def run_classification(
        config_name: str,
        label_experiment: str,
        response_mapping: str,
        build_only: bool = False
) -> None:
    logger = logs.get_model_logger(config_name, response_mapping, 'log_run_classification.log')
    config = shared_configs.build_dynamic_config(config_name, label_experiment, response_mapping)

    # Create directories if necessary
    if not os.path.exists(config.data_build.dir_out):
        os.makedirs(config.data_build.dir_out)
    if not os.path.exists(config.model_training.dir_out):
        os.makedirs(config.model_training.dir_out)

    # Exit early if classification already finished -- assume build is finished too
    filepath_complete = paths.get_filepath_classify_complete(label_experiment, response_mapping, config)
    if os.path.exists(filepath_complete):
        return

    # Exit early if classification in progress
    filepath_lock = paths.get_filepath_classify_lock(label_experiment, response_mapping, config)
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
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--build_only', action='store_true')
    args = vars(parser.parse_args())
    run_classification(**args)
