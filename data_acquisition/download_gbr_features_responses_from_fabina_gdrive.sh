#!/usr/bin/env bash


# This data was acquired from Mitch's Earth Engine account. Mitch shared a script with Nick, which is now on Nick's
# Earth Engine account. This script allowed Nick to download several data layers for specific reef complexes. Nick
# stored that data on his GDrive account and it is now accessible there.


GDRIVE_BASE="/data/atlas/gbr_earth_engine_samples"
SCRATCH_BASE="/scratch/nfabina/gcrmn-benthic-classification/training_data"


for REEF in batt_tongue little ribbon; do
    echo "Downloading features and responses for ${REEF} reef"
    if [[ ! -d ${SCRATCH_BASE}/${REEF}/raw ]]; then
        mkdir -p ${SCRATCH_BASE}/${REEF}/raw
    fi

    rclone copy --include="${REEF}_{geomorphic,dove_rrs}.tif" remote:${GDRIVE_BASE}/ ${SCRATCH_BASE}/${REEF}/raw/
  
done
