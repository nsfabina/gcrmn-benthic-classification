import argparse
import os
import re
import subprocess

from gcrmnbc.application_calval.run_calval_application import DIR_APPLIED_DEST, FILENAME_COMPLETE
from gcrmnbc.model_training.run_classification import FILENAME_COMPLETE as FILENAME_CLASSIFICATION_COMPLETE
from gcrmnbc.utils.shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS, SLURM_GPUS_LARGE


DIR_CONFIGS = '../configs'
DIR_MODELS = '../models'
SLURM_COMMAND_APPLY = '--mail-type=END,FAIL --time=2:00:00 ' + \
                      '--wrap "python run_calval_application.py --config_name={} --response_mapping={}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names', type=str)
    parser.add_argument('--config_regex', type=str)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--num_jobs', type=int, required=True)
    args = parser.parse_args()
    # Get relevant configs, only get one config per window radius if building
    if args.config_names:
        filename_configs = [os.path.basename(filepath) for filepath in args.config_names.split(',')]
    else:
        filename_configs = [
            filename for filename in os.listdir(DIR_CONFIGS) if
            filename.endswith('yaml') and filename != 'config_template.yaml' and not filename.startswith('build_only')
        ]
        if args.config_regex:
            filename_configs = [filename for filename in filename_configs if re.search(args.config_regex, filename)]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            job_name = 'apply_calval_' + config_name + '_' + response_mapping

            # Do not submit jobs that do not have trained models or are already complete
            filepath_class = os.path.join(DIR_MODELS, config_name, response_mapping, FILENAME_CLASSIFICATION_COMPLETE)
            filepath_appli = os.path.join(DIR_APPLIED_DEST, config_name, response_mapping, FILENAME_COMPLETE)
            if not os.path.exists(filepath_class):
                print('Classification not complete:  {} {}'.format(config_name, response_mapping))
                continue
            if os.path.exists(filepath_appli):
                print('Application complete:  {} {}'.format(config_name, response_mapping))
                continue

            # Set dynamic SLURM arguments
            dir_model = os.path.join(DIR_MODELS, config_name, response_mapping)
            slurm_args_dynamic = ' '.join([
                SLURM_GPUS if '256' not in config_name else SLURM_GPUS_LARGE,
                '--job-name={}'.format(job_name),
                '--output={}/slurm.apply_calval.%j.%t.OUT'.format(dir_model),
                '--error={}/slurm.apply_calval.%j.%t.ERROR'.format(dir_model),
            ])

            # Set dynamic python arguments
            slurm_python_wrap = SLURM_COMMAND_APPLY.format(config_name, response_mapping)

            print('Submitting job {}'.format(job_name))
            command = ' '.join([SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
            # print(command)
            for idx_job in range(args.num_jobs):
                subprocess.call(command, shell=True)
