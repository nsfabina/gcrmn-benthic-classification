#!/usr/bin/env bash


set -e

SCRATCH_BASE="/scratch/nfabina/gcrmn-benthic-classification/training_data"
PROJ=4326
NODATA_VALUE=-9999
OUTPUT_TYPE="Float32"


for REEF in "batt_tongue" "little" "ribbon"; do
    echo "Clean data for reef ${REEF}"

    DIR_RAW="${SCRATCH_BASE}/${REEF}/raw"
    DIR_TMP="${SCRATCH_BASE}/${REEF}/tmp"
    DIR_CLEAN="${SCRATCH_BASE}/${REEF}/clean"

    echo "Create temp and clean directories"
    if [[ ! -d ${DIR_TMP} ]]; then
      mkdir -p "${DIR_TMP}"
    fi
    if [[ ! -d ${DIR_CLEAN} ]]; then
      mkdir -p "${DIR_CLEAN}"
    fi

    if [[ ! -f "${DIR_CLEAN}/features.vrt" ]]; then
        echo "Convert reflectance to correct projection"
        # Note that the resolutions of this imagery and the Vulcan quads (other script) are approximately the same and
        # that I've verified this, so there's no need to specify the resolution
        gdalwarp -t_srs EPSG:${PROJ} "${DIR_RAW}/${REEF}_dove_rrs.tif" "${DIR_TMP}/dove_rrs_0_projected.tif" -q

        echo "Switch from BGR to RGB to match Vulcan quads"
        gdal_translate -b 3 -b 2 -b 1 "${DIR_TMP}/dove_rrs_0_projected.tif" "${DIR_TMP}/dove_rrs_1_banded.tif" -q

        echo "Create a VRT file to keep consistent with Vulcan training data"
        gdalbuildvrt "${DIR_CLEAN}/features.vrt" "${DIR_TMP}/dove_rrs_1_banded.tif"
    fi

    if [[ ! -f "${DIR_CLEAN}/responses_lwr.tif" ]]; then
        echo "Convert geomorphic to correct projection"
        gdalwarp -t_srs EPSG:${PROJ} -ot ${OUTPUT_TYPE} \
            "${DIR_RAW}/${REEF}_geomorphic.tif" "${DIR_TMP}/geomorphic_0_projected.tif" -dstnodata ${NODATA_VALUE} \
             -overwrite -q

        echo "Convert geomorphic codes to LWR mappings"
        # Note that order matters and values are found in Mitch's Github repo. Land and water are already encoded as
        # 1 and 2, respectively. Turbid areas can be encoded as either 0 or 3 and we treat this class as missing data.
        # First, we set all turbid==3 to 0, and then all 0 to -9999. Second, we set all reef classes, which is anything
        # encoded as 4 or greater, as 3, which is the encoding for the land/water/reef model.
        gdal_calc.py -A "${DIR_TMP}/geomorphic_0_projected.tif" --outfile="${DIR_TMP}/geomorphic_1_mapped.tif" \
            --calc="A*(A!=3)" --NoDataValue=${NODATA_VALUE} --type=${OUTPUT_TYPE} --overwrite --quiet
        gdal_calc.py -A "${DIR_TMP}/geomorphic_1_mapped.tif" --outfile="${DIR_TMP}/geomorphic_1_mapped.tif" \
            --calc="A*(A>0)${NODATA_VALUE}*(numpy.logical_or(A<=0, numpy.isnan(A)))" \
            --NoDataValue=${NODATA_VALUE} --type=${OUTPUT_TYPE} --overwrite --quiet
        gdal_calc.py -A "${DIR_TMP}/geomorphic_1_mapped.tif" --outfile="${DIR_CLEAN}/responses_lwr.tif" \
            --calc="A*(A<=2)+3*(A>=3)" --NoDataValue=${NODATA_VALUE} --type=${OUTPUT_TYPE} --quiet
    fi

done
