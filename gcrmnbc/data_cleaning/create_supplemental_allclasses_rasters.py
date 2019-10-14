import argparse
import os
import re

import gdal
import osr
from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)

SUFFIX_SUPPL = 'model_class.shp'
SUFFIX_FEAT = 'features.tif'
SUFFIX_RESP = 'model_class.tif'


def create_supplemental_allclasses_rasters(recalculate: bool) -> None:
    _logger.info('Create supplemental response rasters')
    filepaths_supplements = sorted([
        os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename) for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN)
        if filename.endswith(SUFFIX_SUPPL)
    ])
    for filepath_supplement in tqdm(filepaths_supplements, desc='Create supplemental training data rasters'):
        filepath_features = re.sub(SUFFIX_SUPPL, SUFFIX_FEAT, filepath_supplement)
        filepath_responses = re.sub(SUFFIX_SUPPL, SUFFIX_RESP, filepath_supplement)
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
        # Rasterize to responses filepath
        options_rasterize = gdal.RasterizeOptions(
            outputType=gdal.GDT_Int16, creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'], outputBounds=output_bounds,
            outputSRS=srs, xRes=xres, yRes=yres, noData=-9999, initValues=-9999, attribute='dn',
        )
        gdal.Rasterize(filepath_responses, filepath_supplement, options=options_rasterize)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--recalculate', action='store_true')
    args = parser.parse_args()
    create_supplemental_allclasses_rasters(args.recalculate)
