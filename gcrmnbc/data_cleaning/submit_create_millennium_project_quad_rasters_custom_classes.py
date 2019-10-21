import os
import subprocess


SLURM_COMMAND = \
    'sbatch --mail-user=nfabina@asu.edu --mail-type=FAIL --time=2:00:00 --nodes=1 --cpus-per-task=1 ' + \
    '--ntasks=1 --wrap "python create_millennium_project_quad_rasters_custom_classes.py" '


def submit_create_millennium_project_quad_rasters_custom_classes() -> None:
    dir_logs = 'create_millennium_project_quad_rasters_custom_classes'
    if not os.path.exists(dir_logs):
        os.makedirs(dir_logs)
    for idx_job in range(10):
        job_name = 'create_custom_rasters_{}'.format(idx_job)
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
    submit_create_millennium_project_quad_rasters_custom_classes()
