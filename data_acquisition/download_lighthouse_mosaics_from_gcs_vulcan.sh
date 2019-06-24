#!/usr/bin/env bash

URL_ACA=gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/caribbean/west-caribbean

mkdir ../data/lighthouse
for LAT in 0525E 0526E; do
  for LON in 1122N 1123N 1124N 1125N; do
    gsutil cp $URL_ACA/L15-${LAT}-${LON}.tif ../data/lighthouse/
  done
done
