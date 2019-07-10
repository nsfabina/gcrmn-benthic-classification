#!/usr/bin/env bash


if [[ ! -d /scratch/nfabina/gcrmn-benthic-classification/for_application ]]; then
    mkdir -p /scratch/nfabina/gcrmn-benthic-classification/for_application
fi

rclone copy -v remote:imagery/gcrmn/for_application /scratch/nfabina/gcrmn-benthic-classification/for_application/
