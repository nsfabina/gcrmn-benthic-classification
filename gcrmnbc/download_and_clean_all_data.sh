#!/usr/bin/env bash


set -e

echo "Download and clean all data"
echo "Currently, it takes hours/days to parse the shapefiles for raster quads. Do you want to continue?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

echo "Download response geojson"
./data_acquisition/download_response_geojson_from_vulcan.sh

echo "Create shapefile 'quads' for responses to determine which feature quads are needed"
python ./data_cleaning/create_response_shapefile_quads.py

echo "Remove response quads with no reef area"
python ./data_cleaning/remove_quad_files_with_no_reef.py

echo "Download feature quads"
python ./data_acquisition/download_feature_quads.py

echo "Rasterize response shapefiles according to feature extents"
python ./data_cleaning/rasterize_response_quads.py

echo "Create shapefile boundaries for training data sampling"
python ./data_cleaning/create_sampling_boundary_shapefiles.py

echo "Download UNEP evaluation data"
./data_acquisition/download_unep_from_fabina_gdrive.sh
