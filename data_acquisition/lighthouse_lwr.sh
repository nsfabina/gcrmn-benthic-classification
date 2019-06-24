#!/usr/bin/env bash

mkdir ../data
curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson \
  -o ../data/lighthouse.geojson
