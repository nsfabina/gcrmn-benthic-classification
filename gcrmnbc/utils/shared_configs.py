import os
import re

from bfgn.configuration import configs


_DIR_MODELS = '../models'

_DIR_DATA_BASE = '/scratch/nfabina/gcrmn-benthic-classification/'
_DIR_DATA_CLEAN = os.path.join(_DIR_DATA_BASE, 'training_data/clean')
_DIR_DATA_BUILT = os.path.join(_DIR_DATA_BASE, 'built_{}_{}')

_SUFFIX_FEATURES = 'features.tif'
_SUFFIX_RESPONSES = 'responses.tif'
_SUFFIX_BOUNDARIES = 'boundaries.shp'

_RESPONSE_MAPPINGS = ('lwr', )
_RESPONSE_MAPPING_CLASSES = {'lwr': 4, }


def build_dynamic_config(filepath_config: str, response_mapping: str) -> configs.Config:
    assert response_mapping in _RESPONSE_MAPPINGS, \
        'response_mapping is {} but must be one of:  {}'.format(response_mapping, _RESPONSE_MAPPINGS)

    # Get all feature, response, and boundary files
    filepaths_features = [os.path.join(_DIR_DATA_CLEAN, filename) for filename in os.listdir(_DIR_DATA_CLEAN)
                          if filename.endswith(_SUFFIX_FEATURES)]
    filepaths_responses = [re.sub(_SUFFIX_FEATURES, _SUFFIX_RESPONSES, filepath) for filepath in filepaths_features]
    filepaths_boundaries = [re.sub(_SUFFIX_FEATURES, _SUFFIX_BOUNDARIES, filepath) for filepath in filepaths_features]
    assert all([os.path.exists(filepath) for filepath in filepaths_responses]), 'Not all response files are present'
    assert all([os.path.exists(filepath) for filepath in filepaths_responses]), 'Not all boundary files are present'

    # Parse config
    config = configs.create_config_from_file(filepath_config)
    config_name = os.path.splitext(os.path.basename(filepath_config))[0]

    # Update config with dynamic values
    config.raw_files.feature_files = filepaths_features
    config.raw_files.response_files = filepaths_responses
    config.raw_files.boundary_files = filepaths_boundaries
    config.data_build.dir_out = _DIR_DATA_BUILT.format(response_mapping, config.data_build.window_radius)
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name, response_mapping)
    config.architecture.n_classes = _RESPONSE_MAPPING_CLASSES[response_mapping]
    return config
