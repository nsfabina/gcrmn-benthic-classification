#!/usr/bin/env bash

set -e


GDRIVE_PATH="/data/millennium_project"
DIR_DEST="/scratch/nfabina/gcrmn-benthic-classification/training_data/raw_millennium_project"

if [[ ! -d ${DIR_DEST} ]]; then
    mkdir -p ${DIR_DEST}
fi

rclone copy remote:${GDRIVE_PATH} ${DIR_DEST}

# The following regions have murky shore waters and poor correspondence between imagery and classes
for REGION in 'Myanmar_v2.zip' 'SriLanka_v6.zip' 'Tobago_v4.zip' 'Vietnam_v2.zip'; do
    rm ${DIR_DEST}/${REGION}
done

# Chagos has large lagoons that look like deep water and would be better categorized as open water, and it also has
# many deep classes that are not used in our custom mappings, we remove it because it's not critical to the training
# data
rm ${DIR_DEST}/Chagos_v6.shp

for SHAPEFILE in ${DIR_DEST}/*; do
    unzip ${SHAPEFILE} -d ${DIR_DEST}
done
