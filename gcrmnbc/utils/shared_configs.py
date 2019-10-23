import os
import re

from bfgn.configuration import configs

from gcrmnbc.utils import paths


def build_dynamic_config(config_name: str, label_experiment: str, response_mapping: str) -> configs.Config:
    if label_experiment in ('original', 'downsample_50', 'downsample_50_aug'):
        builder = _build_dynamic_config_for_uq_experiments
    elif 'millennium' in label_experiment:
        builder = _build_dynamic_config_for_mp_experiments
    return builder(config_name, label_experiment, response_mapping)


def _build_dynamic_config_for_uq_experiments(
        config_name: str,
        label_experiment: str,
        response_mapping: str
) -> configs.Config:
    raise AssertionError('You need to modify the paths for the UQ experiments, like the MP experiment paths')
    response_mapping_classes = {'lwr': 10, 'lwrn': 8, }
    assert response_mapping in response_mapping_classes, \
        'response_mapping is {} but must be one of:  {}'.format(response_mapping, response_mapping_classes.keys())

    filepaths_features = list()
    filepaths_responses = list()
    filepaths_boundaries = list()

    # Note that we need to use feature files multiple times in some cases. Feature files will always be associated with
    # reef training data, but may also be associated with land and/or water training data. Thus, feature files may be
    # used 1-3 times in the training data.
    # Note that we need to grab land and water from the "clean" training data directory, and we need to grab general
    # response data from the appropriate folder

    # Get supplemental land/water response data
    filenames = [f for f in os.listdir(paths.DIR_DATA_TRAIN_CLEAN) if f.endswith('land.tif') or f.endswith('water.tif')]
    for filename in filenames:
        filepath_responses = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename)
        filepath_features = re.sub('_\w*.tif', '_features.tif', filepath_responses)
        filepath_boundaries = re.sub('.tif', '.shp', filepath_responses)
        assert os.path.exists(filepath_features), 'Features file not found:  {}'.format(filepath_features)
        assert os.path.exists(filepath_boundaries), 'Boundaries file not found:  {}'.format(filepath_boundaries)
        filepaths_features.append([filepath_features])
        filepaths_responses.append([filepath_responses])
        filepaths_boundaries.append(filepath_boundaries)

    # Get supplemental additional class response data
    filenames = [f for f in os.listdir(paths.DIR_DATA_TRAIN_CLEAN) if f.endswith('_model_class.tif')]
    for filename in filenames:
        filepath_responses = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename)
        filepath_features = re.sub('_\w*.tif', '_features.tif', filepath_responses)
        filepath_boundaries = re.sub('.tif', 'boundaries.shp', filepath_responses)
        assert os.path.exists(filepath_features), 'Features file not found:  {}'.format(filepath_features)
        assert os.path.exists(filepath_boundaries), 'Boundaries file not found:  {}'.format(filepath_boundaries)
        filepaths_features.append([filepath_features])
        filepaths_responses.append([filepath_responses])
        filepaths_boundaries.append(filepath_boundaries)

    # Get UQ response data
    response_suffix = '_responses_{}b.tif'.format(response_mapping)
    dir_data = paths.get_dir_training_data_experiment(label_experiment=label_experiment)
    assert os.path.exists(dir_data), 'Training data directory not found for label_experiment {}:  {}'.format(
        label_experiment, dir_data)
    for filename in os.listdir(dir_data):
        if not filename.endswith(response_suffix):
            continue
        filepath_responses = os.path.join(dir_data, filename)
        filepath_features = re.sub(response_suffix, '_features.tif', filepath_responses)
        filename_boundaries = re.sub(response_suffix, '_boundaries.shp', filename)
        filepath_boundaries = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename_boundaries)
        assert os.path.exists(filepath_features), 'Features file not found:  {}'.format(filepath_features)
        assert os.path.exists(filepath_boundaries), 'Boundaries file not found:  {}'.format(filepath_boundaries)

        filepaths_features.append([filepath_features])
        filepaths_responses.append([filepath_responses])
        filepaths_boundaries.append(filepath_boundaries)

    # Parse config and update dynamic values
    config = configs.create_config_from_file(paths.get_filepath_config(config_name))
    config.raw_files.feature_files = filepaths_features
    config.raw_files.response_files = filepaths_responses
    config.raw_files.boundary_files = filepaths_boundaries
    config.data_build.dir_out = paths.get_dir_built_data_experiment(
        label_experiment=label_experiment, response_mapping=response_mapping, config=config)
    config.model_training.dir_out = paths.get_dir_model_experiment_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    config.architecture.n_classes = response_mapping_classes[response_mapping]
    return config


def _build_dynamic_config_for_mp_experiments(
        config_name: str,
        label_experiment: str,
        response_mapping: str
) -> configs.Config:
    response_mapping_classes = {'custom': 11}
    assert response_mapping in response_mapping_classes, \
        'response_mapping is {} but must be one of:  {}'.format(response_mapping, response_mapping_classes)

    config_features = list()
    config_responses = list()
    config_boundaries = list()

    # Set source directories
    dir_features = paths.DIR_DATA_TRAIN_FEATURES_CLEAN
    if '25' in label_experiment:
        dir_responses = os.path.join(paths.DIR_DATA_TRAIN_MP, paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format('25'))
        suffix = '_25'
    elif '50' in label_experiment:
        dir_responses = os.path.join(paths.DIR_DATA_TRAIN_MP, paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format('50'))
        suffix = '_50'
    else:
        dir_responses = paths.DIR_DATA_TRAIN_MP_CLEAN
        suffix = ''
    dir_boundaries = paths.DIR_DATA_TRAIN_MP_BOUNDS

    # Get feature/response/boundary sets
    filepaths_responses = sorted([
        os.path.join(dir_responses, filename) for filename in os.listdir(dir_responses)
        if filename.endswith('custom_response{}.tif'.format(suffix))
    ])
    for filepath_response in filepaths_responses:
        quad_name = re.search('L15-\d{4}E-\d{4}N', filepath_response).group()
        filepath_feature = os.path.join(dir_features, quad_name + '_features{}.tif'.format(suffix))
        filepath_boundary = os.path.join(dir_boundaries, quad_name + '_boundaries.shp')
        assert os.path.exists(filepath_feature), 'Features file not found:  {}'.format(filepath_feature)
        assert os.path.exists(filepath_boundary), 'Boundaries file not found:  {}'.format(filepath_boundary)

        config_features.append([filepath_feature])
        config_responses.append([filepath_response])
        config_boundaries.append(filepath_boundary)

    # Parse config and update dynamic values
    config = configs.create_config_from_file(paths.get_filepath_config(config_name))
    config.raw_files.feature_files = config_features
    config.raw_files.response_files = config_responses
    config.raw_files.boundary_files = config_boundaries
    config.data_build.dir_out = paths.get_dir_built_data_experiment(
        label_experiment=label_experiment, response_mapping=response_mapping, config=config)
    config.model_training.dir_out = paths.get_dir_model_experiment_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    config.architecture.n_classes = response_mapping_classes[response_mapping]
    return config
