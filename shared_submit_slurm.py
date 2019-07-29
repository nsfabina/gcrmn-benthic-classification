SLURM_COMMAND = 'sbatch --mail-type=FAIL --mail-user=nsfabina@asu.edu --time=4:00:00 ' + \
                '--nodes=1 --cpus-per-task=1 --mem-per-cpu=20000 --ntasks=1 ' + \
                '--partition gpu --gres=gpu:1 --qos=wildfire '
SLURM_GPUS_LARGE = '--constraint=V100_32 '
SLURM_GPUS = '--constraint=V100_32|V100_16|GTX1080 '
