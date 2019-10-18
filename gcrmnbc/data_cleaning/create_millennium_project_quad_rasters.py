import os
import re

from osgeo import gdal
from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


ATTRIBUTES = ('L3_CODE', 'L4_CODE', 'DEPTH_CODE')


def create_millennium_project_quad_rasters() -> None:
    _logger.info('Create Millennium Project response quad rasters')
    if not os.path.exists(paths.DIR_DATA_TRAIN_CLEAN_MP):
        os.makedirs(paths.DIR_DATA_TRAIN_CLEAN_MP)
    filenames_polys = [
        filename for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW_MP)
        if filename.startswith('L15-') and filename.endswith('responses.shp')
    ]
    missing_features = list()
    for idx_filename, filename_poly in enumerate(tqdm(filenames_polys, desc='Create Millennium Project rasters')):
        _logger.debug('Create raster {} ({} total):  {}'.format(idx_filename, len(filenames_polys), filename_poly))
        # Set filepaths
        filepath_src = os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, filename_poly)
        filename_raster = re.sub('.shp', '_{}.tif', filename_poly)
        filepath_dest = os.path.join(paths.DIR_DATA_TRAIN_CLEAN_MP, filename_raster)
        all_exist = all([os.path.exists(filepath_dest.format(attribute)) for attribute in ATTRIBUTES])
        if all_exist:
            continue

        # Try to find existing features file, may be either raw or clean, but also may not be available from Vulcan
        filename_features = re.search(r'L15-\d{4}E-\d{4}N', filename_poly).group() + '_features.tif'
        filepath_features = os.path.join(paths.DIR_DATA_TRAIN_RAW, filename_features)
        if not os.path.exists(filepath_features):
            filepath_features = os.path.join(paths.DIR_DATA_TRAIN_CLEAN, filename_features)
        if not os.path.exists(filepath_features):
            _logger.warning('Features file not available in raw or clean dirs: {}'.format(filename_features))
            missing_features.append(filename_features)
            continue

        # Get rasterize parameters
        raster_features = gdal.Open(filepath_features)
        cols = raster_features.RasterXSize
        rows = raster_features.RasterYSize
        llx, xres, _, y0, _, yres = raster_features.GetGeoTransform()
        urx = llx + cols * xres
        y1 = y0 + rows * yres
        lly = min([y0, y1])
        ury = max([y0, y1])

        # Rasterize several attributes separately
        for attribute in ATTRIBUTES:
            filepath_out = filepath_dest.format(attribute)
            if os.path.exists(filepath_out):
                continue
            command = 'gdal_rasterize -ot Int16 -co COMPRESS=DEFLATE -co TILED=YES -a_nodata -9999 -init -9999 ' \
                      '-a {attribute} -te {llx} {lly} {urx} {ury} -tr {xres} {yres} {src} {dest}'
            command = command.format(
                attribute=attribute, llx=llx, lly=lly, urx=urx, ury=ury, xres=xres, yres=yres,
                src=filepath_src, dest=filepath_out
            )
            gdal_command_line.run_gdal_command(command, _logger)

    assert not missing_features, 'Missing features files: {}'.format(', '.join(missing_features))


if __name__ == '__main__':
    create_millennium_project_quad_rasters()
