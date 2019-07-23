#!/usr/bin/env bash


# This data was initially acquired manually from allencoralatlas.org, by navigating to the MVP sites, clicking on the
# pie chart icon, and clicking 'Download Layers and Stats'. It was subsequently uploaded to nsfabina's GDrive.


DIR_DEST=/scratch/nfabina/gcrmn-benthic-classification/training_data


for REEF in belize hawaii heron karimunjawa moorea; do
  if [[ ! -d ${DIR_DEST}/${REEF}/raw ]]; then
    mkdir -p ${DIR_DEST}/${REEF}/raw
  fi
  
  rclone copy remote:/data/gcrmn/${REEF}/raw/responses.geojson ${DIR_DEST}/${REEF}/raw/
done

