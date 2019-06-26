#!/usr/bin/env bash


URL_ACA='gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/caribbean/west-caribbean'

# Create data directory, if necessary
if [[ ! -d ../data/belize ]]; then
  mkdir -p ../data/belize
fi
cd ../data/belize


echo "Downloading Lighthouse Reef imagery"

for LAT in 0525E 0526E; do
  for LON in 1122N 1123N 1124N 1125N; do

    FILENAME=L15-${LAT}-${LON}.tif
    if [[ ! -f ${FILENAME} ]]; then
      echo "Downloading ${FILENAME}"
      gsutil cp ${URL_ACA}/${FILENAME} tmp_0_${FILENAME}
      # Note that mosaics come in different projections than individual scenes
      echo "Reprojecting ${FILENAME}"
      gdalwarp -s_srs EPSG:3857 -t_srs EPSG:4326 tmp_0_${FILENAME} tmp_1_${FILENAME}
      # Note that we only need / want the blue and green bands
      gdal_translate -b 1 -b 2 -a_nodata -9999 tmp_1_${FILENAME} ${FILENAME}
      rm tmp_0_${FILENAME} tmp_1_${FILENAME}
    else
      echo "File already exists at ${FILENAME}"
    fi

  done
done


echo "Building imagery VRT"

if [[ ! -f features.vrt ]]; then
  # Note that it's easier to use a vrt than to assemble paired features/responses manually
  gdalbuildvrt features.vrt L15-052*.tif
else
  echo "VRT already built and reprojected"
fi


echo "Download reef LWR classes"

if [[ ! -f lwr.tif ]]; then

  curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson \
    -o tmp_0.geojson

  # Note that the lwr_class key with string values causes issues with the SQL in rasterization, so we convert that to
  # the lwr key with integer values
  echo "Format reef LWR classes"
  sed 's/"lwr_class": "Land"/"lwr": 1/g' tmp_0.geojson > tmp_1.geojson
  sed 's/"lwr_class": "Reef"/"lwr": 3/g' tmp_1.geojson > tmp_2.geojson
  sed 's/"lwr_class": "Deep Reef Water 10m+"/"lwr": 2/g' tmp_2.geojson > tmp_3.geojson
  sed 's/"lwr_class": "Cloud-Shade"/"lwr": 4/g' tmp_3.geojson > lwr.geojson

  echo "Rasterize reef LWR classes"
  # Note that these values are taken from the feature vrt and are hardcoded rather than referenced dynamically
  gdal_rasterize \
    -init -9999 \
    -a_nodata -9999 \
    -te -87.3632814 16.9727394 -87.7148437 17.6440220 \
    -ts 8380 16001 \
    -a lwr \
    lwr.geojson responses.tif

  rm tmp_0.geojson tmp_1.geojson tmp_2.geojson tmp_3.geojson lwr.geojson
else
  echo "Reef LWR classes already available"
fi

