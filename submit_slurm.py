import argparse
import os
import re
import subprocess


SLURM_COMMAND = 'sbatch --mail-type=END,FAIL --mail-user=nsfabina@asu.edu --time=24:00:00 ' + \
                '--nodes=1 --cpus-per-task=1 --mem-per-cpu=20000 --ntasks=1 '
SLURM_GPUS = '--qos=wildfire --gres=gpu:1 --partition=mrlinegpu1,rcgpu1 '
SLURM_COMMAND_WRAP = '--wrap "python run_classification.py --filepath_config=configs/{} --response_mapping={} --operations={}"'

_OPERATION_BUILD = 'build'
_OPERATION_CLASSIFY = 'classify'
_OPERATION_APPLY = 'apply'
_OPERATION_ALL = 'all'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--response_mappings', type=str, dest='response_mappings', required=True)
    parser.add_argument('--operations', type=str, dest='operations', required=True)
    parser.add_argument('--filepath_configs', type=str, dest='filepath_config')
    parser.add_argument('-f', dest='rerun', action='store_true')
    args = parser.parse_args()

    # Prep commands
    slurm_command = SLURM_COMMAND
    if args.operations in (_OPERATION_CLASSIFY, _OPERATION_APPLY, _OPERATION_ALL):
        slurm_command += SLURM_GPUS

    # Get relevant configs, only get one config per built data type if building
    if args.filepath_config:
        filename_configs = [os.path.basename(filepath) for filepath in args.filepath_configs.split(',')]
    else:
        filename_configs = [filename for filename in os.listdir('configs')
                            if filename.endswith('yaml') and filename != 'config_template.yaml']
        if args.operations == 'build':
            filename_configs = [filename for filename in filename_configs if re.search(r'^unet_\d+_2.yaml', filename)]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            job_name = config_name + '_' + args.response_mapping

            # Create model directory or confirm we want to rerun if already exists
            dir_model = os.path.join('models', config_name, args.response_mapping)
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
            command = ' '.join([slurm_command, slurm_args_dynamic, slurm_python_wrap])
            subprocess.call(command, shell=True)
