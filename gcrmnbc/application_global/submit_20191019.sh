#!/usr/bin/env bash


python ./submit_application_slurm.py \
  --config_name=dense_unet_128_64_42_16 \
  --label_experiment=downsample_50_aug \
  --response_mapping=lwr \
  --model_version=20191019 \
  --num_jobs=10
