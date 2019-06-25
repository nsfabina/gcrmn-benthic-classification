#!/usr/bin/env bash


URL_ACA=gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/caribbean/west-caribbean

# Create data directory, if necessary
if [ ! -d ../data/lighthouse ]; then
  mkdir ../data/lighthouse
fi
cd ../data/lighthouse


echo "Downloading Lighthouse Reef imagery"

for LAT in 0525E 0526E; do
  for LON in 1122N 1123N 1124N 1125N; do

    FILENAME=L15-${LAT}-${LON}.tif
    if [[ ! -f ${FILENAME} ]]; then
      echo "Downloading ${FILENAME}"
      gsutil cp ${URL_ACA}/${FILENAME} ../data/lighthouse/tmp_${FILENAME}
      echo "Reprojecting ${FILENAME}"
      gdalwarp -s_srs EPSG:3857 -t_srs EPSG:4326 tmp_${FILENAME} ${FILENAME}
      rm tmp_${FILENAME}
    else
      echo "File already exists at ${FILENAME}"
    fi

  done
done


echo "Building imagery VRT"

if [ ! -f features.vrt ]; then
  gdalbuildvrt features.vrt L15-052*.tif
else
  echo "VRT already built and reprojected"
fi


echo "Download reef LWR classes"

if [! -f lwr.tif ]; then

  curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson \
    -o tmp_0.geojson

  echo "Format reef LWR classes"
  sed 's/"lwr_class": "Land"/"lwr": 1/g' tmp_0.geojson > tmp_1.geojson
  sed 's/"lwr_class": "Reef"/"lwr": 3/g' tmp_1.geojson > tmp_2.geojson
  sed 's/"lwr_class": "Deep Reef Water 10m+"/"lwr": 2/g' tmp_2.geojson > tmp_3.geojson
  sed 's/"lwr_class": "Cloud-Shade"/"lwr": 4/g' tmp_3.geojson > lwr.geojson

  echo "Rasterize reef LWR classes"
  gdal_rasterize \
    -te -87.3632814 16.9727394 -87.7148437 17.6440220 \
    -ts 8380 16001 \
    -a lwr \
    lwr.geojson responses.tif

  rm tmp_0.geojson tmp_1.geojson tmp_2.geojson tmp_3.geojson lwr.geojson
else
  echo "Reef LWR classes already available"
fi

