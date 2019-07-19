import argparse
import os
import subprocess

from shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS


SLURM_COMMAND_WRAP = '--wrap "python run_classification.py --filepath_config=configs/{} --response_mapping={} {}"'


if __name__ == '__main__':
    # TODO:  add number of jobs per mapping
    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath_config', type=str)
    parser.add_argument('--response_mappings', type=str, required=True)
    args = parser.parse_args()

    # Prep commands
    slurm_command = SLURM_COMMAND + SLURM_GPUS

    # Loop through parameters and submit jobs
    for response_mapping in args.response_mappings.split(','):
        config_name = os.path.splitext(os.path.basename(args.filepath_config))[0]
        job_name = 'apply' + '_' + config_name + '_' + response_mapping

        # Create output directory
        dir_model = os.path.join('models', config_name, response_mapping)

        # Set dynamic SLURM arguments
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.apply.%j.%t.OUT'.format(dir_model),
            '--error={}/slurm.apply.%j.%t.ERROR'.format(dir_model),
        ])

        # Set dynamic python arguments
        slurm_python_wrap = SLURM_COMMAND_WRAP.format(args.filepath_config, response_mapping)

        print('Submitting job {}'.format(job_name))
        command = ' '.join([slurm_command, slurm_args_dynamic, slurm_python_wrap])
        # print(command)
        subprocess.call(command, shell=True)
