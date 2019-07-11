from argparse import ArgumentParser
import os

from rsCNN.configuration import configs
from rsCNN.data_management import apply_model_to_data, data_core
from rsCNN.reporting import reports
from rsCNN.experiments import experiments


_DIR_MODELS = 'models'
_DIR_APPLIED = 'applied'

_DIR_DATA_BASE = '/scratch/nfabina/gcrmn-benthic-classification'
_DIR_DATA_REEF = os.path.join(_DIR_DATA_BASE, 'data')
_DIR_DATA_CLEAN = os.path.join(_DIR_DATA_REEF, '{}/clean')
_DIR_DATA_BUILT = os.path.join(_DIR_DATA_BASE, 'built')
_DIR_DATA_APPLY = os.path.join(_DIR_DATA_BASE, 'for_application')

_FILENAME_FEATURES = 'features.vrt'
_FILENAME_RESPONSES = 'responses_{}.tif'
_FILENAME_BOUNDARIES = 'boundaries.shp'

_RESPONSE_MAPPINGS = ('lwr', 'bio')
_RESPONSE_MAPPING_CLASSES = {'lwr': 3, 'bio': 4}

_OPERATION_BUILD = 'build'
_OPERATION_CLASSIFY = 'classify'
_OPERATION_APPLY = 'apply'
_OPERATION_ALL = 'all'
_OPERATIONS = (_OPERATION_ALL, _OPERATION_BUILD, _OPERATION_CLASSIFY, _OPERATION_APPLY)


def run_classification(filepath_config: str, response_mapping: str, operations: str) -> None:
    assert response_mapping in _RESPONSE_MAPPINGS, 'response_mapping must be one of:  {}'.format(_RESPONSE_MAPPINGS)
    assert all([operation in _OPERATIONS for operation in operations]), 'operations must be in:  {}'.format(_OPERATIONS)

    config = configs.create_config_from_file(filepath_config)
    config_name = os.path.splitext(os.path.basename(filepath_config))[0]

    # Update config with filesystem references or potentially dynamic values
    feature_files = list()
    response_files = list()
    boundary_files = list()
    for dir_reef in os.listdir(_DIR_DATA_REEF):
        dir_clean = _DIR_DATA_CLEAN.format(dir_reef)
        feature_files.append([os.path.join(dir_clean, _FILENAME_FEATURES)])
        response_files.append([os.path.join(dir_clean, _FILENAME_RESPONSES.format(response_mapping))])
        boundary_files.append(os.path.join(dir_clean, _FILENAME_BOUNDARIES))
    config.raw_files.feature_files = feature_files
    config.raw_files.response_files = response_files
    config.raw_files.boundary_files = boundary_files
    config.data_build.dir_out = _DIR_DATA_BUILT
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name)
    config.architecture.n_classes = _RESPONSE_MAPPING_CLASSES[response_mapping]

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
    if _OPERATION_CLASSIFY in operations or _OPERATION_ALL in operations:
        experiment.fit_model_with_data_container(data_container)
        reporter.create_model_report()

    # Apply model
    if _OPERATION_APPLY in operations or _OPERATION_ALL in operations:
        dir_applied = os.path.join(config.model_training.dir_out, _DIR_APPLIED)
        if not os.path.exists(dir_applied):
            os.makedirs(dir_applied)
        filenames_apply = os.listdir(_DIR_DATA_APPLY)
        for idx_apply, filename_apply in enumerate(filenames_apply):
            filepath_in = os.path.join(_DIR_DATA_APPLY, filename_apply)
            filepath_out = os.path.join(dir_applied, filename_apply)
            if os.path.exists(filepath_out):
                continue
            apply_model_to_data.apply_model_to_raster(
                experiment.model, data_container, filepath_in, os.path.splitext(filepath_out)[0])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--filepath_config', dest='filepath_config', required=True)
    parser.add_argument('--response_mapping', dest='response_mapping', required=True)
    parser.add_argument('--operations', dest='operations', required=True)
    args = vars(parser.parse_args())
    run_classification(**args)
