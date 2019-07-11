#!/usr/bin/env bash


if [[ ! -d ../data/for_application ]]; then
    mkdir -p ../data/for_application
fi

# The values for windows were identified with manual inspections in QGIS. Rather than exporting the slices of rasters
# in QGIS, the commands are implemented here in case data needs to be regenerated.

# Belize

gdal_translate \
  -projwin -87.63873041980676 17.482463910859426 -87.44335152626901 17.111584790277597 \
  ../data/belize/clean/features.vrt \
  ../data/for_application/belize_0.tif


# Hawaii

gdal_translate -projwin -155.84317857178934 20.048688656622172 -155.8211183520604 19.96927186559804 \
  ../data/hawaii/clean/features.vrt \
  ../data/for_application/hawaii_0.tif

gdal_translate -projwin -156.056637459833 19.838696374535868 -155.98310339406993 19.781339803240662 \
  ../data/hawaii/clean/features.vrt \
  ../data/for_application/hawaii_1.tif

gdal_translate -projwin -155.91786817287155 19.946161159215354 -155.8754285120597 19.876408845405795 \
  ../data/hawaii/clean/features.vrt \
  ../data/for_application/hawaii_2.tif


# Heron

gdal_translate -projwin 151.87553828821245 -23.403825350531292 152.05038113261605 -23.510567181088042 \
  ../data/heron/clean/features.vrt \
  ../data/for_application/heron_0.tif


# Karimunjawa

gdal_translate -projwin 110.39883791975102 -5.765096278457574 110.52079225418737 -5.90572058825006 \
  ../data/karimunjawa/clean/features.vrt \
  ../data/for_application/karimunjawa_0.tif

gdal_translate -projwin 110.11690416345574 -5.713882309361406 110.27568459607161 -5.829841697582493 \
  ../data/karimunjawa/clean/features.vrt \
  ../data/for_application/karimunjawa_1.tif


# Moorea

gdal_translate -projwin -149.929225855583 -17.46683590582376 -149.74953782288253 -17.509586961930943 \
  ../data/moorea/clean/features.vrt \
  ../data/for_application/karimunjawa_1.tif

gdal_translate -projwin -149.8910393653623 -17.56068783368406 -149.77547791682258 -17.607892124802405 \
  ../data/moorea/clean/features.vrt \
  ../data/for_application/karimunjawa_1.tif

gdal_translate -projwin -149.59400859011762 -17.734586660870033 -149.2938605503651 -17.799158568531922 \
  ../data/moorea/clean/features.vrt \
  ../data/for_application/karimunjawa_1.tif
