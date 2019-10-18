import os
import subprocess


SLURM_COMMAND = \
    'sbatch --mail-user=nfabina@asu.edu --mail-type=FAIL --time=2:00:00 --nodes=1 --cpus-per-task=1 ' + \
    '--ntasks=1 --wrap "python create_boundary_shapefiles_for_millennium_project_training_data.py" '


def submit_create_boundary_shapefiles_for_millennium_project_training_data() -> None:
    dir_logs = 'create_boundary_shapefiles'
    if not os.path.exists(dir_logs):
        os.makedirs(dir_logs)
    for idx_job in range(10):
        job_name = 'create_boundary_shapefiles_{}'.format(idx_job)
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.calc_stats.%j.%t.OUT'.format(dir_logs),
            '--error={}/slurm.calc_stats.%j.%t.ERROR'.format(dir_logs),
        ])
        print('Submitting job {}'.format(job_name))
        command = ' '.join([SLURM_COMMAND, slurm_args_dynamic])
        # print(command)
        subprocess.call(command, shell=True)


if __name__ == '__main__':
    submit_create_boundary_shapefiles_for_millennium_project_training_data()
