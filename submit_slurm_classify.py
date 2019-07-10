import argparse
import os
import subprocess


SLURM_COMMAND = 'sbatch --mail-type=END,FAIL --mail-user=nsfabina@asu.edu --qos=wildfire --time=24:00:00 ' + \
                '--nodes=1 --cpus-per-task=1 --mem-per-cpu=40000 --gres=gpu:1 --ntasks=1 ' + \
                '--partition=physicsgpu1,cidsegpu1,sulcgpu1,sulcgpu2,mrlinegpu1,asinghargpu1 '                

SLURM_COMMAND_WRAP = '--wrap "python classify.py --filepath_config=configs/{}"'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='rerun', action='store_true')
    args = parser.parse_args()

    filename_configs = ('unet.yaml', 'unet_growth.yaml', 'unet_mini.yaml', 'unet_mini_growth.yaml')
    for filename_config in filename_configs:
        job_name = os.path.splitext(filename_config)[0]
        dir_model = os.path.join('models', job_name)
        if not os.path.exists(dir_model):
            os.makedirs(dir_model)
        elif not args.rerun:
            print('Job {} already submitted, not resubmitting'.format(job_name))
            continue
        # Set dynamic SLURM arguments
        slurm_args_dynamic = ' '.join([
            '--job-name={}'.format(job_name),
            '--output={}/slurm.%j.%t.OUT'.format(dir_model),
            '--error={}/slurm.%j.%t.ERROR'.format(dir_model),
        ])
        print(slurm_args_dynamic)
        # Set dynamic python arguments
        slurm_python_wrap = SLURM_COMMAND_WRAP.format(filename_config)

        print('Submitting job {}'.format(job_name))
        command = ' '.join([SLURM_COMMAND, slurm_args_dynamic, slurm_python_wrap])
        subprocess.call(command, shell=True)
