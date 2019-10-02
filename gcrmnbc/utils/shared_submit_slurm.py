import os
import re
from typing import List

from gcrmnbc.utils import paths


SLURM_COMMAND = 'sbatch --mail-user=nsfabina@asu.edu --nodes=1 --cpus-per-task=1 --ntasks=1 --mem-per-cpu=20000 '
SLURM_GPUS = '--partition gpu --gres=gpu:1 --qos=wildfire '
SLURM_GPUS_LARGE = SLURM_GPUS + '--constraint="V100_32" '


def get_classify_job_name(config_name: str, label_experiment: str, response_mapping: str) -> str:
    return 'classify_' + config_name + '_' + label_experiment + '_' + response_mapping


def get_relevant_config_filenames(config_names: List[str], build_only: bool, config_regex: str = None) -> List[str]:
    if build_only:
        # Only return configs with "build_only" in name
        filename_configs = [filename for filename in os.listdir(paths.DIR_CONFIGS) if filename.startswith('build_only')]
    elif config_names:
        filename_configs = [os.path.basename(filepath) for filepath in config_names]
    else:
        filename_configs = [
            filename for filename in os.listdir(paths.DIR_CONFIGS)
            if filename.endswith('yaml')
            and filename != 'config_template.yaml'
            and not filename.startswith('build_only')
        ]
    if config_regex:
        filename_configs = [filename for filename in filename_configs if re.search(config_regex, filename)]
    return filename_configs
