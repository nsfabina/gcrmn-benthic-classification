import argparse
import subprocess

from gcrmnbc.utils import paths, shared_submit_slurm


SLURM_COMMAND_APPLY = \
    '--mail-type=END,FAIL --time=24:00:00 --wrap "python run_global_application.py --config_name={config_name} ' + \
    '--label_experiment={label_experiment} --response_mapping={response_mapping} --model_version={model_version}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--model_version', required=True)
    parser.add_argument('--num_jobs', type=int, required=True)
    args = parser.parse_args()

    # Prep for calling jobs
    shared_submit_slurm.validate_label_experiment(args.label_experiment)
    shared_submit_slurm.validate_response_mapping(args.response_mapping)
    dir_model = paths.get_dir_model_experiment_config(
        config_name=args.config_name, label_experiment=args.label_experiment, response_mapping=args.response_mapping)
    slurm_python_wrap = SLURM_COMMAND_APPLY.format(
        config_name=args.config_name, label_experiment=args.label_experiment, response_mapping=args.response_mapping,
        mdoel_version=args.model_version
    )

    for idx_job in range(args.num_jobs):
        job_name = shared_submit_slurm.get_global_apply_job_name(
            config_name=args.config_name, label_experiment=args.label_experiment,
            response_mapping=args.response_mapping
        )
        slurm_args_dynamic = ' '.join([
            shared_submit_slurm.SLURM_GPUS,
            '--job-name={}'.format(job_name),
            '--output={}/slurm.global_apply.%j.%t.OUT'.format(dir_model),
            '--error={}/slurm.global_apply.%j.%t.ERROR'.format(dir_model),
        ])

        print('Submitting job {}'.format(job_name))
        command = ' '.join([shared_submit_slurm.SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
        subprocess.call(command, shell=True)
