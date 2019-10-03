from argparse import ArgumentParser
import logging

from bfgn.configuration import configs
from bfgn.data_management import data_core
from bfgn.experiments import experiments

from gcrmnbc.application_global import apply
from gcrmnbc.utils import data_bucket, logs, shared_configs


def run_application(config_name: str, label_experiment: str, response_mapping: str, model_version: str) -> None:
    config = shared_configs.build_dynamic_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)

    logger = logs.get_model_logger(
        logger_name='log_run_global_application', label_experiment=label_experiment, response_mapping=response_mapping,
        config=config
    )

    # Get data and model objects
    logger.info('Create data and model objects')
    data_container = _load_dataset(config)
    experiment = _load_experiment(config, data_container)
    logging.getLogger('bfgn').setLevel(logging.WARNING)  # Turn down BFGN logging

    # Get quad blobs and apply model
    logger.info('Get quad blobs')
    quad_blobs = data_bucket.get_imagery_quad_blobs()
    logger.info('Apply model to quads')
    for idx_quad, quad_blob in enumerate(quad_blobs):
        logger.info('Apply model to quad blob {} of {}'.format(1+idx_quad, len(quad_blobs)))
        apply.apply_model_to_quad(quad_blob, data_container, experiment, response_mapping, config_name, model_version)


def _load_dataset(config: configs.Config) -> data_core.DataContainer:
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()
    return data_container


def _load_experiment(config: configs.Config, data_container: data_core.DataContainer) -> experiments.Experiment:
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)
    return experiment


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--model_version', required=True)
    args = vars(parser.parse_args())
    run_application(**args)
