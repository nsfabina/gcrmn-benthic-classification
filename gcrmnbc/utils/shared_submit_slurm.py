SLURM_COMMAND = 'sbatch --mail-user=nsfabina@asu.edu --nodes=1 --cpus-per-task=1 --ntasks=1 --mem-per-cpu=20000 '
SLURM_GPUS = '--partition gpu --gres=gpu:1 --qos=wildfire '
SLURM_GPUS_LARGE = SLURM_GPUS + '--constraint="V100_32" '
