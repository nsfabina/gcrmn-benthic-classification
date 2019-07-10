from argparse import ArgumentParser
import os

from rsCNN.configuration import configs
from rsCNN.data_management import data_core
from rsCNN.reporting import reports
from rsCNN.experiments import experiments


_DIR_MODELS = 'models'
_DIR_DATA_BASE = '/scratch/nfabina/gcrmn-benthic-classification'

_DIR_DATA_REEF = os.path.join(_DIR_DATA_BASE, 'data')
_DIR_DATA_CLEAN = os.path.join(_DIR_DATA_REEF, '{}/clean')
_DIR_DATA_BUILT = os.path.join(_DIR_DATA_BASE, 'built')

_FILENAME_FEATURES = 'features.vrt'
_FILENAME_RESPONSES = 'responses.tif'
_FILENAME_BOUNDARIES = 'boundaries.shp'


def classify(filepath_config: str) -> None:
    config = configs.create_config_from_file(filepath_config)
    config_name = os.path.splitext(os.path.basename(filepath_config))[0]

    # Update config with filesystem references or potentially dynamic values
    feature_files = list()
    response_files = list()
    boundary_files = list()
    for dir_reef in os.listdir(_DIR_DATA_REEF):
        dir_clean = _DIR_DATA_CLEAN.format(dir_reef)
        feature_files.append([os.path.join(dir_clean, _FILENAME_FEATURES)])
        response_files.append([os.path.join(dir_clean, _FILENAME_RESPONSES)])
        boundary_files.append(os.path.join(dir_clean, _FILENAME_BOUNDARIES))
    config.raw_files.feature_files = feature_files
    config.raw_files.response_files = response_files
    config.raw_files.boundary_files = boundary_files
    config.data_build.dir_out = _DIR_DATA_BUILT
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name)

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

    # Train model
    experiment.fit_model_with_data_container(data_container)

    # Create completed model report
    reporter.create_model_report()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--filepath_config', dest='filepath_config', required=True)
    filepath_config = vars(parser.parse_args())['filepath_config']
    classify(filepath_config=filepath_config)
