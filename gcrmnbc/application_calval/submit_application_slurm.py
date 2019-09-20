import argparse
import os
import subprocess

from gcrmnbc.utils.shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS


DIR_CONFIGS = '../configs'
DIR_MODELS = '../models'
SLURM_COMMAND_WRAP = '--wrap "python run_application.py --config_names={} --response_mapping={} "'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names', type=str)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--num_jobs', type=int, required=True)
    args = parser.parse_args()

    # Prep commands
    slurm_command = SLURM_COMMAND + SLURM_GPUS

    # Get relevant configs, only get one config per window radius if building
    if args.config_names:
        filename_configs = [os.path.basename(filepath) for filepath in args.config_names.split(',')]
    else:
        filename_configs = [
            filename for filename in os.listdir(DIR_CONFIGS) if
            filename.endswith('yaml') and filename != 'config_template.yaml' and not filename.startswith('build_only')
        ]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            job_name = 'apply_' + config_name + '_' + response_mapping

            # Set dynamic SLURM arguments
            dir_model = os.path.join(DIR_MODELS, config_name, response_mapping)
            slurm_args_dynamic = ' '.join([
                '--job-name={}'.format(job_name),
                '--output={}/slurm.classify.%j.%t.OUT'.format(dir_model),
                '--error={}/slurm.classify.%j.%t.ERROR'.format(dir_model),
            ])

            # Set dynamic python arguments
            slurm_python_wrap = SLURM_COMMAND_WRAP.format(config_name, response_mapping)

            print('Submitting job {}'.format(job_name))
            command = ' '.join([slurm_command, slurm_args_dynamic, slurm_python_wrap])
            # print(command)
            for idx_job in range(args.num_jobs):
                subprocess.call(command, shell=True)
