import os
import subprocess


SLURM_COMMAND = \
    'sbatch --mail-user=nfabina@asu.edu --mail-type=FAIL --time=10:00:00 --nodes=1 --cpus-per-task=1 ' + \
    '--mem=50000 --ntasks=1 --wrap "python reproject_landsat_rasters.py" '


def submit_reproject_landsat_rasters() -> None:
    dir_logs = 'reproject_landsat_rasters'
    if not os.path.exists(dir_logs):
        os.makedirs(dir_logs)
    for idx_job in range(20):
        job_name = 'reproject_landsat_rasters_{}'.format(idx_job)
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.%j.%t.OUT'.format(dir_logs),
            '--error={}/slurm.%j.%t.ERROR'.format(dir_logs),
        ])
        print('Submitting job {}'.format(job_name))
        command = ' '.join([SLURM_COMMAND, slurm_args_dynamic])
        # print(command)
        subprocess.call(command, shell=True)


if __name__ == '__main__':
    submit_reproject_landsat_rasters()
