import os

from bfgn.configuration import configs


DIR_BFGN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIR_CONFIGS = os.path.join(DIR_BFGN, 'configs')
DIR_MODELS = os.path.join(DIR_BFGN, 'models')

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/'

DIR_DATA_APPLY_CALVAL = os.path.join(DIR_DATA, 'applied_data')
DIR_DATA_BUILT = os.path.join(DIR_DATA, 'built_data')
DIR_DATA_EVAL = os.path.join(DIR_DATA, 'evaluation_data')
DIR_DATA_GLOBAL = os.path.join(DIR_DATA, 'global_data')
DIR_DATA_TRAIN = os.path.join(DIR_DATA, 'training_data')

DIR_DATA_TRAIN_FEATURES = os.path.join(DIR_DATA_TRAIN, 'features')
DIR_DATA_TRAIN_FEATURES_RAW = os.path.join(DIR_DATA_TRAIN_FEATURES, 'raw')
DIR_DATA_TRAIN_FEATURES_CLEAN = os.path.join(DIR_DATA_TRAIN_FEATURES, 'clean')

DIR_DATA_TRAIN_MP = os.path.join(DIR_DATA_TRAIN, 'responses_mp')
DIR_DATA_TRAIN_MP_RAW = os.path.join(DIR_DATA_TRAIN_MP, 'raw')
DIR_DATA_TRAIN_MP_CLEAN = os.path.join(DIR_DATA_TRAIN_MP, 'clean')
DIR_DATA_TRAIN_MP_BOUNDS = os.path.join(DIR_DATA_TRAIN_MP, 'boundaries_mp')

DIR_DATA_TRAIN_UQ = os.path.join(DIR_DATA_TRAIN, 'responses_uq')
DIR_DATA_TRAIN_UQ_RAW = os.path.join(DIR_DATA_TRAIN_UQ, 'raw')

DIR_DATA_TRAIN_SUPP = os.path.join(DIR_DATA_TRAIN, 'responses_supp')
DIR_DATA_TRAIN_SUPP_RAW = os.path.join(DIR_DATA_TRAIN_UQ, 'raw')

SUBDIR_DATA_TRAIN_DOWNSAMPLE = 'resolution_{}'

FILENAME_BUILD_COMPLETE = 'build.complete'
FILENAME_CLASSIFY_LOCK = 'classify.lock'
FILENAME_CLASSIFY_COMPLETE = 'classify.complete'
FILENAME_APPLY_CALVAL_COMPLETE = 'calval_application.complete'

FILENAME_CALVAL_STATS = 'asu_statistics.json'
FILENAME_CALVAL_FIGS = 'asu_statistics.pdf'


def get_dir_built_data_experiment(label_experiment: str, response_mapping: str, config: configs.Config) -> str:
    if label_experiment.endswith('_aug'):
        label_experiment = label_experiment[:-4]
    window_radius = str(config.data_build.window_radius)
    loss_radius = str(config.data_build.loss_window_radius)
    return os.path.join(DIR_DATA_BUILT, label_experiment, '_'.join([response_mapping, window_radius, loss_radius]))


def get_dir_calval_data_experiment(label_experiment: str, response_mapping: str) -> str:
    return os.path.join(DIR_DATA_APPLY_CALVAL, label_experiment, response_mapping)


def get_dir_calval_data_experiment_config(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return os.path.join(get_dir_calval_data_experiment(label_experiment, response_mapping), config_name)


def get_dir_eval_data_experiment(reef: str, label_experiment: str) -> str:
    if label_experiment.endswith('_aug'):
        label_experiment = label_experiment[:-4]
    if label_experiment == 'millennium':
        return os.path.join(DIR_DATA_EVAL, reef, 'downsample_50')
    return os.path.join(DIR_DATA_EVAL, reef, label_experiment)


def get_dir_training_data_experiment(label_experiment: str) -> str:
    if label_experiment.endswith('_aug'):
        label_experiment = label_experiment[:-4]
    return os.path.join(DIR_DATA_TRAIN, label_experiment)


def get_dir_model_experiment(label_experiment: str) -> str:
    return os.path.join(DIR_MODELS, label_experiment)


def get_dir_model_experiment_config(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return os.path.join(get_dir_model_experiment(label_experiment), response_mapping, config_name)


def get_filepath_build_complete(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return os.path.join(
        get_dir_model_experiment_config(config_name, label_experiment, response_mapping),
        FILENAME_BUILD_COMPLETE
    )


def get_filepath_calval_apply_complete(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return os.path.join(
        get_dir_calval_data_experiment_config(config_name, label_experiment, response_mapping),
        FILENAME_APPLY_CALVAL_COMPLETE
    )


def get_filepath_classify_complete(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return os.path.join(
        get_dir_model_experiment_config(config_name, label_experiment, response_mapping),
        FILENAME_CLASSIFY_COMPLETE
    )


def get_filepath_classify_lock(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return os.path.join(
        get_dir_model_experiment_config(config_name, label_experiment, response_mapping),
        FILENAME_CLASSIFY_LOCK
    )


def get_filepath_config(config_name: str) -> str:
    return os.path.join(DIR_CONFIGS, config_name + '.yaml')


def get_filepath_config_from_config(config: configs.Config) -> str:
    return os.path.join(DIR_CONFIGS, _get_experiment_config_string(config) + '.yaml')


def get_filepath_build_only_config_from_config(config: configs.Config) -> str:
    return os.path.join(DIR_CONFIGS, 'build_only_{}_{}.yaml'.format(
        config.data_build.window_radius, config.data_build.loss_window_radius))


def _get_experiment_config_string(config: configs.Config) -> str:
    if config.model_training.architecture_name in ('dense_unet', 'unet'):
        str_layers = str(config.architecture.block_structure[0]) + str(len(config.architecture.block_structure))
        str_growth = '_growth' if config.architecture.use_growth else ''
    elif config.model_training.architecture_name == 'flat_net':
        str_layers = str(config.architecture.num_layers)
        str_growth = ''
    str_batch_norm = '_batch_norm' if config.architecture.use_batch_norm else ''
    config_string = '_'.join([
        config.model_training.architecture_name,
        str(config.data_build.window_radius),
        str(config.data_build.loss_window_radius),
        str_layers,
        str(config.architecture.filters)
    ])
    config_string += str_batch_norm + str_growth
    return config_string
