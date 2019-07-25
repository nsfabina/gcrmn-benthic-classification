#!/usr/bin/env bash


set -e

GDRIVE_PATH="/data/unep/WCMC008_CoralReefs2018_v4.zip"
SCRATCH_BASE="/scratch/nfabina/gcrmn-benthic-classification"


if [[ ! -d "${SCRATCH_BASE}" ]]; then
    mkdir -p "${SCRATCH_BASE}"
fi

rclone copy "remote:${GDRIVE_PATH}" "${SCRATCH_BASE}"
unzip "${SCRATCH_BASE}/WCMC008_CoralReefs2018_v4.zip" -d "${SCRATCH_BASE}/unep"
rm "${SCRATCH_BASE}/WCMC008_CoralReefs2018_v4.zip"
