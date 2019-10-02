import argparse
import os
import shlex
import subprocess

from bfgn.configuration import configs

from gcrmnbc.utils import paths, shared_submit_slurm


SLURM_COMMAND_CLASSIFY = \
    '--mail-type=END,FAIL --time=8:00:00 --wrap ' + \
    '"python run_classification.py --config_name={config_name} --label_experiment={label_experiment} ' + \
    '--response_mapping={response_mapping} {build_only}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names', type=str)
    parser.add_argument('--config_regex', type=str)
    parser.add_argument('--label_experiment', type=str, required=True)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--build_only', action='store_true')
    args = parser.parse_args()

    # Warning about usage and error checks
    if args.build_only and args.config_names:
        print('WARNING:  build_only takes precedence over config_names, which is ignored')

    config_names = None
    if args.config_names:
        config_names = args.config_names.split(',')
    filename_configs = shared_submit_slurm.get_relevant_config_filenames(
        config_names, args.build_only, args.config_regex)

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            config = configs.create_config_from_file(paths.get_filepath_config(config_name))
            job_name = shared_submit_slurm.get_classify_job_name(config_name, args.label_experiment, response_mapping)

            # Create model directory
            dir_model = paths.get_dir_model_experiment_config(args.label_experiment, response_mapping, config)
            if not os.path.exists(dir_model):
                os.makedirs(dir_model)

            # Do not submit if classification is locked or complete
            filepath_complete = paths.get_filepath_classify_complete(args.label_experiment, response_mapping, config)
            filepath_lock = paths.get_filepath_classify_lock(args.label_experiment, response_mapping, config)
            command = 'squeue -u nfabina -o %j'
            result = subprocess.run(shlex.split(command), capture_output=True)
            is_in_job_queue = job_name in result.stdout.decode('utf-8')
            if os.path.exists(filepath_lock):
                if is_in_job_queue:
                    print('Classification in progress:  {} {}'.format(config_name, response_mapping))
                    continue
                else:
                    os.remove(filepath_lock)
            if os.path.exists(filepath_complete):
                print('Classification complete:  {} {}'.format(config_name, response_mapping))
                continue

            # Set dynamic SLURM arguments
            slurm_args_dynamic = ' '.join([
                '' if args.build_only else shared_submit_slurm.SLURM_GPUS,
                '--job-name={}'.format(job_name),
                '--output={}/slurm.classify.%j.%t.OUT'.format(dir_model),
                '--error={}/slurm.classify.%j.%t.ERROR'.format(dir_model),
            ])

            # Set dynamic python arguments
            slurm_python_wrap = SLURM_COMMAND_CLASSIFY.format(
                config_name=config_name, label_experiment=args.label_experiment, response_mapping=response_mapping,
                build_only='--build_only' if args.build_only else ''
            )

            print('Submitting job {}'.format(job_name))
            command = ' '.join([shared_submit_slurm.SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
            # print(command)
            subprocess.call(command, shell=True)
