import argparse
import os
import subprocess

from shared_submit_slurm import SLURM_COMMAND, SLURM_GPUS


SLURM_COMMAND_WRAP = '--wrap "python run_classification.py --config_names={} --response_mapping={} {}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names', type=str)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--build_only', action='store_true')
    args = parser.parse_args()

    # Warning about usage and error checks
    if args.build_only and args.config_names:
        print('WARNING:  build_only takes precedence over config_names, which is ignored')

    # Prep commands
    slurm_command = SLURM_COMMAND
    if not args.build_only:
        slurm_command += SLURM_GPUS

    # Get relevant configs, only get one config per window radius if building
    if args.build_only:
        filename_configs = [filename for filename in os.listdir('configs') if filename.startswith('build_only')]
    elif args.config_names:
        filename_configs = [os.path.basename(filepath) for filepath in args.config_names.split(',')]
    else:
        filename_configs = [
            filename for filename in os.listdir('configs') if filename.endswith('yaml')
            and filename != 'config_template.yaml' and not filename.startswith('build_only')
        ]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            job_name = config_name + '_' + response_mapping

            # Create model directory
            dir_model = os.path.join('models', config_name, response_mapping)
            if not os.path.exists(dir_model):
                os.makedirs(dir_model)

            # Set dynamic SLURM arguments
            slurm_args_dynamic = ' '.join([
                '--job-name={}'.format(job_name),
                '--output={}/slurm.classify.%j.%t.OUT'.format(dir_model),
                '--error={}/slurm.classify.%j.%t.ERROR'.format(dir_model),
            ])

            # Set dynamic python arguments
            slurm_python_wrap = SLURM_COMMAND_WRAP.format(
                config_name, response_mapping, '--build_only' if args.build_only else '')

            print('Submitting job {}'.format(job_name))
            command = ' '.join([slurm_command, slurm_args_dynamic, slurm_python_wrap])
            # print(command)
            subprocess.call(command, shell=True)
