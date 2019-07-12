#!/usr/bin/env bash

SCRATCH_DIR='/scratch/nfabina/gcrmn-benthic-classification/'

if [[ ! -d ${SCRATCH_DIR}/data ]]; then
    mkdir -p ${SCRATCH_DIR}/data
fi

if [[ ! -d ${SCRATCH_DIR}/for_application ]]; then
    mkdir -p ${SCRATCH_DIR}/for_application
fi

mv ../data/for_application/* ${SCRATCH_DIR}/for_application
rmdir ../data/for_application
mv ../data/* ${SCRATCH_DIR}/data
rmdir ../data

