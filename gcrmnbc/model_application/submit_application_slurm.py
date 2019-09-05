import argparse
import os
import subprocess

from gcrmnbc.utils.shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS


SLURM_COMMAND_WRAP = '--wrap "python run_application.py --config_name={} --response_mapping={} --version_map={} "'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', type=str, required=True)
    parser.add_argument('--response_mapping', type=str, required=True)
    parser.add_argument('--version_map', type=str, required=True)
    parser.add_argument('--num_jobs', type=int, required=True)
    args = parser.parse_args()

    # Prep for calling jobs
    dir_model = os.path.join('../models', args.config_name, args.response_mapping)
    slurm_command = SLURM_COMMAND + SLURM_GPUS
    slurm_python_wrap = SLURM_COMMAND_WRAP.format(args.config_name, args.response_mapping, args.version_map)

    for idx_job in range(args.num_jobs):
        job_name = 'apply_' + args.config_name + '_' + args.response_mapping + '_' + str(idx_job)
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.apply.%j.%t.OUT'.format(dir_model),
            '--error={}/slurm.apply.%j.%t.ERROR'.format(dir_model),
        ])

        print('Submitting job {}'.format(job_name))
        command = ' '.join([slurm_command, slurm_args_dynamic, slurm_python_wrap])
        subprocess.call(command, shell=True)
