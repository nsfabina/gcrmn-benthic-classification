import os
import re

from tqdm import tqdm

from gcrmnbc.utils import encodings_mp, gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def create_sampling_boundary_shapefiles() -> None:
    _logger.info('Creating sampling boundary shapefiles for Millennium Project training data')
    filenames_responses = sorted([
        filename for filename in os.listdir(paths.DIR_DATA_TRAIN_MP_CLEAN) if filename.endswith('_responses_custom.tif')
    ])

    desc = 'Create sampling boundary shapefiles'
    for idx_filepath, filename_response in enumerate(tqdm(filenames_responses, desc=desc)):
        filepath_response = os.path.join(paths.DIR_DATA_TRAIN_MP_CLEAN, filename_response)
        tmp_filename_raster = re.sub('_responses_custom.tif', '_tmp_noland.tif', filename_sqlvalid)
        tmp_filepath_raster = os.path.join(paths.DIR_DATA_TRAIN_MP_BOUNDS, tmp_filename_raster)
        tmp_filename_outline = re.sub('_responses_custom.tif', '_tmp_noland.shp', filename_sqlvalid)
        tmp_filepath_outline = os.path.join(paths.DIR_DATA_TRAIN_MP_BOUNDS, tmp_filename_outline)
        basename_outline = os.path.splitext(os.path.basename(tmp_filepath_outline))[0]
        filename_boundary = re.sub('_responses_custom.tif', '_boundaries.shp', filename_response)
        filepath_boundary = os.path.join(paths.DIR_DATA_TRAIN_MP_BOUNDS, filename_boundary)
        filename_sqlvalid = re.sub('-', '_', os.path.basename(filepath_response))
        filepath_lock = filepath_boundary + '.lock'
        if os.path.exists(filepath_boundary):
            _logger.debug('Boundary file already exists at:  {}'.format(filepath_boundary))
            continue
        if os.path.exists(filepath_lock):
            _logger.debug('Boundary file already being processed:  {}'.format(filepath_boundary))
            continue

        try:
            file_lock = open(filepath_lock, 'x')
        except OSError:
            continue

        _logger.debug('Creating boundary file {} ({} total):  {}'.format(
            idx_filepath, len(filepaths_responses), filepath_response
        ))

        try:
            # Get raster of areas we care about, those that are not land
            _logger.debug('Creating non-land raster')
            code_land = encodings_mp.CODE_LAND
            command = 'gdal_calc.py -A {filepath_response} --outfile={tmp_raster} --NoDataValue=-9999 ' + \
                      '--calc="1*(A!={code_land}) + -9999*(A=={code_land})"'
            command = command.format(
                filepath_response=filepath_response, tmp_raster=tmp_filepath_raster, code_land=code_land)
            gdal_command_line.run_gdal_command(command, _logger)

            # Get shapefile for outline of areas we care about
            _logger.debug('Creating non-land outline shapefile')
            command = 'gdal_polygonize.py {} {}'.format(tmp_filepath_raster, tmp_filepath_outline)
            gdal_command_line.run_gdal_command(command, _logger)

            # Get shapefile of sampling boundaries by buffering reef outline
            _logger.debug('Creating buffered outline for boundary file')
            command = 'ogr2ogr -f "ESRI Shapefile" {filepath_boundary} {tmp_outline} -dialect sqlite ' + \
                      '-sql "select ST_buffer(geometry, 64) as geometry from {basename_outline}"'
            command = command.format(
                filepath_boundary=filepath_boundary, tmp_outline=tmp_filepath_outline, basename_outline=basename_outline
            )
            gdal_command_line.run_gdal_command(command, _logger)
        except Exception as error_:
            raise error_
        finally:
            if os.path.exists(tmp_filepath_raster):
                os.remove(tmp_filepath_raster)
            for filename in os.listdir(os.path.dirname(tmp_filepath_outline)):
                if not re.search(basename_outline, filename):
                    continue
                os.remove(os.path.join(os.path.dirname(tmp_filepath_outline), filename))
            file_lock.close()
            os.remove(filepath_lock)


if __name__ == '__main__':
    create_sampling_boundary_shapefiles()
