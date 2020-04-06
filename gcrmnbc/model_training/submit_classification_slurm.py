import argparse
import os
import shlex
import subprocess

from gcrmnbc.utils import paths, shared_submit_slurm


SLURM_COMMAND_CLASSIFY = \
    '--mail-type={mail_end}FAIL --time=72:00:00 --chdir={dir_working} --wrap ' + \
    '"python run_classification.py --config_name={config_name} --label_experiment={label_experiment} ' + \
    '--response_mapping={response_mapping} {build_only} {run_all}"'


def submit_classification_slurm(
        labels_experiments: str,
        response_mappings: str,
        config_names: str = None,
        config_regex: str = None,
        build_only: bool = False,
        run_all: bool = False
) -> None:
    # Warning about usage and error checks
    if build_only and config_names:
        print('WARNING:  build_only takes precedence over config_names, which is ignored')

    config_names = None
    if config_names:
        config_names = config_names.split(',')
    filename_configs = shared_submit_slurm.get_relevant_config_filenames(
        config_names, build_only, config_regex)

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for label_experiment in labels_experiments.split(','):
            for response_mapping in response_mappings.split(','):
                shared_submit_slurm.validate_label_experiment(label_experiment)
                shared_submit_slurm.validate_response_mapping(response_mapping)

                config_name = os.path.splitext(filename_config)[0]
                job_name = shared_submit_slurm.get_classify_job_name(config_name, label_experiment, response_mapping)

                # Create model directory
                dir_model = paths.get_dir_model_experiment_config(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                if not os.path.exists(dir_model):
                    os.makedirs(dir_model)

                # Do not submit if classification is locked or complete, or if data is built and build_only is True
                filepath_built = paths.get_filepath_build_complete(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                filepath_complete = paths.get_filepath_classify_complete(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                filepath_lock = paths.get_filepath_classify_lock(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                command = 'squeue -u nfabina -o %j'
                result = subprocess.run(shlex.split(command), capture_output=True)
                is_in_job_queue = job_name in result.stdout.decode('utf-8')
                if not is_in_job_queue and os.path.exists(filepath_lock):
                    os.remove(filepath_lock)
                if is_in_job_queue:
                    print('Classification in progress:  {} {} {}'.format(
                        config_name, label_experiment, response_mapping))
                    continue
                elif os.path.exists(filepath_complete):
                    print('Classification complete:  {} {} {}'.format(
                        config_name, label_experiment, response_mapping))
                    continue
                elif os.path.exists(filepath_built) and build_only:
                    print('Data build complete:  {} {} {}'.format(
                        config_name, label_experiment, response_mapping))
                    continue

                # Set dynamic SLURM arguments
                slurm_args_dynamic = ' '.join([
                    '' if build_only else shared_submit_slurm.SLURM_GPUS_LARGE,
                    '--job-name={}'.format(job_name),
                    '--output={}/slurm.classify.%j.%t.OUT'.format(dir_model),
                    '--error={}/slurm.classify.%j.%t.ERROR'.format(dir_model),
                ])
                # Set dynamic python arguments
                dir_working = os.path.dirname(os.path.abspath(__file__))
                slurm_python_wrap = SLURM_COMMAND_CLASSIFY.format(
                    mail_end='END,' if build_only else '', config_name=config_name, dir_working=dir_working,
                    label_experiment=label_experiment, response_mapping=response_mapping,
                    build_only='--build_only' if build_only else '', run_all='--run_all' if run_all else ''
                )

                print('Submitting job {}'.format(job_name))
                command = ' '.join([shared_submit_slurm.SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
                # print(command)
                subprocess.call(command, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names', type=str)
    parser.add_argument('--config_regex', type=str)
    parser.add_argument('--labels_experiments', type=str, required=True)
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--build_only', action='store_true')
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    submit_classification_slurm(**args)
