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


# Data acquisition - order independent

echo "Download global feature quads"
python ./data_acquisition/download_global_feature_quads.sh

echo "Download training feature quads"
python ./data_acquisition/download_training_feature_quads.sh

echo "Download response geojson"
./data_acquisition/download_response_geojson_from_vulcan.sh

echo "Download supplemental training data"
./data_acquisition/download_supplemental_shapefiles.sh

echo "Download UNEP evaluation data"
./data_acquisition/download_unep_from_fabina_gdrive.sh

# Data cleaning - order dependent

# Needs global and training feature quads to be downloaded

echo "Copy feature quads for training and evaluation"
python ./data_cleaning/copy_evaluation_feature_quads.py

echo "Remove alpha band from features"
python ./data_cleaning/remove_feature_rasters_alpha_band.py

# Needs response geojson to be downloaded

echo "Remove response quads with no reef area"
python ./data_cleaning/remove_quad_files_with_no_reef.py

echo "Create shapefile 'quads' for responses to determine which feature quads are needed"
python ./data_cleaning/create_response_shapefile_quads.py

echo "Rasterize UQ and supplemental response quads"
python ./data_cleaning/create_response_rasters.py
python ./data_cleaning/create_supplemental_landwater_rasters.py
python ./data_cleaning/create_supplemental_allclasses_rasters.py

echo "Create shapefile boundaries for training data"
python ./data_cleaning/create_boundary_shapefiles_for_original_training_data.py
python ./data_cleaning/create_boundary_shapefiles_for_supplementary_training_data.py

# Needs all feature and response rasters to be cleaned

echo "Create downsampled rasters"
python ./data_cleaning/downsample_feature_response_rasters.py

# Needs files to be downsampled

echo "Create class boundaries for response rasters"
python ./data_cleaning/create_response_boundary_classes.py

# Needs evaluation feature data to be copied

echo "Create atlas reef multipolygons for evaluation"
python ./data_cleaning/create_evaluation_reef_multipolygons.py

# Needs everything complete

echo "Compress rasters for efficient reads"
python ./data_cleaning/compress_feature_response_rasters.py

