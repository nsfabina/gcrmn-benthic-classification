import os
import re

from tqdm import tqdm

from gcrmnbc.utils import encodings_mp, gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def create_sampling_boundary_shapefiles() -> None:
    _logger.info('Creating sampling boundary shapefiles for Millennium Project training data')
    # Get list of completed depth rasters with associated responses
    tmp_filepath_raster = os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, 'tmp_reef_only.tif')
    tmp_filepath_outline = os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, 'tmp_reef_outline.shp')
    filepaths_depths = sorted([
        os.path.join(paths.DIR_DATA_TRAIN_CLEAN_MP, filename) for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN_MP)
        if filename.endswith('_responses_DEPTH_CODE.tif')
    ])

    desc = 'Create sampling boundary shapefiles'
    for idx_filepath, filepath_depth in enumerate(tqdm(filepaths_depths, desc=desc)):
        filepath_boundary = re.sub('_responses_DEPTH_CODE.tif', '_boundaries.shp', filepath_depth)
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
            idx_filepath, len(filepaths_depths), filepath_depth
        ))

        try:
            # Get raster of non-land areas
            _logger.debug('Creating non-land raster')
            code_land = [code for code, attr in encodings_mp.MAPPINGS_DEPTH.items() if attr == 'land'][0]
            command = 'gdal_calc.py -A {filepath_depth} --outfile={tmp_raster} --NoDataValue=-9999 ' + \
                      '--calc="1*(A!={code_land}) + -9999*(A=={code_land})"'
            command = command.format(filepath_depth=filepath_depth, tmp_raster=tmp_filepath_raster, code_land=code_land)
            gdal_command_line.run_gdal_command(command, _logger)

            # Get shapefile of reef outline
            _logger.debug('Creating reef outline shapefile')
            command = 'gdal_polygonize.py {} {}'.format(tmp_filepath_raster, tmp_filepath_outline)
            gdal_command_line.run_gdal_command(command, _logger)

            # Get shapefile of sampling boundaries by buffering reef outline
            _logger.debug('Creating buffered outline for boundary file')
            basename_outline = os.path.splitext(os.path.basename(tmp_filepath_outline))[0]
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
            for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW):
                if not re.search(basename_outline, filename):
                    continue
                os.remove(os.path.join(paths.DIR_DATA_TRAIN_RAW, filename))
            file_lock.close()
            os.remove(filepath_lock)


if __name__ == '__main__':
    create_sampling_boundary_shapefiles()
