#!/usr/bin/env bash

set -e


GDRIVE_PATH="/data/millennium_project"
DIR_DEST="/scratch/nfabina/gcrmn-benthic-classification/training_data/raw_millennium_project"

if [[ ! -d ${DIR_DEST} ]]; then
    mkdir -p ${DIR_DEST}
fi

rclone copy remote:${GDRIVE_PATH} ${DIR_DEST}

for SHAPEFILE in ${DIR_DEST}/*; do
    unzip ${SHAPEFILE} -d ${DIR_DEST}
done
