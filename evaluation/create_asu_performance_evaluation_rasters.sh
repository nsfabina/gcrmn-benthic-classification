#!/usr/bin/env bash


set -e


CONFIG_NAME=$1

DIR_IN="/scratch/nfabina/gcrmn-benthic-classification/training_data"
DIR_OUT="/scratch/nfabina/gcrmn-benthic-classification/training_data_applied/${CONFIG_NAME}/lwr/"


for REEF in `ls ${DIR_IN}`; do
    echo "Creating Reef/NoReef shapefile for ${REEF}"

    FILEPATH_IN="${DIR_IN}/${REEF}/clean/responses_lwr.tif"
    DIR_OUT_REEF="${DIR_OUT}/${REEF}"
    FILEPATH_OUT_TMP="${DIR_OUT_REEF}/responses_r.tif"
    FILEPATH_OUT_CLEAN="${DIR_OUT_REEF}/reef_outline.shp"

    if [[ ! -d "${DIR_OUT_REEF}" ]]; then
        mkdir -p "${DIR_OUT_REEF}"
    fi

    echo "Creating intermediate Reef/NoReef raster"
    gdal_calc.py -A "${FILEPATH_IN}" --outfile="${FILEPATH_OUT_TMP}" \
        --calc="(A==3)-9999*(A!=3)" --NoDataValue=-9999 --type="Float32" --overwrite --quiet

    echo "Creating final Reef/NoReef shapefile"
    gdal_polygonize.py "${FILEPATH_OUT_TMP}" "${FILEPATH_OUT_CLEAN}" -q

done
