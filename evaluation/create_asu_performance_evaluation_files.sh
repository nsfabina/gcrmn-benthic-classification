#!/usr/bin/env bash


set -e


CONFIG_NAME=$1

if [[ -z "${CONFIG_NAME}" ]]; then
    echo "Config name required as first argument to script"
    exit 1
fi

DIR_BASE="/scratch/nfabina/gcrmn-benthic-classification/training_data_applied/${CONFIG_NAME}/lwr/reefs"

if [[ ! -d "${DIR_BASE}" ]]; then
    echo "There are no training data application files for specified config"
    exit 1
fi


for REEF in `ls "${DIR_BASE}"`; do
    DIR_REEF="${DIR_BASE}/${REEF}"
    DIR_TMP="${DIR_REEF}/tmp"

    echo "Creating Reef/NoReef shapefiles for ${REEF} at: \n${DIR_REEF}"

    if [[ ! -d "${DIR_TMP}" ]]; then
        mkdir -p "${DIR_TMP}"
    fi

    for RASTER in `ls "${DIR_REEF}"`; do
        BASENAME="${RASTER%_*}"
        FILEPATH_IN="${DIR_REEF}/${RASTER}"
        FILEPATH_OUT_TMP="${DIR_REEF}/tmp/${BASENAME}_reefs.tif"
        FILEPATH_OUT_CLEAN="${DIR_REEF}/${BASENAME}_reef_outline.shp"

        echo "Creating Reef/NoReef shapefile for raster: \n${FILEPATH_IN}"


        if [[ -f "${FILEPATH_OUT_CLEAN}" ]]; then
            echo "Shapefile already created, skipping: \n${FILEPATH_OUT_CLEAN}"
            continue
        fi

        echo "Creating intermediate Reef/NoReef raster at: \n${FILEPATH_OUT_TMP}"
        gdal_calc.py -A "${FILEPATH_IN}" --outfile="${FILEPATH_OUT_TMP}" \
            --calc="(A==3)-9999*(A!=3)" --NoDataValue=-9999 --type="Float32" --overwrite --quiet

        echo "Creating final Reef/NoReef shapefile at: \n${FILEPATH_OUT_CLEAN}"
        gdal_polygonize.py "${FILEPATH_OUT_TMP}" "${FILEPATH_OUT_CLEAN}" -q
    done

done
