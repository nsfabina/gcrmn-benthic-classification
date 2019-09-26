from argparse import ArgumentParser
import logging
import os

from bfgn.configuration import configs
from bfgn.data_management import data_core
from bfgn.experiments import experiments

from gcrmnbc.application_global import apply
from gcrmnbc.utils import data_bucket, shared_configs


_DIR_CONFIGS = '../configs'
_DIR_MODELS = '../models'


def run_application(config_name: str, response_mapping: str, model_version: str) -> None:
    filepath_config = os.path.join(_DIR_CONFIGS, config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)

    # Get paths and logger
    log_out = os.path.join(_DIR_MODELS, config_name, response_mapping, 'log_global_application')
    if not os.path.exists(os.path.dirname(log_out)):
        os.makedirs(os.path.dirname(log_out))
    logger = logging.getLogger('model_global_application')
    logger.setLevel('DEBUG')
    _formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
    _handler = logging.FileHandler(log_out)
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

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
    parser.add_argument('--config_name', type=str, required=True)
    parser.add_argument('--response_mapping', type=str, required=True)
    parser.add_argument('--model_version', type=str, required=True)
    args = parser.parse_args()
    run_application(args.config_name, args.response_mapping, args.model_version)
