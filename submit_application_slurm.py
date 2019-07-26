import argparse
import os
import subprocess

from shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS


SLURM_COMMAND_WRAP = '--wrap "python run_application.py --target={} --config_name={} --response_mapping={} "'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--config_name', type=str, required=True)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--num_jobs', type=int, required=True)
    args = parser.parse_args()

    # Prep commands
    slurm_command = SLURM_COMMAND + SLURM_GPUS

    # Loop through parameters and submit jobs
    for response_mapping in args.response_mappings.split(','):
        job_name = 'apply' + '_' + args.config_name + '_' + response_mapping

        # Set dynamic SLURM arguments
        dir_model = os.path.join('models', args.config_name, response_mapping)
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.apply.%j.%t.OUT'.format(dir_model),
            '--error={}/slurm.apply.%j.%t.ERROR'.format(dir_model),
        ])

        # Set dynamic python arguments
        slurm_python_wrap = SLURM_COMMAND_WRAP.format(args.target, args.config_name, response_mapping)

        print('Submitting job {}'.format(job_name))
        command = ' '.join([slurm_command, slurm_args_dynamic, slurm_python_wrap])
        # print(command)
        for idx_job in range(args.num_jobs):
            subprocess.call(command, shell=True)
