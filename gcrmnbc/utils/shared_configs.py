import os
import re

from bfgn.configuration import configs


_DIR_MODELS = '../models'

_DIR_DATA_BASE = '/scratch/nfabina/gcrmn-benthic-classification/'
_DIR_DATA_CLEAN = os.path.join(_DIR_DATA_BASE, 'training_data/clean')
_DIR_DATA_BUILT = os.path.join(_DIR_DATA_BASE, 'built_{}_{}_{}')

_SUFFIX_FEATURES = '_features.tif'

_SUFFIXES_RESPONSES_BOUNDARIES = (
    ('_responses_{}.tif', '_boundaries.shp', True),  # Reef data, True/False denotes whether its required or not
    ('_land.tif', '_land.shp', False),  # Land data
    ('_water.tif', '_water.shp', False),  # Water data
)

_RESPONSE_MAPPINGS = ('lwr', 'lwrn', )
_RESPONSE_MAPPING_CLASSES = {'lwr': 3, 'lwrn': 4, }


def build_dynamic_config(filepath_config: str, response_mapping: str) -> configs.Config:
    assert response_mapping in _RESPONSE_MAPPINGS, \
        'response_mapping is {} but must be one of:  {}'.format(response_mapping, _RESPONSE_MAPPINGS)

    filepaths_features = list()
    filepaths_responses = list()
    filepaths_boundaries = list()

    # Note that we need to use feature files multiple times in some cases. Feature files will always be associated with
    # reef training data, but may also be associated with land and/or water training data. Thus, feature files may be
    # used 1-3 times in the training data.

    for filename in os.listdir(_DIR_DATA_CLEAN):
        if not filename.endswith(_SUFFIX_FEATURES):
            continue

        filepath_features = os.path.join(_DIR_DATA_CLEAN, filename)

        for suffix_responses, suffix_boundaries, is_required in _SUFFIXES_RESPONSES_BOUNDARIES:
            if 'responses' in suffix_responses:
                filepath_responses = re.sub(
                    _SUFFIX_FEATURES, suffix_responses.format(response_mapping), filepath_features)
            else:
                filepath_responses = re.sub(_SUFFIX_FEATURES, suffix_responses, filepath_features)
            filepath_boundaries = re.sub(_SUFFIX_FEATURES, suffix_boundaries, filepath_features)

            if is_required:
                assert os.path.exists(filepath_responses), \
                    'Response file is not available at {}'.format(filepath_responses)
                assert os.path.exists(filepath_boundaries), \
                    'Boundary file is not available at {}'.format(filepath_boundaries)
            if os.path.exists(filepath_responses):
                assert os.path.exists(filepath_boundaries), \
                    'Response file is available, but boundary file not found:  {} and {}'.format(
                        filepath_responses, filepath_boundaries)
            if not os.path.exists(filepath_responses):
                continue

            filepaths_features.append([filepath_features])
            filepaths_responses.append([filepath_responses])
            filepaths_boundaries.append(filepath_boundaries)

    # Parse config
    config = configs.create_config_from_file(filepath_config)
    config_name = os.path.splitext(os.path.basename(filepath_config))[0]

    # Update config with dynamic values
    config.raw_files.feature_files = filepaths_features
    config.raw_files.response_files = filepaths_responses
    config.raw_files.boundary_files = filepaths_boundaries
    config.data_build.dir_out = _DIR_DATA_BUILT.format(
        response_mapping, config.data_build.window_radius, config.data_build.loss_window_radius)
    config.model_training.dir_out = os.path.join(_DIR_MODELS, config_name, response_mapping)
    config.architecture.n_classes = _RESPONSE_MAPPING_CLASSES[response_mapping]
    return config
