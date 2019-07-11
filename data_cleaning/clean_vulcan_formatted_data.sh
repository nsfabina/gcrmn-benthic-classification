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
    FILENAME=$(basename ${DIR_REEF}/raw/*.geojson)
    DIR_TMP=${DIR_REEF}/tmp
    PT_REGEX='\-*[0-9]+\.*[0-9]+,( )*\-*[0-9]+\.*[0-9]+'
    LOWER_LEFT=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Lower Left' | egrep -o "${PT_REGEX}" | tr -d ',')
    UPPER_RIGHT=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Upper Right' | egrep -o "${PT_REGEX}" | tr -d ',')
    RES_REGEX='[0-9]+\.*[0-9]+,\-[0-9]+\.*[0-9]+'
    RESOLUTION=$(gdalinfo ${DIR_REEF}/clean/features.vrt | grep 'Pixel Size' | egrep -o "${RES_REGEX}" | tr ',' ' ')


    if [[ ! -f ${DIR_REEF}/clean/responses_lwr.tif ]]; then
        echo "Cleaning data for LWR data"
        # Note that the lwr_class key with string values causes issues with the SQL in rasterization, so we convert
        # that to the lwr key with integer values
        sed 's/"lwr_class": "Land"/"lwr": 1/g' "${DIR_REEF}/raw/${FILENAME}" > ${DIR_TMP}/responses_lwr.geojson
        sed -i 's/"lwr_class": "Deep Reef Water 10m+"/"lwr": 2/g' ${DIR_TMP}/responses_lwr.geojson
        sed -i 's/"lwr_class": "Reef"/"lwr": 3/g' ${DIR_TMP}/responses_lwr.geojson
        sed -i 's/"lwr_class": "Cloud-Shade"/"lwr": -9999/g' ${DIR_TMP}/responses_lwr.geojson

        echo "Rasterize reef LWR classes"
        gdal_rasterize -init -9999 -a_nodata -9999 -te ${LOWER_LEFT} ${UPPER_RIGHT} -tr ${RESOLUTION} -a lwr \
            ${DIR_TMP}/responses_lwr.geojson ${DIR_REEF}/clean/responses_lwr.tif

        echo "Create compressed version"
        gdal_translate -co "COMPRESS=LZW" \
            ${DIR_REEF}/clean/responses_lwr.tif ${DIR_REEF}/clean/responses_lwr_compressed.tif
    else
        echo "LWR data already cleaned"
    fi

    if [[ ! -f ${DIR_REEF}/clean/responses_bio.tif ]]; then
        echo "Cleaning data for biotic/abiotic data"
        # Note that I didn't want to test whether the find and replace was necessary for this layer as well, so I just
        # assumed it would be necessary
        sed 's/"benthic_class": "Land"/"benthic": 1/g' "${DIR_REEF}/raw/${FILENAME}" > ${DIR_TMP}/responses_bio.geojson

        sed -i 's/"benthic_class": "Deep"/"benthic": 2/g' ${DIR_TMP}/responses_bio.geojson

        sed -i 's/"benthic_class": "Benthic Microalgae"/"benthic": 3/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Coral *\/ *Algae"/"benthic": 3/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Seagrass"/"benthic": 3/g' ${DIR_TMP}/responses_bio.geojson

        sed -i 's/"benthic_class": "Plateau 3-10m"/"benthic": 4/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Rock"/"benthic": 4/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Rubble"/"benthic": 4/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Sand"/"benthic": 4/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Sand *\/ *Mud"/"benthic": 4/g' ${DIR_TMP}/responses_bio.geojson

        sed -i 's/"benthic_class": "Breaking Waves"/"benthic": -9999/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Cloud *- *Shade"/"benthic": -9999/g' ${DIR_TMP}/responses_bio.geojson
        # Small reef looks like it's a combination of biotic and abiotic components, so I'm marking it as unknown to
        # avoid training the model on bad data
        sed -i 's/"benthic_class": "Small Reef"/"benthic": -9999/g' ${DIR_TMP}/responses_bio.geojson
        sed -i 's/"benthic_class": "Unknown"/"benthic": -9999/g' ${DIR_TMP}/responses_bio.geojson

        echo "Rasterize reef biotic/abiotic classes"
        gdal_rasterize -init -9999 -a_nodata -9999 -te ${LOWER_LEFT} ${UPPER_RIGHT} -tr ${RESOLUTION} -a benthic \
            ${DIR_TMP}/responses_bio.geojson ${DIR_REEF}/clean/responses_bio.tif

        echo "Create compressed version"
        gdal_translate -co "COMPRESS=LZW" \
            ${DIR_REEF}/clean/responses_bio.tif ${DIR_REEF}/clean/responses_bio_compressed.tif
    else
        echo "Biotic/abiotic data already cleaned"
    fi

done
