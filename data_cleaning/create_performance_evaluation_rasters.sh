#!/usr/bin/env bash


set -e


DIR_BASE="/scratch/nfabina/gcrmn-benthic-classification/training_data"


for REEF in `ls ${DIR_BASE}`; do
    echo "Creating Reef/NoReef shapefile for ${REEF}"

    DIR_REEF="${DIR_BASE}/${REEF}"

    echo "Creating intermediate Reef/NoReef raster"
    gdal_calc.py -A "${DIR_REEF}/clean/responses_lwr.tif" --outfile="${DIR_REEF}/tmp/responses_r.tif" \
        --calc="(A==3)-9999*(A!=3)" --NoDataValue=-9999 --type="Float32" --overwrite --quiet

    echo "Creating final Reef/NoReef shapefile"
    gdal_polygonize.py "${DIR_REEF}/tmp/responses_r.tif" "${DIR_REEF}/clean/reef_outline.shp" -q

done
