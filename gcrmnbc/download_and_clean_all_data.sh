#!/usr/bin/env bash


set -e

echo "Download and clean all data"

echo "Download response geojson"
./data_acquisition_responses/download_response_geojson_from_vulcan.sh

echo "Create shapefile 'quads' for responses to determine which feature quads are needed"
./data_cleaning/create_response_shapefile_quads.py

echo "Download feature quads"
./data_acquisition_features/download_feature_quads.py

echo "Rasterize response shapefiles according to feature extents"
./data_cleaning/rasterize_response_quads.py



