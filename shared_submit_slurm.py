SLURM_COMMAND = 'sbatch --mail-type=FAIL --mail-user=nsfabina@asu.edu --time=4:00:00 ' + \
                '--nodes=1 --cpus-per-task=1 --mem-per-cpu=20000 --ntasks=1 '
SLURM_GPUS_LARGE = '--qos=wildfire --gres=gpu:1 --partition=mrlinegpu1,rcgpu1 '
SLURM_GPUS = '--qos=wildfire --gres=gpu:1 ' + \
             '--partition=mrlinegpu1,rcgpu1,physicsgpu1,cidsegpu1,cidsegpu2,sulcgpu1,sulcgpu2,asinghargpu1 '
