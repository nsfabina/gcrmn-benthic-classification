import argparse
import os
import re
import subprocess

from gcrmnbc.utils.shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS


DIR_CONFIGS = '../configs'
DIR_MODELS = '../models'
FILENAME_LOCK = 'classify.lock'
FILENAME_SUCCESS = 'classify.complete'
SLURM_COMMAND_CLASSIFY = \
    '--mail-type=END,FAIL --time=24:00:00 --wrap ' + \
    '"python run_classification_downsample_experiment.py --config_name={} --response_mapping={} --downsample_pct {} {}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names', type=str)
    parser.add_argument('--config_regex', type=str)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--downsample_pct', type=int, required=True)
    parser.add_argument('--build_only', action='store_true')
    args = parser.parse_args()

    # Warning about usage and error checks
    if args.build_only and args.config_names:
        print('WARNING:  build_only takes precedence over config_names, which is ignored')

    # Get relevant configs, only get one config per window radius if building
    if args.build_only:
        filename_configs = [filename for filename in os.listdir(DIR_CONFIGS) if filename.startswith('build_only')]
    elif args.config_names:
        filename_configs = [os.path.basename(filepath) for filepath in args.config_names.split(',')]
    else:
        filename_configs = [
            filename for filename in os.listdir(DIR_CONFIGS) if filename.endswith('yaml')
            and filename != 'config_template.yaml' and not filename.startswith('build_only')
        ]
        if args.config_regex:
            filename_configs = [filename for filename in filename_configs if re.search(args.config_regex, filename)]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            job_name = 'classify_' + config_name + '_' + response_mapping

            # Create model directory
            dir_model = os.path.join(DIR_MODELS, config_name, 'downsample_{}'.format(args.downsample_pct))
            if not os.path.exists(dir_model):
                os.makedirs(dir_model)

            # Do not submit if classification is locked or complete
            filepath_complete = os.path.join(dir_model, FILENAME_SUCCESS)
            filepath_lock = os.path.join(dir_model, FILENAME_LOCK)
            if os.path.exists(filepath_lock):
                print('Classification in progress:  {} {}'.format(config_name, response_mapping))
                continue
            if os.path.exists(filepath_complete):
                print('Classification complete:  {} {}'.format(config_name, response_mapping))
                continue

            # Set dynamic SLURM arguments
            if args.build_only:
                gpu_constraint = ''
            else:
                gpu_constraint = SLURM_GPUS
            slurm_args_dynamic = ' '.join([
                gpu_constraint,
                '--job-name={}'.format(job_name),
                '--output={}/slurm.classify.%j.%t.OUT'.format(dir_model),
                '--error={}/slurm.classify.%j.%t.ERROR'.format(dir_model),
            ])

            # Set dynamic python arguments
            slurm_python_wrap = SLURM_COMMAND_CLASSIFY.format(
                config_name, response_mapping, '--build_only' if args.build_only else '')

            print('Submitting job {}'.format(job_name))
            command = ' '.join([SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
            # print(command)
            subprocess.call(command, shell=True)
