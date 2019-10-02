import argparse
import os
import shlex
import subprocess

from bfgn.configuration import configs

from gcrmnbc.utils import paths, shared_submit_slurm


SLURM_COMMAND_CLASSIFY = \
    '--mail-type=END,FAIL --time=8:00:00 --wrap ' + \
    '"python run_classification.py --config_name={} --label_experiment={} --response_mapping={} {}"'


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

    filename_configs = shared_submit_slurm.get_relevant_config_filenames(
        args.config_names.split(','), args.build_only, args.config_regex)

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
            command = 'squeue -u nfabina -o %j | grep ${}'.format(job_name)
            result = subprocess.run(shlex.split(command), capture_output=True)
            print(result.stdout)
            print(result.stderr)
            raise AssertionError('Check the STDOUT to see the response, remove locks if necessary and remove this')
            is_in_job_queue = True  # TODO
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
                config_name, args.label_experiment, response_mapping, '--build_only' if args.build_only else '')

            print('Submitting job {}'.format(job_name))
            command = ' '.join([shared_submit_slurm.SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
            # print(command)
            subprocess.call(command, shell=True)
