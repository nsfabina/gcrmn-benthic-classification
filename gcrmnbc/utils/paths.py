import os

from bfgn.configuration import configs


DIR_BFGN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIR_CONFIGS = os.path.join(DIR_BFGN, 'configs')
DIR_MODELS = os.path.join(DIR_BFGN, 'models')

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/'

DIR_DATA_BUILT = os.path.join(DIR_DATA, 'built_data')

DIR_DATA_TRAIN = os.path.join(DIR_DATA, 'training_data')
DIR_DATA_TRAIN_CLEAN = os.path.join(DIR_DATA_TRAIN, 'clean')
DIR_DATA_TRAIN_RAW = os.path.join(DIR_DATA_TRAIN, 'raw')

DIR_DATA_EVAL = os.path.join(DIR_DATA, 'evaluation_data')
DIR_DATA_APPLY_CALVAL = os.path.join(DIR_DATA, 'applied_data')
DIR_DATA_APPLY_GLOBAL = os.path.join(DIR_DATA, 'tmp_global_application')

FILENAME_CLASSIFY_LOCK = 'classify.lock'
FILENAME_CLASSIFY_COMPLETE = 'classify.complete'
FILENAME_APPLY_CALVAL_COMPLETE = 'calval_application.complete'


def get_dir_built_data_experiment(label_experiment: str, response_mapping: str, config: configs.Config) -> str:
    return os.path.join(
        DIR_DATA_BUILT,
        label_experiment,
        '_'.join([response_mapping, config.data_build.window_radius, config.data_build.loss_window_radius])
    )


def get_dir_model_experiment(label_experiment: str) -> str:
    return os.path.join(DIR_MODELS, label_experiment)


def get_dir_model_experiment_config(label_experiment: str, response_mapping: str, config: configs.Config) -> str:
    str_blocks = str(config.architecture.block_structure[0]) + str(len(config.architecture.block_structure))
    return os.path.join(
        get_dir_model_experiment(label_experiment),
        '_'.join([
            response_mapping, config.model_training.architecture_name, config.data_build.window_radius,
            config.data_build.loss_window_radius, str_blocks, config.architecture.filters
        ])
    )


def get_filepath_classify_complete(label_experiment: str, response_mapping: str, config: configs.Config) -> str:
    return os.path.join(get_dir_model_experiment(label_experiment, response_mapping, config), FILENAME_CLASSIFY_COMPLETE)


def get_filepath_classify_lock(label_experiment: str, response_mapping: str, config: configs.Config) -> str:
    return os.path.join(get_dir_model_experiment(label_experiment, response_mapping, config), FILENAME_CLASSIFY_LOCK)


def get_filepath_config(config_name: str) -> str:
    return os.path.join(DIR_CONFIGS, config_name)


def get_filepath_config_from_config(config: configs.Config) -> str:
    str_blocks = str(config.architecture.block_structure[0]) + str(len(config.architecture.block_structure))
    basename = '_'.join([
        config.model_training.architecture_name,
        config.data_build.window_radius,
        config.data_build.loss_window_radius,
        str_blocks,
        config.architecture.filters
    ])
    return os.path.join(DIR_CONFIGS, basename + '.yaml')


def get_filepath_build_only_config_from_config(config: configs.Config) -> str:
    return os.path.join(DIR_CONFIGS, 'build_only_{}_{}.yaml'.format(
        config.data_build.window_radius, config.data_build.loss_window_radius))
