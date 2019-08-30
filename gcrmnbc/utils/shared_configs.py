import os

from bfgn.configuration import configs


_DIR_MODELS = '../models'

_DIR_DATA_BASE = '/scratch/nfabina/gcrmn-benthic-classification'
_DIR_DATA_REEF = os.path.join(_DIR_DATA_BASE, 'training_data')
_DIR_DATA_CLEAN = os.path.join(_DIR_DATA_REEF, '{}/clean')
_DIR_DATA_BUILT = os.path.join(_DIR_DATA_BASE, 'built_{}_{}')

_FILENAME_FEATURES = 'features.vrt'
_FILENAME_RESPONSES = 'responses_{}.tif'
_FILENAME_BOUNDARIES = 'boundaries.shp'

_RESPONSE_MAPPINGS = ('lwr', )
_RESPONSE_MAPPING_CLASSES = {'lwr': 3, }


def build_dynamic_config(filepath_config: str, response_mapping: str) -> configs.Config:
    assert response_mapping in _RESPONSE_MAPPINGS, \
        'response_mapping is {} but must be one of:  {}'.format(response_mapping, _RESPONSE_MAPPINGS)

    # Parse config
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
    config.data_build.dir_out = _DIR_DATA_BUILT.format(response_mapping, config.data_build.window_radius)
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name, response_mapping)
    config.architecture.n_classes = _RESPONSE_MAPPING_CLASSES[response_mapping]
    return config
