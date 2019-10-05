import argparse
import os
import shlex
import subprocess

from gcrmnbc.utils import paths, shared_configs, shared_submit_slurm


SLURM_COMMAND = \
    'sbatch --mail-user=nfabina@asu.edu --mail-type=END,FAIL --time=2:00:00 --nodes=1 --cpus-per-task=1 ' + \
    '--mem-per-cpu=20000 --ntasks=1 --dir_working={dir_working} --wrap "python calculate_asu_statistics.py ' + \
    '--config_name={config_name} --label_experiment={label_experiment} --response_mapping={response_mapping} ' + \
    '{recalculate}"'


def submit_calculation_slurm(
        labels_experiments: str,
        response_mappings: str,
        recalculate: bool = False,
) -> None:
    # Get configs
    filename_configs = shared_submit_slurm.get_all_config_filenames()

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for label_experiment in labels_experiments.split(','):
            for response_mapping in response_mappings.split(','):
                shared_submit_slurm.validate_label_experiment(label_experiment)
                shared_submit_slurm.validate_response_mapping(response_mapping)

                config_name = os.path.splitext(filename_config)[0]
                config = shared_configs.build_dynamic_config(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
                job_name = shared_submit_slurm.get_calval_calculate_job_name(
                    config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)

                # Do not submit jobs that do not have application data, are already complete, or are already submitted
                dir_results = paths.get_dir_calval_data_experiment_config(
                    label_experiment=label_experiment, response_mapping=response_mapping, config=config)
                filepath_apply_complete = os.path.join(dir_results, paths.FILENAME_APPLY_CALVAL_COMPLETE)
                filepath_stats = os.path.join(dir_results, paths.FILENAME_CALVAL_STATS)
                filepath_report = os.path.join(dir_results, paths.FILENAME_CALVAL_FIGS)
                command = 'squeue -u nfabina -o %j'
                result = subprocess.run(shlex.split(command), capture_output=True)
                is_in_job_queue = job_name in result.stdout.decode('utf-8')

                if not os.path.exists(filepath_apply_complete):
                    print('Application not complete:  {} {} {}'.format(config_name, label_experiment, response_mapping))
                    continue
                elif os.path.exists(filepath_stats) and os.path.exists(filepath_report):
                    print('Stats complete:  {} {} {}'.format(config_name, label_experiment, response_mapping))
                    continue
                elif is_in_job_queue:
                    print('Stats already submitted:  {} {}'.format(config_name, response_mapping))
                    continue

                # Set dynamic SLURM arguments
                dir_working = os.path.dirname(os.path.abspath(__file__))
                slurm_command = SLURM_COMMAND.format(
                    dir_working=dir_working, config_name=config_name, label_experiment=label_experiment,
                    response_mapping=response_mapping, recalculate='--recalculate' if recalculate else '')
                dir_model = paths.get_dir_model_experiment_config(
                    label_experiment=label_experiment, response_mapping=response_mapping, config=config)
                slurm_args_dynamic = ' '.join([
                    '--job-name={}'.format(job_name),
                    '--output={}/slurm.calc_stats.%j.%t.OUT'.format(dir_model),
                    '--error={}/slurm.calc_stats.%j.%t.ERROR'.format(dir_model),
                ])

                print('Submitting job {}'.format(job_name))
                command = ' '.join([slurm_command, slurm_args_dynamic])
                # print(command)
                subprocess.call(command, shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels_experiments', required=True)
    parser.add_argument('--response_mappings', required=True)
    parser.add_argument('--recalculate', action='store_true')
    args = vars(parser.parse_args())
    submit_calculation_slurm(**args)
