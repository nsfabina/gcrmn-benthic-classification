#!/usr/bin/env bash


set -e

echo "Download and clean all data"
echo "Currently, it takes hours/days to parse the shapefiles for raster quads. Do you want to continue?"
select yn in "Yes" "No"; do
    case ${yn} in
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

echo "Download training feature quads"
python ./data_acquisition/download_training_feature_quads.py

echo "Download gloal feature quads"
python ./data_acquisition/download_global_feature_quads.sh

echo "Remove alpha band from features"
python ./data_cleaning/remove_feature_rasters_alpha_band.py

echo "Rasterize response shapefiles according to feature extents"
python ./data_cleaning/rasterize_response_quads.py

echo "Compress rasters for efficient reads"
python ./data_cleaning/compress_feature_response_rasters.py

echo "Create downsampled rasters"
python ./data_cleaning/downsample_feature_response_rasters.py

echo "Create class boundaries for response rasters"
python ./data_cleaning/create_response_boundary_classes.py

echo "Create shapefile boundaries for training data sampling"
python ./data_cleaning/create_sampling_boundary_shapefiles.py

echo "Download supplemental training data"
./data_acquisition/download_supplemental_shapefiles.sh

echo "Create supplemental response rasters"
python ./data_cleaning/create_supplemental_landwater_rasters.py
python ./data_cleaning/create_supplemental_allclasses_rasters.py

echo "Download UNEP evaluation data"
./data_acquisition/download_unep_from_fabina_gdrive.sh

echo "Create atlas reef multipolygons for evaluation"
python ./data_cleaning/create_evaluation_reef_multipolygons.py

echo "Copy feature quads for evaluation"
python ./data_cleaning/copy_evaluation_feature_quads.py
