#!/usr/bin/env bash

# These commands were used to convert files to the correct formats and extents

if [[ ! -d ../data/gbr/tmp ]]; then
  mkdir -p ../data/gbr/tmp
fi
if [[ ! -d ../data/gbr/clean ]]; then
  mkdir -p ../data/gbr/clean
fi
cd ../data/gbr

# To convert files to the correct projection
gdalwarp -t_srs EPSG:28355 -tr 5 -5 raw/benthic.tif tmp/benthic_proj.tif
gdalwarp -t_srs EPSG:28355 -tr 5 -5 raw/geomorphic.tif tmp/geomorphic_proj.tif
gdalwarp -t_srs EPSG:28355 -tr 5 -5 raw/depth.tif tmp/depth_proj.tif
gdalwarp -t_srs EPSG:28355 -tr 5 -5 raw/rrs.tif tmp/rrs_proj.tif

# To convert missing or uninformative values to null
# To convert Dove rrs to B/G bands and null values from 0 to -9999, while being defensive about bad data
gdal_translate tmp/rrs_proj.tif tmp/rrs_bands.tif -b 1 -b 2
gdal_calc.py -A tmp/rrs_bands.tif --allBands=A --calc="A*(A>0)-9999*(numpy.logical_or(A<=0, ~numpy.isfinite(A)))" --NoDataValue=-9999 --outfile=tmp/rrs_null.tif
# To convert depth null values from nan to -9999, while being defensive about bad data
gdal_calc.py -A tmp/depth_proj.tif --allBands=A --calc="A*(A>0)-9999*(numpy.logical_or(A<=0, ~numpy.isfinite(A)))" --NoDataValue=-9999 --outfile=tmp/depth_null.tif
# To convert benthic 0 values (deep water related) to -9999
gdal_calc.py -A tmp/benthic_proj.tif --allBands=A --calc="A*(A>0.5)-9999*(numpy.logical_or(A<=0.5, ~numpy.isfinite(A)))" --NoDataValue=-9999 --outfile=tmp/benthic_null.tif
# To convert geomorphic 0 and 1 values (deep water related) to -9999
gdal_calc.py -A tmp/geomorphic_proj.tif --allBands=A --calc="A*(A>1.5)-9999*(numpy.logical_or(A<=1.5, ~numpy.isfinite(A)))" --NoDataValue=-9999 --outfile=tmp/geomorphic_null.tif

# To match the feature extents to the response extents
python match_extent.py tmp/rrs_null.tif tmp/benthic_null.tif tmp/rrs_match.tif
python match_extent.py tmp/depth_null.tif tmp/benthic_null.tif clean/depth.tif
python match_extent.py tmp/geomorphic_null.tif tmp/benthic_null.tif tmp/geomorphic_match.tif

# To apply depth mask to features and responses
gdal_calc.py -A tmp/rrs_match.tif -B clean/depth.tif --allBands=A --calc="A*(B>0)-9999*(numpy.logical_or(B<=0, ~numpy.isfinite(B)))" --NoDataValue=-9999 --outfile=clean/rrs.tif
gdal_calc.py -A tmp/geomorphic_match.tif -B clean/depth.tif --allBands=A --calc="A*(B>0)-9999*(numpy.logical_or(B<=0, ~numpy.isfinite(B)))" --NoDataValue=-9999 --outfile=clean/geomorphic.tif
gdal_calc.py -A tmp/benthic_null.tif -B clean/depth.tif --allBands=A --calc="A*(B>0)-9999*(numpy.logical_or(B<=0, ~numpy.isfinite(B)))" --NoDataValue=-9999 --outfile=clean/benthic.tif

# To combine the rasters for features
gdal_merge.py -separate -o clean/rrs_depth.tif clean/rrs.tif clean/depth.tif
gdal_merge.py -separate -o clean/rrs_depth_geomorphic.tif clean/rrs_depth.tif clean/geomorphic.tif
https://github.com/mitchest/coral-atlas/blob/master/class_renaming/dbf_renaming_functions.R


  x$class_num[grepl("Ignore",x$glob_class)] <- 0
  x$class_num[grepl("Land",x$glob_class)] <- 1
  x$class_num[grepl("Deep",x$glob_class)] <- 2
  if (use_turbid) {
    x$class_num[grepl("Turbid",x$glob_class)] <- 3
  } else {
    x$class_num[grepl("Turbid",x$glob_class)] <- 0
  }
  x$class_num[grepl("Shallow Lagoon",x$glob_class)] <- 11
  x$class_num[grepl("Deep Lagoon",x$glob_class)] <- 12
  x$class_num[grepl("Inner Reef Flat",x$glob_class)] <- 13
  x$class_num[grepl("Outer Reef Flat",x$glob_class)] <- 14
  x$class_num[grepl("Reef Rim",x$glob_class)] <- 15
  x$class_num[grepl("Reef Flat Terrestrial",x$glob_class)] <- 16
  x$class_num[grepl("Slope Sheltered",x$glob_class)] <- 21
  x$class_num[grepl("Slope Exposed",x$glob_class)] <- 22
  x$class_num[grepl("Plateau",x$glob_class)] <- 23
  x$class_num[grepl("Open Comlex Lagoon",x$glob_class)] <- 24
  x$class_num[grepl("Patch Reef",x$glob_class)] <- 25
  x$class_num[grepl("Small Reef",x$glob_class)] <- 26





  x$class_num[grepl("Ignore",x$glob_class)] <- 0
  x$class_num[grepl("Land",x$glob_class)] <- 1
  x$class_num[grepl("Temporal",x$glob_class)] <- 2 ## "temporal classes that have not been updated to mapping date/capture time (turbid, waves etc.)
  if (use_turbid) {
    x$class_num[grepl("Turbid",x$glob_class)] <- 0
  } else {
    x$class_num[grepl("Turbid",x$glob_class)] <- 2
  }
  x$class_num[grepl("Mangrove",x$glob_class)] <- 3
  x$class_num[grepl("Mud",x$glob_class)] <- 4
  x$class_num[grepl("Sand",x$glob_class)] <- 11
  x$class_num[grepl("Rubble",x$glob_class)] <- 12
  x$class_num[grepl("Rock",x$glob_class)] <- 13
  x$class_num[grepl("Seagrass",x$glob_class)] <- 14
  x$class_num[grepl("Cor_Alg",x$glob_class)] <- 15
  x$class_num[grepl("Coral",x$glob_class)] <- 16
  x$class_num[grepl("Algae",x$glob_class)] <- 17



