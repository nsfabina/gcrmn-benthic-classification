#!/usr/bin/env bash


if [[ ! -d ../data/for_application ]]; then
    mkdir -p ../data/for_application
fi

# The values for windows were identified with manual inspections in QGIS. Rather than exporting the slices of rasters
# in QGIS, the commands are implemented here in case data needs to be regenerated.

# Belize

gdal_translate \
  -projwin -87.650 17.100 -87.450 17.500 \
  ../data/belize/clean/features.vrt \
  ../data/for_application/belize_0.tif


# Hawaii

gdal_translate -projwin -155.844 19.970 -155.820 20.0480 \
  ../data/hawaii/clean/features.vrt \
  ../data/for_application/hawaii_0.tif

gdal_translate -projwin -156.057 19.780 -155.980 19.840 \
  ../data/hawaii/clean/features.vrt \
  ../data/for_application/hawaii_1.tif

gdal_translate -projwin -155.918 19.876 -155.875 19.947 \
  ../data/hawaii/clean/features.vrt \
  ../data/for_application/hawaii_2.tif


# Heron

gdal_translate -projwin 151.876 -23.511 152.051 -23.403 \
  ../data/heron/clean/features.vrt \
  ../data/for_application/heron_0.tif


# Karimunjawa

gdal_translate -projwin 110.398 -5.906 110.521 -5.764 \
  ../data/karimunjawa/clean/features.vrt \
  ../data/for_application/karimunjawa_0.tif

gdal_translate -projwin 110.116 -5.830 110.276 -5.713 \
  ../data/karimunjawa/clean/features.vrt \
  ../data/for_application/karimunjawa_1.tif


# Moorea

gdal_translate -projwin -149.929 -17.510 -149.749 -17.466 \
  ../data/moorea/clean/features.vrt \
  ../data/for_application/moorea_0.tif

gdal_translate -projwin -149.891 -17.608 -149.775 -17.560 \
  ../data/moorea/clean/features.vrt \
  ../data/for_application/moorea_1.tif

gdal_translate -projwin -149.593 -17.800 -149.293 -17.734 \
  ../data/moorea/clean/features.vrt \
  ../data/for_application/moorea_2.tif
