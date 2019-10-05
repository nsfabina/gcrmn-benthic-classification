import argparse
import os
import subprocess

from gcrmnbc.utils import paths, shared_configs, shared_submit_slurm


SLURM_COMMAND_APPLY = \
    '--mail-type=FAIL --time=2:00:00 --chdir={dir_working} --wrap "python run_calval_application.py ' + \
    '--config_name={config_name} --label_experiment={label_experiment} --response_mapping={response_mapping} ' + \
    '{run_all}"'


def submit_application_slurm(
        labels_experiments: str,
        response_mappings: str,
        num_jobs: int,
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
                config = shared_configs.build_dynamic_config(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                job_name = shared_submit_slurm.get_calval_apply_job_name(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)

                # Do not submit jobs that do not have trained models or are already complete
                filepath_class = paths.get_filepath_classify_complete(
                    label_experiment=label_experiment, response_mapping=response_mapping, config=config)
                filepath_appli = paths.get_filepath_calval_apply_complete(
                    label_experiment=label_experiment, response_mapping=response_mapping, config=config)
                if not os.path.exists(filepath_class):
                    print('Classification not complete:  {} {}'.format(config_name, response_mapping))
                    continue
                if os.path.exists(filepath_appli):
                    print('Application complete:  {} {}'.format(config_name, response_mapping))
                    continue

                # Set dynamic SLURM arguments
                dir_model = paths.get_dir_model_experiment_config(
                    label_experiment=label_experiment, response_mapping=response_mapping, config=config)
                slurm_args_dynamic = ' '.join([
                    shared_submit_slurm.SLURM_GPUS,
                    '--job-name={}'.format(job_name),
                    '--output={}/slurm.apply_calval.%j.%t.OUT'.format(dir_model),
                    '--error={}/slurm.apply_calval.%j.%t.ERROR'.format(dir_model),
                ])

                # Set dynamic python arguments
                dir_working = os.path.dirname(os.path.abspath(__file__))
                slurm_python_wrap = SLURM_COMMAND_APPLY.format(
                    dir_working=dir_working, config_name=config_name, label_experiment=label_experiment,
                    response_mapping=response_mapping, run_all='--run_all' if run_all else ''
                )
                print('Submitting job {}'.format(job_name))
                command = ' '.join([shared_submit_slurm.SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
                # print(command)
                for idx_job in range(num_jobs):
                    subprocess.call(command, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names')
    parser.add_argument('--config_regex')
    parser.add_argument('--labels_experiments', required=True)
    parser.add_argument('--response_mappings', required=True)
    parser.add_argument('--num_jobs', type=int, required=True)
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    submit_application_slurm(**args)
