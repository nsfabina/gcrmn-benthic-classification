from argparse import ArgumentParser
import os

from rsCNN.configuration import configs
from rsCNN.data_management import apply_model_to_data, data_core
from rsCNN.reporting import reports
from rsCNN.experiments import experiments
from rsCNN.utils import logging


_LOG_LEVEL = 'DEBUG'

_DIR_MODELS = 'models'
_DIR_IMAGERY = '/scratch/nfabina/gcrmn-benthic-classification/imagery/belize'
_DIR_BUILT_DATA = os.path.join(_DIR_IMAGERY, 'built')
_DIR_RAW_DATA = os.path.join(_DIR_IMAGERY, 'raw')

_FILEPATH_FEATURES = os.path.join(_DIR_RAW_DATA, 'features.vrt')
_FILEPATH_RESPONSES = os.path.join(_DIR_RAW_DATA, 'responses.tif')


def classify(filepath_config: str) -> None:
    config = configs.create_config_from_file(filepath_config)
    config_name = os.path.splitext(os.path.basename(filepath_config))[0]

    # Update config with filesystem references or potentially dynamic values
    config.raw_files.feature_files = [[_FILEPATH_FEATURES]]
    config.raw_files.response_files = [[_FILEPATH_RESPONSES]]
    config.data_build.dir_out = _DIR_BUILT_DATA
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name)

    # Create directories if necessary
    if not os.path.exists(config.data_build.dir_out):
        os.makedirs(config.data_build.dir_out)
    if not os.path.exists(config.model_training.dir_out):
        os.makedirs(config.model_training.dir_out)
    
    # Logger for tracking progress and debugging
    logger = logging.get_root_logger(os.path.join(config.model_training.dir_out, 'log.out'))
    logger.setLevel(_LOG_LEVEL)

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)
    logger.info('Model memory: {} GB'.format(
        experiment.calculate_model_memory_footprint(batch_size=config.data_samples.batch_size)))

    # Create preliminary model report before training
    reporter = reports.Reporter(data_container, experiment, config)
    reporter.create_model_report()

    # Train model
    experiment.fit_model_with_data_container(data_container)

    # Create completed model report
    reporter.create_model_report()

    # Apply model
    filepath_out = os.path.join(config.model_training.dir_out, 'applied.tif')
    apply_model_to_data.apply_model_to_raster(experiment.model, data_container, _FILEPATH_FEATURES, filepath_out)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--filepath_config', dest='filepath_config', required=True)
    filepath_config = vars(parser.parse_args())['filepath_config']
    classify(filepath_config=filepath_config)
