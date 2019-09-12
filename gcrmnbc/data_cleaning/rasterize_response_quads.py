import logging
import os
import re

import gdal
import osr

from gcrmnbc.utils import data_bucket


_logger = logging.getLogger(__name__)
_logger.setLevel('DEBUG')
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.FileHandler('rasterize_response_quads.log')
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data'
DIR_DATA_TMP = os.path.join(DIR_DATA, 'tmp')
DIR_DATA_CLEAN = os.path.join(DIR_DATA, 'clean')


def rasterize_response_quads() -> None:
    filenames = [filename for filename in os.listdir(DIR_DATA_TMP) if filename.endswith('.shp')]
    for idx_filename, filename in enumerate(filenames):
        print('\rRasterizing shapefile {} of {}'.format(1+idx_filename, len(filenames)))
        # Get quad and filepaths
        quad = re.search(r'L15-\d{4}E-\d{4}N', filename).group()
        filepath_features = os.path.join(DIR_DATA_CLEAN, quad + data_bucket.FILENAME_SUFFIX_FEATURES)
        filepath_source_responses = os.path.join(DIR_DATA_TMP, filename)
        filepath_dest_responses = re.sub('features', 'responses', filepath_features)
        assert os.path.exists(filepath_features), 'Download all feature quads before rasterizing response quads'
        # Get rasterize parameters
        raster_features = gdal.Open(filepath_features)
        srs = osr.SpatialReference(wkt=raster_features.GetProjection())
        cols = raster_features.RasterXSize
        rows = raster_features.RasterYSize
        llx, xres, _, y0, _, yres = raster_features.GetGeoTransform()
        urx = llx + cols * xres
        y1 = y0 + rows * yres
        lly = min([y0, y1])
        ury = max([y0, y1])
        # Rasterize
        options_rasterize = gdal.RasterizeOptions(
            outputType=gdal.GDT_Int16, creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'],
            outputBounds=[llx, lly, urx, ury], outputSRS=srs, xRes=xres, yRes=yres, noData=-9999, initValues=-9999,
            attribute='class_code'
        )
        raster_out = gdal.Rasterize(filepath_dest_responses, filepath_source_responses, options=options_rasterize)
        del raster_out
