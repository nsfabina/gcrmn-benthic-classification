#!/usr/bin/env bash


set -e


DIR_DEST="/scratch/nfabina/gcrmn-benthic-classification/training_data/responses_uq/raw"


if [[ ! -d ${DIR_DEST} ]]; then
  mkdir -p ${DIR_DEST}
fi


echo "Download geojson responses"
gsutil cp gs://coral-atlas-data-share/geojson/20190910.lwr.geojson.zip ${DIR_DEST}/lwr.geojson.zip

echo "Unzip geojson responses"
unzip ${DIR_DEST}/lwr.geojson.zip
rm ${DIR_DEST}/lwr.geojson.zip

echo "Reproject geojson responses"
ogr2ogr -f 'GeoJSON' ${DIR_DEST}/lwr_3857.geojson ${DIR_DEST}/lwr.geojson -s_srs EPSG:4326 -t_srs EPSG:3857
rm ${DIR_DEST}/lwr.geojson
