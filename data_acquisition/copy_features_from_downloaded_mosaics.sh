#!/usr/bin/env bash


DIR_SRC=/scratch/nfabina/gcrmn-benthic-classification/visual_mosaic_v1
DIR_DEST=/scratch/nfabina/gcrmn-benthic-classification/training_data


echo "Copy and clean training data"

echo "Clean Belize data"

if [[ ! -d ${DIR_DEST}/belize/raw ]]; then
  mkdir -p ${DIR_DEST}/belize/raw
fi

for LAT in 0525E 0526E; do
  for LON in 1122N 1123N 1124N 1125N; do
    FILENAME=L15-${LAT}-${LON}.tif
    cp ${DIR_SRC}/caribbean/west-caribbean/${FILENAME} ${DIR_DEST}/belize/raw/
  done
done

curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson \
  -o ${DIR_DEST}/belize/raw/lwr.geojson


echo "Clean Heron data"

if [[ ! -d ${DIR_DEST}/heron/raw ]]; then
    mkdir -p ${DIR_DEST}/heron/raw
fi

cp -r ${DIR_SRC}/GBR/Heron/*.tif ${DIR_DEST}/heron/raw/


echo "Clean Karimunjawa data"

if [[ ! -d ${DIR_DEST}/karimunjawa/raw ]]; then
    mkdir -p ${DIR_DEST}/karimunjawa/raw
fi

cp -r ${DIR_SRC}/karimunjawa/*.tif ${DIR_DEST}/karimunjawa/raw/


echo "Clean Moorea data"

if [[ ! -d ${DIR_DEST}/moorea/raw ]]; then
    mkdir -p ${DIR_DEST}/moorea/raw
fi

cp -r ${DIR_SRC}/moorea/*.tif ${DIR_DEST}/moorea/raw/


echo "Clean West Hawaii Data"

if [[ ! -d ${DIR_DEST}/hawaii/raw ]]; then
    mkdir -p ${DIR_DEST}/hawaii/raw
fi

cp -r ${DIR_SRC}/hawaii/hawaii/*.tif ${DIR_DEST}/hawaii/raw/
