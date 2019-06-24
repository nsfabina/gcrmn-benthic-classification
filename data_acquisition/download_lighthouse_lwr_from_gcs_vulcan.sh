#!/usr/bin/env bash

mkdir ../data/lighthouse
curl https://storage.googleapis.com/coral-atlas-data-share/geojson/lighthouse.geojson \
  -o ../data/lighthouse/lwr.geojson
