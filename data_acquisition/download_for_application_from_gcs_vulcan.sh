#!/usr/bin/env bash


set -e

DIR_DEST=/scratch/nfabina/gcrmn-benthic-classification/visual_mosaic_v1/
GCS_URL=gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/


if [[ ! -d ${DIR_DEST} ]]; then
  mkdir -p ${DIR_DEST}
fi
  
gsutil cp -n -r ${GCS_URL} ${DIR_DEST}

