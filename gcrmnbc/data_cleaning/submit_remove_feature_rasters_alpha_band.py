import os
import subprocess


SLURM_COMMAND = \
    'sbatch --mail-user=nfabina@asu.edu --mail-type=FAIL --time=2:00:00 --nodes=1 --cpus-per-task=1 ' + \
    '--ntasks=1 --wrap "python remove_feature_rasters_alpha_band.py" '


def submit_remove_feature_rasters_alpha_band() -> None:
    for idx_job in range(50):
        job_name = 'remove_alpha_bands_{}'.format(idx_job)
        dir_logs = 'remove_alpha_bands'
        if not os.path.exists(dir_logs):
            os.makedirs(dir_logs)
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
    submit_remove_feature_rasters_alpha_band()
