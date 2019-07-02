#!/usr/bin/env bash

mkdir -p ../data/{dr,usvi}
rclone copy remote:imagery/gcrmn/dr ../data/dr
rclone copy remote:imagery/gcrmn/usvi ../data/usvi
