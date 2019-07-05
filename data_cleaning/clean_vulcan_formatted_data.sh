#!/usr/bin/env bash


for DIR_REEF in ../data/*; do
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
            gdalwarp -s_srs EPSG:3857 -t_srs EPSG:4326 ${FILEPATH} ${DIR_REEF}/tmp/${FILENAME}

            echo "Storing only blue and green bands"
            gdal_translate -b 1 -b 2 -a_nodata -9999 ${DIR_REEF}/tmp/${FILENAME} ${DIR_REEF}/clean/${FILENAME}
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

    if [[ ! -f ${DIR_REEF}/clean/responses.tif ]]; then
        echo "Cleaning data for LWR data"
        # Note that the lwr_class key with string values causes issues with the SQL in rasterization, so we convert that to
        # the lwr key with integer values
        FILENAME=$(basename ${DIR_REEF}/raw/*.geojson)
        DIR_TMP=${DIR_REEF}/tmp
        sed 's/"lwr_class": "Land"/"lwr": 1/g' "${DIR_REEF}/raw/${FILENAME}" > ${DIR_TMP}/0_${FILENAME}
        sed 's/"lwr_class": "Reef"/"lwr": 3/g' ${DIR_TMP}/0_${FILENAME} > ${DIR_TMP}/1_${FILENAME}
        sed 's/"lwr_class": "Deep Reef Water 10m+"/"lwr": 2/g' ${DIR_TMP}/1_${FILENAME} > ${DIR_TMP}/2_${FILENAME}
        sed 's/"lwr_class": "Cloud-Shade"/"lwr": 4/g' ${DIR_TMP}/2_${FILENAME} > ${DIR_TMP}/responses.geojson

        echo "Rasterize reef LWR classes"
        PT_REGEX='\-*[0-9]+\.*[0-9]+,( )*\-*[0-9]+\.*[0-9]+'
        LOWER_LEFT=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Lower Left' | egrep -o "${PT_REGEX}" | tr -d ',')
        UPPER_RIGHT=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Upper Right' | egrep -o "${PT_REGEX}" | tr -d ',')
        RES_REGEX='[0-9]+\.*[0-9]+,\-[0-9]+\.*[0-9]+'
        RESOLUTION=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Pixel Size' | egrep -o "${RES_REGEX}" | tr ',' ' ')
        gdal_rasterize \
        -init -9999 \
        -a_nodata -9999 \
        -te ${LOWER_LEFT} ${UPPER_RIGHT} \
        -tr ${RESOLUTION} \
        -a lwr \
        ${DIR_TMP}/responses.geojson ${DIR_REEF}/clean/responses.tif
    else
        echo "LWR data already cleaned"
    fi

done
