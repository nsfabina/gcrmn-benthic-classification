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
        FILEPATH_TMP_1="${DIR_REEF}/tmp/${BASENAME}_1.tif"
        FILEPATH_TMP_2="${DIR_REEF}/tmp/${BASENAME}_2.tif"
        FILEPATH_TMP_3="${DIR_REEF}/tmp/${BASENAME}_reefs.tif"
        FILEPATH_OUT_CLEAN="${DIR_REEF}/${BASENAME}_reef_outline.shp"

        printf "\nCreating Reef/NoReef shapefile for raster: \n${RASTER}\n"


        if [[ -f "${FILEPATH_OUT_CLEAN}" ]]; then
            printf "Shapefile already created, skipping: \n${FILEPATH_OUT_CLEAN}\n"
            continue
        fi

        printf "Creating intermediate Reef/NoReef raster at: \n${FILEPATH_TMP_3}\n"
        echo "Create raster for reefs more likely than land"
        gdal_calc.py -A "${RASTER}" --A_band=3 -B "${RASTER}" --B_band=1 \
            --outfile="${FILEPATH_TMP_1}" --NoDataValue=-9999 --type="Int16" --overwrite --quiet \
            --calc="A > B"
        echo "Create raster for reefs more likely than water"
        gdal_calc.py -A "${RASTER}" --A_band=3 -B "${RASTER}" --B_band=2 \
            --outfile="${FILEPATH_TMP_2}" --NoDataValue=-9999 --type="Int16" --overwrite --quiet \
            --calc="A > B"
        echo "Create raster for rReefs more likely in both"
        gdal_calc.py -A "${FILEPATH_TMP_1}" -B "${FILEPATH_TMP_2}" \
            --outfile="${FILEPATH_TMP_3}" --NoDataValue=-9999 --type="Int16" --overwrite --quiet \
            --calc="numpy.logical_and(A, B)"

        printf "Creating final Reef/NoReef shapefile at: \n${FILEPATH_OUT_CLEAN}\n"
        gdal_polygonize.py "${FILEPATH_TMP_3}" "${FILEPATH_OUT_CLEAN}" -q
    done

done
