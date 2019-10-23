import os
import re
from typing import List

from gcrmnbc.utils import paths


SLURM_COMMAND = 'sbatch --mail-user=nsfabina@asu.edu --nodes=1 --cpus-per-task=1 --ntasks=1 --mem-per-cpu=20000 '
SLURM_GPUS = '--partition gpu --gres=gpu:1 --qos=wildfire '
SLURM_GPUS_LARGE = SLURM_GPUS + '--constraint="V100_32" '

VALID_LABELS_EXPERIMENTS = (
    # UQ data
    'originals',
    'downsample_25',
    'downsample_50',
    'downsample_50_aug'
    # MP data
    'millennium_25_aug',
    'millennium_50_aug'
)
VALID_RESPONSE_MAPPINGS = ('lwr', 'lwrn', 'custom')


def get_classify_job_name(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return 'classify_' + config_name + '_' + label_experiment + '_' + response_mapping


def get_calval_apply_job_name(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return 'applycalval_' + config_name + '_' + label_experiment + '_' + response_mapping


def get_calval_calculate_job_name(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return 'calcstats_' + config_name + '_' + label_experiment + '_' + response_mapping


def get_global_apply_job_name(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return 'applyglobal_' + config_name + '_' + label_experiment + '_' + response_mapping


def get_all_config_filenames():
    return [
        filename for filename in os.listdir(paths.DIR_CONFIGS) if
        filename.endswith('yaml') and 'template' not in filename and not filename.startswith('build_only')
    ]


def get_relevant_config_filenames(
        config_names: List[str],
        build_only: bool = False,
        config_regex: str = None
) -> List[str]:
    if build_only:
        # Only return configs with "build_only" in name
        filename_configs = [filename for filename in os.listdir(paths.DIR_CONFIGS) if filename.startswith('build_only')]
    elif config_names:
        filename_configs = [config_name + '.yaml' for config_name in config_names]
    else:
        filename_configs = get_all_config_filenames()
    if config_regex:
        filename_configs = [filename for filename in filename_configs if re.search(config_regex, filename)]
    return filename_configs


def validate_label_experiment(label_experiment: str) -> None:
    assert label_experiment in VALID_LABELS_EXPERIMENTS, \
        'Label experiment "{}" is not in valid experiment labels: {}'.format(label_experiment, VALID_LABELS_EXPERIMENTS)


def validate_response_mapping(response_mapping: str) -> None:
    assert response_mapping in VALID_RESPONSE_MAPPINGS, \
        'Response mapping "{}" is not in valid response mappings: {}'.format(response_mapping, VALID_RESPONSE_MAPPINGS)
