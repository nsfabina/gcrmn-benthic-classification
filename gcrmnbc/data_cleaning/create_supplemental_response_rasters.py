import argparse
import os
import re

import gdal
import osr

from gcrmnbc.utils import encodings, logs, paths


_logger = logs.get_logger(__file__)

SUFFIX_LAND = '_land.shp'
SUFFIX_WATER = '_water.shp'


def create_supplemental_response_rasters(recalculate: bool) -> None:
    _logger.info('Create supplemental response rasters')
    filepaths_boundaries = sorted([
        os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename) for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN)
        if any([filename.endswith(suffix) for suffix in (SUFFIX_LAND, SUFFIX_WATER)])
    ])
    for idx, filepath_boundary in enumerate(filepaths_boundaries):
        _logger.debug('Processing raster {} of {}'.format(1+idx, len(filepaths_boundaries)))
        filepath_features = re.sub(r'_\w*\.shp', '_features.tif', filepath_boundary)
        filepath_responses = re.sub(r'\.shp', '.tif', filepath_boundary)
        if os.path.exists(filepath_responses) and not recalculate:
            _logger.debug('Skipping, raster already processed')
            continue
        # Get rasterize parameters from existing features file
        raster_features = gdal.Open(filepath_features)
        srs = osr.SpatialReference(wkt=raster_features.GetProjection())
        cols = raster_features.RasterXSize
        rows = raster_features.RasterYSize
        llx, xres, _, y0, _, yres = raster_features.GetGeoTransform()
        urx = llx + cols * xres
        y1 = y0 + rows * yres
        lly = min([y0, y1])
        ury = max([y0, y1])
        output_bounds = (llx, lly, urx, ury)
        if filepath_boundary.endswith(SUFFIX_LAND):
            burn_value = encodings.MAPPINGS[encodings.LAND]
        elif filepath_boundary.endswith(SUFFIX_WATER):
            burn_value = encodings.MAPPINGS[encodings.WATER]
        else:
            raise AssertionError('Filepath does not end with land or water pattern, need to specify burn value')
        # Rasterize to responses filepath
        options_rasterize = gdal.RasterizeOptions(
            outputType=gdal.GDT_Int16, creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'], outputBounds=output_bounds,
            outputSRS=srs, xRes=xres, yRes=yres, noData=-9999, initValues=-9999, burnValues=burn_value,
        )
        gdal.Rasterize(filepath_responses, filepath_boundary, options=options_rasterize)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--recalculate', action='store_true')
    args = parser.parse_args()
    create_supplemental_response_rasters(args.recalculate)

