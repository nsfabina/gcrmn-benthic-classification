import os
import subprocess


SLURM_COMMAND = \
    'sbatch --mail-user=nfabina@asu.edu --mail-type=FAIL --time=2:00:00 --nodes=1 --cpus-per-task=1 ' + \
    '--ntasks=1 --wrap "python downsample_feature_response_rasters.py" '


def submit_downsample_feature_response_rasters() -> None:
    dir_logs = 'downsample_feature_response_rasters'
    if not os.path.exists(dir_logs):
        os.makedirs(dir_logs)
    for idx_job in range(10):
        job_name = 'submit_downsample_feature_response_rasters_{}'.format(idx_job)
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
    submit_downsample_feature_response_rasters()
