import os
import re

from osgeo import gdal, osr
from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def create_millennium_project_quad_rasters() -> None:
    _logger.info('Create Millennium Project response quad rasters')
    filenames_polys = [
        filename for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW_MP)
        if filename.startswith('L15-') and filename.endswith('responses.shp')
    ]
    for idx_filename, filename_poly in tqdm(enumerate(filenames_polys), desc='Create Millennium Project rasters'):
        _logger.debug('Create raster {} ({} total):  {}'.format(idx_filename, len(filenames_polys), filename_poly))
        # Set filepaths
        filepath_src = os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, filename_poly)
        filename_raster = re.sub('.shp', '.tif', filename_poly)
        filepath_dest = os.path.join(paths.DIR_DATA_TRAIN_CLEAN_MP, filename_raster)
        quad_name = re.search('L15-\d{4}E-\d{4}N', filename_poly).group()
        filepath_features = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, quad_name + '_features.tif')
        if os.path.exists(filepath_dest):
            continue

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

        # Rasterize each band for different attributes
        for idx_band, property in enumerate(('L1_CODE', 'L2_CODE', 'L3_CODE', 'L4_CODE', 'DEPTH_CODE')):
            command = \
                'gdal_rasterize -ot Int16 -co COMPRESS=DEFLATE -co TILED=YES -a_nodata -9999 -init -9999 ' \
                '-b {idx_band} -a {property} -te {llx} {lly} {urx} {ury} -tr {xres} {yres} -a_srs {srs} {src} {dest}'
            command = command.format(
                idx_band=idx_band, property=property, llx=llx, lly=lly, urx=urx, ury=ury, xres=xres, yres=yres,
                srs=srs, src=filepath_src, dest=filepath_dest
            )
            gdal_command_line.run_gdal_command(command, _logger)


if __name__ == '__main__':
    create_millennium_project_quad_rasters()
