#!/usr/bin/env bash

SCRATCH_DIR='/scratch/nfabina/gcrmn-benthic-classification/'

if [[ ! -d ${SCRATCH_DIR} ]]; then
    mkdir -p ${SCRATCH_DIR}
fi

mv ../data/for_application ${SCRATCH_DIR}
mv ../data ${SCRATCH_DIR}
