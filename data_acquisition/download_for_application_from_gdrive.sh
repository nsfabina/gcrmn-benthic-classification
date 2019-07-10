#!/usr/bin/env bash


if [[ ! -d ../data/for_application ]]; then
  mkdir -p ../data/for_application
fi

rclone copy -v remote:imagery/gcrmn/for_application ../data/for_application/
