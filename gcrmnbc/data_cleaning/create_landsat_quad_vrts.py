import os
import re

import gdal
from tqdm import tqdm

from gcrmnbc.utils import command_line, paths


def create_landsat_quad_vrts() -> None:
    # Get quad filepaths
    dir_quads = os.path.join(paths.DIR_DATA_GLOBAL, paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format(50))
    filepaths_quads = [os.path.join(dir_quads, fn) for fn in os.listdir(dir_quads)]

    # Get global landsat filepath
    filepath_landsat_global = os.path.join(paths.DIR_DATA_LANDSAT_ORIG, 'global.vrt')
    if not os.path.exists(filepath_landsat_global):
        cw_dir = os.getcwd()
        os.chdir(paths.DIR_DATA_LANDSAT_ORIG)
        filepaths_landsats = [f for f in os.listdir(paths.DIR_DATA_LANDSAT_ORIG) if re.search(r'\d{10}-\d{10}.tif$', f)]
        filepath_inputs = 'input_list.txt'
        with open(filepath_inputs, 'w') as file_:
            file_.writelines('\n'.join(filepaths_landsats))
        command = 'gdalbuildvrt -input_file_list {filepath_inputs} {filepath_out}'.format(
            filepath_inputs=filepath_inputs, filepath_out=filepath_landsat_global)
        command_line.run_command_line(command)
        os.remove(filepath_inputs)
        os.chdir(cw_dir)

    # Create quad vrts
    dir_out = os.path.join(paths.DIR_DATA_LANDSAT, paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format(50))
    if not os.path.exists(dir_out):
        os.makedirs(dir_out)
    for filepath_quad in tqdm(filepaths_quads):
        filepath_out = os.path.join(dir_out, os.path.basename(filepath_quad))
        # Get vrt parameters
        raster_quad = gdal.Open(filepath_quad)
        cols = raster_quad.RasterXSize
        rows = raster_quad.RasterYSize
        llx, xres, _, y0, _, yres = raster_quad.GetGeoTransform()
        urx = llx + cols * xres
        y1 = y0 + rows * yres
        lly = min([y0, y1])
        ury = max([y0, y1])
        command = 'gdalbuildvrt -tr {xres} {yres} -te {llx} {lly} {urx} {ury} -vrtnodata -9999 ' + \
                  '-r average {filepath_out} {filepath_src}'
        command = command.format(
            xres=xres, yres=-yres, llx=llx, lly=lly, urx=urx, ury=ury, filepath_out=filepath_out,
            filepath_src=filepath_landsat_global)
        command_line.run_command_line(command)


if __name__ == '__main__':
    create_landsat_quad_vrts()
