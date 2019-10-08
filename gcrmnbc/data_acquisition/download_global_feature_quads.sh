#!/usr/bin/env bash


DIR_DEST='/scratch/nfabina/gcrmn-benthic-classification/global_data'

if [[ ! -d "${DIR_DEST}" ]]; then
    mkdir -p "${DIR_DEST}"
fi

gsutil -m cp -n -r "gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/**/L15-*.tif" "${DIR_DEST}"
