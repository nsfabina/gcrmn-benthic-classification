#!/usr/bin/env bash


SCRATCH_BASE="/scratch/nfabina/gcrmn-benthic-classification/training_data"
PROJ=4326


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
        gdalwarp -t_srs EPSG:${PROJ} "${DIR_RAW}/*dove_rrs.tif" "${DIR_TMP}/dove_rrs_0_projected.tif"

        echo "Switch from BGR to RGB to match Vulcan quads"
        gdal_translate -b 3 -b -2 -b -1 "${DIR_TMP}/dove_rrs_0_projected.tif" "${DIR_TMP}/dove_rrs_1_banded.tif"

        echo "Create a VRT file to keep consistent with Vulcan training data"
        gdalbuildvrt "${DIR_CLEAN}/features.vrt" "${DIR_TMP}/dove_rrs_1_banded.tif"
    fi

    if [[ ! -f "${DIR_CLEAN}/responses_lwr.tif" ]]; then
        echo "Convert geomorphic to correct projection"
        gdalwarp -t_srs EPSG:${PROJ} "${DIR_RAW}/*geomorphic.tif" "${DIR_TMP}/geomorphic_0_projected.tif"

        echo "Convert geomorphic codes to LWR mappings"
        # Note that order matters and values are found in Mitch's Github repo
        # Land should be encoded as 1 and is already via the "Land" class
        # Water should be encoded as 2 and is already via the "Deep" class
        # Missing or invalid data -- "turbid" can be 0 or 3 but we also handle missing data. We set turbid encodings of 3 to
        # 0, then encodings of 0 or nan to -9999
        gdal_calc.py -A "${DIR_TMP}/geomorphic_0_projected.tif" --outfile="${DIR_TMP}/geomorphic_1_mapped.tif" \
            --calc="A*(A!=3)"
        gdal_calc.py -A "${DIR_TMP}/geomorphic_1_mapped.tif" --overwrite \
            --calc="A*(A>0)-9999*(numpy.logical_or(A<=0, numpy.isnan(A)))"
        # Reef should be encoded as 3 which is fine now that turbidity has been changed, so everything greater than 3 can be
        # mapped to 3
        gdal_calc.py -A "${DIR_TMP}/geomorphic_1_mapped.tif" --outfile="${DIR_CLEAN}/responses_lwr.tif" \
            --calc="A*(A<=2)+3*(A>=3)"
    fi

done
