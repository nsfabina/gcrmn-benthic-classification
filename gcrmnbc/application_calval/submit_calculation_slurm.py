import argparse
import os
import subprocess


DIR_CONFIGS = '../configs'
DIR_MODELS = '../models'
DIR_APPLIED_DEST = '/scratch/nfabina/gcrmn-benthic-classification/applied_data'

FILENAME_APPL_COMPLETE = 'calval_application.complete'
FILENAME_STATS_OUT = 'asu_statistics.json'
FILENAME_FIG_OUT = 'asu_statistics.pdf'

SLURM_COMMAND = 'sbatch --mail-user=nfabina@asu.edu --mail-type=END,FAIL --time=4:00:00 ' + \
                '--nodes=1 --cpus-per-task=1 --mem-per-cpu=20000 --ntasks=1 ' + \
                '--wrap "python calculate_asu_statistics.py --config_name={} --response_mapping={}" {}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--response_mappings', type=str, required=True)
    parser.add_argument('--recalculate', action='store_true')
    args = parser.parse_args()

    # Get configs
    filename_configs = [
        filename for filename in os.listdir(DIR_CONFIGS) if
        filename.endswith('yaml') and filename != 'config_template.yaml' and not filename.startswith('build_only')
    ]

    # Loop through configs and submit jobs
    for filename_config in filename_configs:
        for response_mapping in args.response_mappings.split(','):
            config_name = os.path.splitext(filename_config)[0]
            job_name = 'calc_stats_' + config_name + '_' + response_mapping

            # Do not submit jobs that do not have application data or are already complete
            filepath_appli = os.path.join(DIR_APPLIED_DEST, config_name, response_mapping, FILENAME_APPL_COMPLETE)
            filepath_stats = os.path.join(DIR_APPLIED_DEST, config_name, response_mapping, FILENAME_STATS_OUT)
            filepath_report = os.path.join(DIR_APPLIED_DEST, config_name, response_mapping, FILENAME_FIG_OUT)
            if not os.path.exists(filepath_appli):
                print('Application not complete:  {} {}'.format(config_name, response_mapping))
                continue
            if os.path.exists(filepath_stats) and os.path.exists(filepath_report):
                print('Stats complete:  {} {}'.format(config_name, response_mapping))
                continue

            # Set dynamic SLURM arguments
            slurm_command = SLURM_COMMAND.format(
                config_name, response_mapping, '--recalculate' if args.recalculate else '')
            dir_model = os.path.join(DIR_MODELS, config_name, response_mapping)
            slurm_args_dynamic = ' '.join([
                '--job-name={}'.format(job_name),
                '--output={}/slurm.calc_stats.%j.%t.OUT'.format(dir_model),
                '--error={}/slurm.calc_stats.%j.%t.ERROR'.format(dir_model),
            ])

            print('Submitting job {}'.format(job_name))
            command = ' '.join([slurm_command, slurm_args_dynamic])
            # print(command)
            subprocess.call(command, shell=True)
