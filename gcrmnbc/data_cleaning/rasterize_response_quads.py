import os
import re
import shlex
import subprocess

import gdal
import osr

from gcrmnbc.utils import data_bucket, encodings, logs


_logger = logs.get_logger(__file__)

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
        filepath_dest_lwr = re.sub('features.tif', 'responses_lwr.tif', filepath_features)
        filepath_dest_lwrn = re.sub('features.tif', 'responses_lwrn.tif', filepath_features)
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
        # Rasterize into Land-Water-Reef-NotReef
        options_rasterize = gdal.RasterizeOptions(
            outputType=gdal.GDT_Int16, creationOptions=['COMPRESS=DEFLATE', 'TILED=YES'],
            outputBounds=[llx, lly, urx, ury], outputSRS=srs, xRes=xres, yRes=yres, noData=-9999, initValues=-9999,
            attribute='class_code'
        )
        raster_out = gdal.Rasterize(filepath_dest_lwrn, filepath_source_responses, options=options_rasterize)
        del raster_out
        # Remove cloud-shade and unknown classes. Unknown classes could be anything from water to reef to clouds, while
        # cloud-shade is not reliable as the map was created with the analytical mosaic rather than the visual mosaic.
        min_nodata = min(encodings.MAPPINGS[encodings.CLOUD_SHADE], encodings.MAPPINGS[encodings.UNKNOWN])
        command = 'gdal_calc.py -A {filepath} --outfile {filepath} --NoDataValue=-9999 --overwrite ' + \
                  '--calc="A * (A < {min_nodata}) + -9999 * (A >= {min_nodata})"'
        command = command.format(filepath=filepath_dest_lwrn, min_nodata=min_nodata)
        completed = subprocess.run(shlex.split(command), capture_output=True)
        if completed.stderr:
            _logger.error('gdalinfo stdout:  {}'.format(completed.stdout.decode('utf-8')))
            _logger.error('gdalinfo stderr:  {}'.format(completed.stderr.decode('utf-8')))
            raise AssertionError('Unknown error in removing cloud-shade/unknown, see above log lines')
        # Create Land-Water-Reef
        val_reef = encodings.MAPPINGS[encodings.REEF_TOP]
        val_notreef = encodings.MAPPINGS[encodings.NOT_REEF_TOP]
        command = 'gdal_calc.py -A {filepath_lwrn} --outfile={filepath_lwr} --NoDataValue=-9999 --overwrite ' + \
                  '--calc="A * (A != {val_notreef}) + {val_reef} * (A == {val_notreef})"'
        command = command.format(
            filepath_lwrn=filepath_dest_lwrn, filepath_lwr=filepath_dest_lwr, val_notreef=val_notreef,
            val_reef=val_reef
        )
        completed = subprocess.run(shlex.split(command), capture_output=True)
        if completed.stderr:
            _logger.error('gdalinfo stdout:  {}'.format(completed.stdout.decode('utf-8')))
            _logger.error('gdalinfo stderr:  {}'.format(completed.stderr.decode('utf-8')))
            raise AssertionError('Unknown error in LWR creation, see above log lines')


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
