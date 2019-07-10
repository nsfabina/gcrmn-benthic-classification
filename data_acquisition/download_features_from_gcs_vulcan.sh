#!/usr/bin/env bash


GCS_URL=gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic


echo "Download Belize data (Lighthouse Reef)"

if [[ ! -d ../data/belize/raw ]]; then
  mkdir -p ../data/belize/raw
fi

for LAT in 0525E 0526E; do
  for LON in 1122N 1123N 1124N 1125N; do
    FILENAME=L15-${LAT}-${LON}.tif
    gsutil cp ${GCS_URL}/caribbean/west-caribbean/${FILENAME} ../data/belize/raw/
  done
done

curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson -o ../data/belize/raw/lwr.geojson


echo "Download Heron data"

if [[ ! -d ../data/heron/raw ]]; then
    mkdir -p ../data/heron/raw
fi

gsutil cp -r ${GCS_URL}/Heron/*.tif ../data/heron/raw/


echo "Download Karimunjawa data"

if [[ ! -d ../data/karimunjawa/raw ]]; then
    mkdir -p ../data/karimunjawa/raw
fi

gsutil cp -r ${GCS_URL}/karimunjawa/*.tif ../data/karimunjawa/raw/


echo "Download Moorea data"

if [[ ! -d ../data/moorea/raw ]]; then
    mkdir -p ../data/moorea/raw
fi

gsutil cp -r ${GCS_URL}/moorea/*.tif ../data/moorea/raw/


echo "Download West Hawaii Data"

if [[ ! -d ../data/hawaii/raw ]]; then
    mkdir -p ../data/hawaii/raw
fi

gsutil cp -r ${GCS_URL}/hawaii/hawaii/*.tif ../data/hawaii/raw/

