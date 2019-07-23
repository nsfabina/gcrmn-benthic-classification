#!/usr/bin/env bash


DIR_DEST=/scratch/nfabina/gcrmn-benthic-classification/training_data


for REEF in belize hawaii heron karimunjawa moorea; do
    DIR_REEF="${DIR_DEST}/${REEF}"
    echo "Cleaning data for reef directory: " ${DIR_REEF}

    if [[ ! -d ${DIR_REEF}/tmp ]]; then
        mkdir -p ${DIR_REEF}/tmp
    fi

    if [[ ! -d ${DIR_REEF}/clean ]]; then
        mkdir -p ${DIR_REEF}/clean
    fi

    for FILEPATH in ${DIR_REEF}/raw/*.tif; do
        FILENAME=$(basename ${FILEPATH})

        if [[ ! -f ${DIR_REEF}/clean/${FILENAME} ]]; then
            echo "Cleaning data for imagery file: " ${FILEPATH}

            echo "Reprojecting"
            # Note that mosaics come in different projections than individual scenes
            gdalwarp -s_srs EPSG:3857 -t_srs EPSG:4326 ${FILEPATH} ${DIR_REEF}/clean/${FILENAME}

        else
            echo "Imagery file already cleaned: " ${FILEPATH}
        fi
    done

    if [[ ! -f ${DIR_REEF}/clean/features.vrt ]]; then
        echo "Building imagery VRT"
        # Note that it's easier to use a vrt than to assemble paired features/responses manually
        gdalbuildvrt ${DIR_REEF}/clean/features.vrt ${DIR_REEF}/clean/*.tif
    else
        echo "Imagery VRT already built"
    fi

    # Calculate parameters for responses
    FILENAME_IN=$(basename ${DIR_REEF}/raw/responses.geojson)
    DIR_TMP=${DIR_REEF}/tmp
    PT_REGEX='\-*[0-9]+\.*[0-9]+,( )*\-*[0-9]+\.*[0-9]+'
    LOWER_LEFT=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Lower Left' | egrep -o "${PT_REGEX}" | tr -d ',')
    UPPER_RIGHT=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Upper Right' | egrep -o "${PT_REGEX}" | tr -d ',')
    RES_REGEX='[0-9]+\.*[0-9]+,\-[0-9]+\.*[0-9]+'
    RESOLUTION=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Pixel Size' | egrep -o "${RES_REGEX}" | tr ',' ' ')


    TMP_FILEPATH_OUT="${DIR_TMP}/responses_lwr.geojson"
    CLEAN_FILEPATH_OUT="${DIR_REEF}/clean/responses_lwr.tif"
    if [[ ! -f ${CLEAN_FILEPATH_OUT} ]]; then
        echo "Cleaning data for LWR models"

        # Note that the lwr_class key with string values causes issues with the SQL in rasterization, so we convert
        # that to the lwr key with integer values
        sed 's/"lwr_class": "Land"/"lwr": 1/g' "${DIR_REEF}/raw/${FILENAME_IN}" > ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "Deep Reef Water 10m+"/"lwr": 2/g' ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "Reef"/"lwr": 3/g' ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "Cloud[^"]*Shade"/"lwr": -9999/g' ${TMP_FILEPATH_OUT}
        sed -i 's/"lwr_class": "[^"]*"/"lwr": -9999/g' ${TMP_FILEPATH_OUT}  # Catch-all for anything missed

        echo "Rasterize reef LWR classes"
        gdal_rasterize -init -9999 -a_nodata -9999 -te ${LOWER_LEFT} ${UPPER_RIGHT} -tr ${RESOLUTION} -a lwr \
            ${TMP_FILEPATH_OUT} ${CLEAN_FILEPATH_OUT}
    else
        echo "LWR data already cleaned"
    fi

done
