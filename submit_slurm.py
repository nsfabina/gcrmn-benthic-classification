import argparse
import os
import re
import subprocess


SLURM_COMMAND = 'sbatch --mail-type=END,FAIL --mail-user=nsfabina@asu.edu --qos=wildfire --time=24:00:00 ' + \
                '--nodes=1 --cpus-per-task=1 --mem-per-cpu=40000 --gres=gpu:1 --ntasks=1 ' + \
                '--partition=mrlinegpu1,rcgpu1 '

SLURM_COMMAND_WRAP = '--wrap "python classify.py --filepath_config=configs/{} --response_mapping={} --operations={}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--response_mapping', dest='response_mapping', required=True)
    parser.add_argument('--operations', dest='operations', required=True)
    parser.add_argument('-f', dest='rerun', action='store_true')
    args = parser.parse_args()

    # Get relevant configs, only get one config per built data type if building
    filename_configs = [filename for filename in os.listdir('configs')
                        if filename.endswith('yaml') and filename != 'config_template.yaml']
    if args.operations == 'build':
        filename_configs = [filename for filename in filename_configs if re.search('unet_\d+_2.yaml', filename)]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        job_name = os.path.splitext(filename_config)[0]

        # Create model directory or confirm we want to rerun if already exists
        dir_model = os.path.join('models', job_name)
        if not os.path.exists(dir_model):
            os.makedirs(dir_model)
        elif not args.rerun:
            print('Job {} already submitted, not resubmitting'.format(job_name))
            continue

        # Set dynamic SLURM arguments
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.%j.%t.OUT'.format(dir_model),
            '--error={}/slurm.%j.%t.ERROR'.format(dir_model),
        ])

        # Set dynamic python arguments
        slurm_python_wrap = SLURM_COMMAND_WRAP.format(filename_config, args.response_mapping, args.operations)

        print('Submitting job {}'.format(job_name))
        command = ' '.join([SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
        subprocess.call(command, shell=True)
