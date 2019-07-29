#!/usr/bin/env bash


set -e


CONFIG_NAME=$1

if [[ -z "${CONFIG_NAME}" ]]; then
    echo "Config name required as first argument to script"
    exit 1
fi

DIR_IN="/scratch/nfabina/gcrmn-benthic-classification/training_data"
DIR_OUT="/scratch/nfabina/gcrmn-benthic-classification/training_data_applied/${CONFIG_NAME}/lwr"

if [[ ! -d "${DIR_OUT}" ]]; then
    echo "There are no training data application files for specified config"
    exit 1
fi


for REEF in `ls ${DIR_IN}`; do
    echo "Creating Reef/NoReef shapefile for ${REEF}"

    FILEPATH_IN="${DIR_IN}/${REEF}/clean/responses_lwr.tif"
    DIR_OUT_REEF="${DIR_OUT}/${REEF}"
    FILEPATH_OUT_TMP="${DIR_OUT_REEF}/responses_r.tif"
    FILEPATH_OUT_CLEAN="${DIR_OUT_REEF}/reef_outline.shp"

    if [[ -f "${FILEPATH_OUT_CLEAN}" ]]; then
        echo "Shapefile already created at ${FILEPATH_OUT_CLEAN}, skipping"
        continue
    fi

    if [[ ! -d "${DIR_OUT_REEF}" ]]; then
        mkdir -p "${DIR_OUT_REEF}"
    fi

    echo "Creating intermediate Reef/NoReef raster"
    gdal_calc.py -A "${FILEPATH_IN}" --outfile="${FILEPATH_OUT_TMP}" \
        --calc="(A==3)-9999*(A!=3)" --NoDataValue=-9999 --type="Float32" --overwrite --quiet

    echo "Creating final Reef/NoReef shapefile"
    gdal_polygonize.py "${FILEPATH_OUT_TMP}" "${FILEPATH_OUT_CLEAN}" -q

done
