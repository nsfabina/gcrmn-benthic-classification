import os
import re

from gcrmnbc.utils import command_line, logs, paths
from tqdm import tqdm


_logger = logs.get_logger(__file__)


def create_sampling_boundary_shapefiles() -> None:
    _logger.info('Creating sampling boundary shapefiles for supplemental training data')
    # Get list of supplemental shapefiles
    tmp_filepath_raster = os.path.join(paths.DIR_DATA_TRAIN_RAW, 'tmp_raster_valid.tif')
    tmp_filepath_polygon = os.path.join(paths.DIR_DATA_TRAIN_RAW, 'tmp_outline_valid.shp')
    basename_polygon = os.path.splitext(os.path.basename(tmp_filepath_polygon))[0]
    filepaths_shapes = sorted([
        os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename) for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN)
        if filename.endswith('_model_class.shp')
    ])

    for filepath_shape in tqdm(filepaths_shapes, desc='Create sampling boundary shapefiles'):
        filepath_boundary = re.sub('.shp', 'boundaries.shp', filepath_shape)
        if os.path.exists(filepath_boundary):
            _logger.debug('Boundary file already exists at:  {}'.format(filepath_boundary))
            continue
        _logger.debug('Creating boundary file at:  {}'.format(filepath_boundary))

        _logger.debug('Creating valid sampling area raster')
        command = 'gdal_rasterize -burn 1 -tr 5 5 -a_nodata -9999 -init -9999 ' + \
                  '{filepath_shape} {tmp_filepath_raster}'
        command = command.format(filepath_shape=filepath_shape, tmp_filepath_raster=tmp_filepath_raster)
        command_line.run_command_line(command, _logger)

        _logger.debug('Creating valid sampling area outline')
        command = 'gdal_polygonize.py {} {}'.format(tmp_filepath_raster, tmp_filepath_polygon)
        command_line.run_command_line(command, _logger)

        _logger.debug('Creating buffered outline for boundary file')
        command = 'ogr2ogr -f "ESRI Shapefile" {filepath_boundary} {tmp_filepath_polygon} -dialect sqlite ' + \
                  '-sql "select ST_buffer(geometry, 64) as geometry from {basename_polygon}"'
        command = command.format(
            filepath_boundary=filepath_boundary, tmp_filepath_polygon=tmp_filepath_polygon,
            basename_polygon=basename_polygon
        )
        command_line.run_command_line(command, _logger)

        _logger.debug('Remove temporary files')
        os.remove(tmp_filepath_raster)
        for extension in ('.dbf', '.prj', '.shp', '.shx'):
            os.remove(os.path.join(paths.DIR_DATA_TRAIN_RAW, basename_polygon + extension))


if __name__ == '__main__':
    create_sampling_boundary_shapefiles()

