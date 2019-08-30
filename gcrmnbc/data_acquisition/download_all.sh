#!/usr/bin/env bash


set -e

raise error "Update copy_mvp_features to be download_mvp_features and update paths for new Vulcan buckets"

./download_gbr_features_responses_from_fabina_gdrive.sh
./copy_mvp_features_from_downloaded_mosaics.sh
./download_mvp_responses_from_fabina_gdrive.sh
./download_boundaries_from_fabina_gdrive.sh
./download_unep_from_fabina_gdrive.sh
