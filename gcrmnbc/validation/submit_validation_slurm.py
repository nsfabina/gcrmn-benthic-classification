import argparse
import os
import subprocess

from gcrmnbc.utils import paths, shared_submit_slurm


SLURM_COMMAND_VALIDATE = \
    '--mail-type=FAIL --time=2:00:00 --chdir={dir_working} --wrap "python run_validation.py ' + \
    '--config_name={config_name} --label_experiment={label_experiment} --response_mapping={response_mapping} ' + \
    '{run_all}"'


def submit_validation_slurm(
        labels_experiments: str,
        response_mappings: str,
        config_names: str = None,
        config_regex: str = None,
        run_all: bool = False
) -> None:
    # Get config filenames
    if config_names:
        config_names = config_names.split(',')
    filename_configs = shared_submit_slurm.get_relevant_config_filenames(
        config_names=config_names, build_only=False, config_regex=config_regex)

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for label_experiment in labels_experiments.split(','):
            for response_mapping in response_mappings.split(','):
                shared_submit_slurm.validate_label_experiment(label_experiment)
                shared_submit_slurm.validate_response_mapping(response_mapping)

                config_name = os.path.splitext(filename_config)[0]
                job_name = shared_submit_slurm.get_validation_job_name(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)

                # Do not submit jobs that do not have trained models or are already complete
                filepath_classify = paths.get_filepath_classify_complete(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                filepath_validate = paths.get_filepath_validation_complete(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                if not os.path.exists(filepath_classify):
                    print('Classification not complete:  {} {}'.format(config_name, response_mapping))
                    continue
                if os.path.exists(filepath_validate):
                    print('Validation complete:  {} {}'.format(config_name, response_mapping))
                    continue

                # Set dynamic SLURM arguments
                dir_model = paths.get_dir_model_experiment_config(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                slurm_args_dynamic = ' '.join([
                    shared_submit_slurm.SLURM_GPUS,
                    '--job-name={}'.format(job_name),
                    '--output={}/slurm.validate.%j.%t.OUT'.format(dir_model),
                    '--error={}/slurm.validate.%j.%t.ERROR'.format(dir_model),
                ])

                # Set dynamic python arguments
                dir_working = os.path.dirname(os.path.abspath(__file__))
                slurm_python_wrap = SLURM_COMMAND_VALIDATE.format(
                    dir_working=dir_working, config_name=config_name, label_experiment=label_experiment,
                    response_mapping=response_mapping, run_all='--run_all' if run_all else ''
                )
                print('Submitting job {}'.format(job_name))
                command = ' '.join([shared_submit_slurm.SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
                # print(command)
                subprocess.call(command, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names')
    parser.add_argument('--config_regex')
    parser.add_argument('--labels_experiments', required=True)
    parser.add_argument('--response_mappings', required=True)
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    submit_validation_slurm(**args)
