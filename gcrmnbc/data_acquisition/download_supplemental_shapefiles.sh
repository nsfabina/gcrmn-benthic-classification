#!/usr/bin/env bash


set -e

PATH_GDRIVE="/data/gcrmn/"
PATH_SCRATCH="/scratch/nfabina/gcrmn-benthic-classification/training_data/clean"


if [[ ! -d "${PATH_SCRATCH}" ]]; then
    mkdir -p "${PATH_SCRATCH}"
fi

rclone copy "remote:${PATH_GDRIVE}/land" "${PATH_SCRATCH}"
rclone copy "remote:${PATH_GDRIVE}/water" "${PATH_SCRATCH}"
