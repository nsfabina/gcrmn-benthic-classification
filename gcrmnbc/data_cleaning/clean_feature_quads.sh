#!/usr/bin/env bash


set -e

DIR_DATA="/scratch/nfabina/gcrmn-benthic-classification/training_data"
DIR_TMP="${DIR_DATA}/tmp"
DIR_CLEAN="${DIR_DATA}/clean"
NODATA_VALUE=-9999

echo "Cleaning feature quads"

for FILEPATH_TMP in `ls "${DIR_TMP}/*_features.tif"`; do
    echo "Cleaning feature quad:  ${FILEPATH_TMP}"

    BASENAME=$(basename ${FILEPATH_TMP} .tif)
    FILEPATH_CLEAN="${DIR_CLEAN}/${BASENAME}.tif"

    if [[ -f "${FILEPATH_CLEAN}" ]]; then
        echo "Feature quad already cleaned"
        continue
    fi

    gdal_translate -b 1 -b 2 -b 3 -q "${FILEPATH_TMP}" "${FILEPATH_CLEAN}"
    rm "${FILEPATH_TMP}"

done
