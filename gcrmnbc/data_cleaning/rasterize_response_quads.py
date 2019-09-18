import logging
import os
import re
import shlex
import subprocess
import sys

import gdal
import osr

from gcrmnbc.utils import data_bucket, encodings


_logger = logging.getLogger(__file__)
_logger.setLevel('DEBUG')
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.FileHandler(__name__ + '.log')
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data'
DIR_DATA_TMP = os.path.join(DIR_DATA, 'tmp')
DIR_DATA_CLEAN = os.path.join(DIR_DATA, 'clean')


def rasterize_response_quads() -> None:
    _assert_encoding_assumptions_hold()
    filenames = [filename for filename in os.listdir(DIR_DATA_TMP) if filename.endswith('.shp')]
    for idx_filename, filename in enumerate(filenames):
        print('\rRasterizing shapefile {} of {}'.format(1+idx_filename, len(filenames)))
        # Get quad and filepaths
        quad = re.search(r'L15-\d{4}E-\d{4}N', filename).group()
        filepath_features = os.path.join(DIR_DATA_CLEAN, quad + data_bucket.FILENAME_SUFFIX_FEATURES)
        filepath_source_responses = os.path.join(DIR_DATA_TMP, filename)
        filepath_dest_responses = re.sub('feature', 'response', filepath_features)
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
        # Remove cloud-shade and unknown classes. Unknown classes could be anything from water to reef to clouds, while
        # cloud-shade is not reliable as the map was created with the analytical mosaic rather than the visual mosaic.
        min_nodata = min(encodings.MAPPINGS[encodings.CLOUD_SHADE], encodings.MAPPINGS[encodings.UNKNOWN])
        command = 'gdal_calc.py -A {filepath} --outfile {filepath} --NoDataValue=-9999 --overwrite --quiet ' + \
                  '--calc="A * (A < {min_nodata}) + -9999 * (A >= {min_nodata})"'
        command = command.format(filepath=filepath_dest_responses, min_nodata=min_nodata)
        subprocess.run(shlex.split(command))


def _assert_encoding_assumptions_hold():
    """
    We remove cloud-shade and unknown classes using the gdal_calc command within the rasterize operation. Currently,
    cloud-shade and unknown are both encoded as greater values than any other class, so we do a simple check to see if
    the raster values exceed a threshold. i.e., cloud-shade is 5 and unknown is 6 at the time of this writing, while
    land, water, and reef are all 1 through 4. If this changes, the gdal_calc command will fail.

    I'd put this function in the rasterize function, but I only want to check once and I want to keep this in an
    obvious place, rather than buried in a large function.
    """
    cloudshade = encodings.MAPPINGS[encodings.CLOUD_SHADE]
    unknown = encodings.MAPPINGS[encodings.UNKNOWN]
    max_other = max([value for key, value in encodings.MAPPINGS.items()
                     if key not in (encodings.CLOUD_SHADE, encodings.UNKNOWN)])
    assert cloudshade > max_other and unknown > max_other, 'Please see _assert_encoding_assumptions_hold for details'


if __name__ == '__main__':
    rasterize_response_quads()
