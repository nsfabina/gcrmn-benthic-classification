import os
import re

from bfgn.configuration import configs

from gcrmnbc.utils import paths


_SUFFIX_FEATURES = '_features.tif'

_SUFFIXES_RESPONSES_BOUNDARIES = (
    ('_responses_{}b.tif', '_boundaries.shp', True),  # Reef data, True/False denotes whether its required or not
    ('_land.tif', '_land.shp', False),  # Land data
    ('_water.tif', '_water.shp', False),  # Water data
)

_RESPONSE_MAPPINGS = ('lwr', 'lwrn', )
_RESPONSE_MAPPING_CLASSES = {'lwr': 6, 'lwrn': 10, }


def build_dynamic_config(config_name: str, label_experiment: str, response_mapping: str) -> configs.Config:
    assert response_mapping in _RESPONSE_MAPPINGS, \
        'response_mapping is {} but must be one of:  {}'.format(response_mapping, _RESPONSE_MAPPINGS)

    filepaths_features = list()
    filepaths_responses = list()
    filepaths_boundaries = list()

    # Note that we need to use feature files multiple times in some cases. Feature files will always be associated with
    # reef training data, but may also be associated with land and/or water training data. Thus, feature files may be
    # used 1-3 times in the training data.

    for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN):
        if not filename.endswith(_SUFFIX_FEATURES):
            continue

        filepath_features = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename)

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

    # Parse config and update dynamic values
    config = configs.create_config_from_file(paths.get_filepath_config(config_name))
    config.raw_files.feature_files = filepaths_features
    config.raw_files.response_files = filepaths_responses
    config.raw_files.boundary_files = filepaths_boundaries
    config.data_build.dir_out = paths.get_dir_built_data_experiment(label_experiment, response_mapping, config)
    config.model_training.dir_out = paths.get_dir_model_experiment_config(label_experiment, response_mapping, config)
    config.architecture.n_classes = _RESPONSE_MAPPING_CLASSES[response_mapping]

    # Modify configs for different experiments
    if label_experiment.startswith('downsample'):
        config = _modify_config_for_downsampling(label_experiment, response_mapping, config)

    return config


def _modify_config_for_downsampling(label_experiment: str, response_mapping: str, config: configs.Config) \
        -> configs.Config:
    if label_experiment == 'downsample_25':
        downsample_pct = '25'
    elif label_experiment == 'downsample_50':
        downsample_pct = '50'

    # Modify feature and response filepaths, but leave boundaries the same
    config.raw_files.feature_files = [
        [re.sub('originals', 'downsample_{}'.format(downsample_pct), ff[0])] for ff in config.raw_files.feature_files]
    config.raw_files.response_files = [
        [re.sub('originals', 'downsample_{}'.format(downsample_pct), rf[0])] for rf in config.raw_files.response_files]

    # Modify built data filepath
    config.data_build.dir_out = paths.get_dir_built_data_experiment(label_experiment, response_mapping, config)
    config.model_training.dir_out = paths.get_dir_model_experiment_config(label_experiment, response_mapping, config)
    return config
