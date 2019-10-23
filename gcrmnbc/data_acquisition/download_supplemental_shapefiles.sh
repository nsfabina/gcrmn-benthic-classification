#!/usr/bin/env bash


set -e

PATH_GDRIVE="/data/gcrmn"
PATH_SUPP="/scratch/nfabina/gcrmn-benthic-classification/training_data/responses_supp/raw"
PATH_SUPP_MODEL="/scratch/nfabina/gcrmn-benthic-classification/training_data/responses_uq_model/raw"


if [[ ! -d "${PATH_SUPP}" ]]; then
    mkdir -p "${PATH_SUPP}"
fi

if [[ ! -d "${PATH_SUPP_MODEL}" ]]; then
    mkdir -p "${PATH_SUPP_MODEL}"
fi

rclone copy "remote:${PATH_GDRIVE}/land" "${PATH_SUPP}"
rclone copy "remote:${PATH_GDRIVE}/water" "${PATH_SUPP}"
rclone copy "remote:${PATH_GDRIVE}/supplemental_training_data" "${PATH_SUPP_MODEL}"
