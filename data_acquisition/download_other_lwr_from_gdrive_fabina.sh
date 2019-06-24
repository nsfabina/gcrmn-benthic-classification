#!/usr/bin/env bash

mkdir ../data
rclone copy remote:imagery/gcrmn/dr ../data/
rclone copy remote:imagery/gcrmn/usvi ../data/
