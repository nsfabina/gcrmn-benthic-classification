#!/usr/bin/env bash


python ./submit_application_slurm.py \
  --config_name=dense_unet_128_64_43_16 \
  --label_experiment=millennium_50_aug \
  --response_mapping=custom \
  --model_version=20191105 \
  --num_jobs=10
