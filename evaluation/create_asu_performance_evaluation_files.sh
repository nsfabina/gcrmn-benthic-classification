#!/usr/bin/env bash


set -e


CONFIG_NAME=$1

if [[ -z "${CONFIG_NAME}" ]]; then
    printf "Config name required as first argument to script\n"
    exit 1
fi

DIR_BASE="/scratch/nfabina/gcrmn-benthic-classification/training_data_applied/${CONFIG_NAME}/lwr/reefs"

if [[ ! -d "${DIR_BASE}" ]]; then
    printf "There are no training data application files for specified config\n"
    exit 1
fi


for REEF in `ls "${DIR_BASE}"`; do
    DIR_REEF="${DIR_BASE}/${REEF}"
    DIR_TMP="${DIR_REEF}/tmp"

    printf "\n\nCreating Reef/NoReef shapefiles for ${REEF} at: \n${DIR_REEF}\n"

    if [[ ! -d "${DIR_TMP}" ]]; then
        mkdir -p "${DIR_TMP}"
    fi

    for RASTER in `ls ${DIR_REEF}/*applied.tif`; do
        FILENAME="$(basename $(basename $RASTER) .tif)"
        BASENAME="${FILENAME%_*}"
        FILEPATH_OUT_TMP="${DIR_REEF}/tmp/${BASENAME}_reefs.tif"
        FILEPATH_OUT_CLEAN="${DIR_REEF}/${BASENAME}_reef_outline.shp"

        printf "\nCreating Reef/NoReef shapefile for raster: \n${RASTER}\n"


        if [[ -f "${FILEPATH_OUT_CLEAN}" ]]; then
            printf "Shapefile already created, skipping: \n${FILEPATH_OUT_CLEAN}\n"
            continue
        fi

        printf "Creating intermediate Reef/NoReef raster at: \n${FILEPATH_OUT_TMP}\n"
        gdal_calc.py -A "${RASTER}" --A_band=1 -B "${RASTER}" --B_band=2 -C "${RASTER}" --C_band=3 \
            --outfile="${FILEPATH_OUT_TMP}" --NoDataValue=-9999 --type="Float32" --overwrite --quiet
            --calc="-9999 + 10000 * numpy.logical_and(C > A, C > B)"

        printf "Creating final Reef/NoReef shapefile at: \n${FILEPATH_OUT_CLEAN}\n"
        gdal_polygonize.py "${FILEPATH_OUT_TMP}" "${FILEPATH_OUT_CLEAN}" -q
    done

done
