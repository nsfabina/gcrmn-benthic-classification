#!/usr/bin/env bash


set -e

./download_gbr_features_responses_from_fabina_gdrive.sh
./download_mvp_responses_from_fabina_gdrive.sh
./download_for_application_from_gcs_vulcan.sh
./copy_mvp_features_from_downloaded_mosaics.sh
./download_boundaries_from_fabina_gdrive.sh
./download_unep_from_fabina_gdrive.sh
