#!/usr/bin/env bash


set -e

DIR_DEST="/scratch/nfabina/gcrmn-benthic-classification/training_data"
NODATA_VALUE=-9999


for REEF in belize hawaii heron karimunjawa moorea; do
    DIR_REEF="${DIR_DEST}/${REEF}"
    echo "Cleaning data for reef directory: ${DIR_REEF}"

    DIR_RAW="${DIR_REEF}/raw"
    DIR_TMP="${DIR_REEF}/tmp"
    DIR_CLEAN="${DIR_REEF}/clean"

    if [[ ! -d "${DIR_TMP}" ]]; then
        mkdir -p "${DIR_TMP}"
    fi

    if [[ ! -d "${DIR_CLEAN}" ]]; then
        mkdir -p "${DIR_CLEAN}"
    fi

    for FILEPATH in ${DIR_RAW}/*.tif; do
        FILENAME=$(basename ${FILEPATH})

        if [[ ! -f "${DIR_CLEAN}/${FILENAME}" ]]; then
            echo "Cleaning data for imagery file: ${FILEPATH}"

            echo "Reprojecting"
            # Note that mosaics come in different projections than individual scenes
            gdalwarp -s_srs EPSG:3857 -t_srs EPSG:4326 ${FILEPATH} "${DIR_TMP}/${FILENAME}" -q

            echo "Removing fourth band"
            gdal_translate -b 1 -b 2 -b 3 "${DIR_TMP}/${FILENAME}" "${DIR_CLEAN}/${FILENAME}" -q

        else
            echo "Imagery file already cleaned: ${FILEPATH}"
        fi
    done

    if [[ ! -f "${DIR_CLEAN}/features.vrt" ]]; then
        echo "Building imagery VRT"
        # Note that it's easier to use a vrt than to assemble paired features/responses manually
        gdalbuildvrt "${DIR_CLEAN}/features.vrt" ${DIR_CLEAN}/*.tif
    else
        echo "Imagery VRT already built"
    fi

    # Calculate parameters for responses
    FILENAME_IN=$(basename ${DIR_RAW}/responses.geojson)
    PT_REGEX='\-*[0-9]+\.*[0-9]+,( )*\-*[0-9]+\.*[0-9]+'
    LOWER_LEFT=$(gdalinfo ${DIR_CLEAN}/features.vrt | grep 'Lower Left' | egrep -o "${PT_REGEX}" | tr -d ',')
    UPPER_RIGHT=$(gdalinfo ${DIR_CLEAN}/features.vrt | grep 'Upper Right' | egrep -o "${PT_REGEX}" | tr -d ',')
    RES_REGEX='[0-9]+\.*[0-9]+,\-[0-9]+\.*[0-9]+'
    RESOLUTION=$(gdalinfo ${DIR_CLEAN}/features.vrt | grep 'Pixel Size' | egrep -o "${RES_REGEX}" | tr ',' ' ')


    TMP_FILEPATH_OUT="${DIR_TMP}/responses_lwr.geojson"
    CLEAN_FILEPATH_OUT="${DIR_CLEAN}/responses_lwr.tif"
    if [[ ! -f ${CLEAN_FILEPATH_OUT} ]]; then
        echo "Cleaning data for LWR models"

        # Note that the lwr_class key with string values causes issues with the SQL in rasterization, so we convert
        # that to the lwr key with integer values
        sed 's/"lwr_class": "Land"/"lwr": 1/g' "${DIR_RAW}/${FILENAME_IN}" > ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "Deep Reef Water 10m+"/"lwr": 2/g' ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "Reef"/"lwr": 3/g' ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "Cloud[^"]*Shade"/"lwr": -9999/g' ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "[^"]*"/"lwr": -9999/g' ${TMP_FILEPATH_OUT}  # Catch-all for anything missed

        echo "Rasterize reef LWR classes"
        gdal_rasterize -init ${NODATA_VALUE} -a_nodata ${NODATA_VALUE} -ot "Float32" \
            -te ${LOWER_LEFT} ${UPPER_RIGHT} -tr ${RESOLUTION} -a "lwr" \
            ${TMP_FILEPATH_OUT} ${CLEAN_FILEPATH_OUT} -q
    else
        echo "LWR data already cleaned"
    fi

done
