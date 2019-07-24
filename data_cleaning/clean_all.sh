#!/usr/bin/env bash


set -e

./clean_gbr_training_data.sh
./clean_vulcan_formatted_training_data.sh
./create_performance_evaluation_rasters.sh
