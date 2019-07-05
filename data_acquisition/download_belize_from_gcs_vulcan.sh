#!/usr/bin/env bash


URL_ACA='gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/caribbean/west-caribbean'


# Create data directory, if necessary
if [[ ! -d ../data/belize/raw ]]; then
  mkdir -p ../data/belize/raw
fi


echo "Downloading Lighthouse Reef imagery"

for LAT in 0525E 0526E; do
  for LON in 1122N 1123N 1124N 1125N; do

    FILENAME=L15-${LAT}-${LON}.tif
    if [[ ! -f ${FILENAME} ]]; then
      echo "Downloading ${FILENAME}"
      gsutil cp ${URL_ACA}/${FILENAME} tmp_0_${FILENAME}
    else
      echo "File already exists at ${FILENAME}"
    fi

  done
done


echo "Download reef LWR classes"

if [[ ! -f lwr.tif ]]; then
  curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson \
    -o tmp_0.geojson
else
  echo "Reef LWR classes already available"
fi
