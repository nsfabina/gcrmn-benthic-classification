import os
import re
import shutil

from tqdm import tqdm

from gcrmnbc.utils import EPSG_DEST
from gcrmnbc.utils import command_line, paths


def reproject_landsat() -> None:
    # Convert all landsat imagery to the desired projection to avoid recalculating this later, takes ~5 mins per file
    filepaths_landsat = [os.path.join(paths.DIR_DATA_LANDSAT_ORIG, f) for f in os.listdir(paths.DIR_DATA_LANDSAT_ORIG)
                         if re.search('\d{10}-\d{10}.tif$', f)]
    for filepath_landsat in tqdm(filepaths_landsat):
        # Prepare paths
        filepath_tmp = filepath_landsat + '.tmp'
        filepath_lock = filepath_landsat + '.lock'
        filepath_complete = filepath_landsat + '.complete'
        if os.path.exists(filepath_complete):
            continue
        try:
            file_lock = open(filepath_lock, 'x')
        except:
            continue
        command = 'gdal_warp -s_srs EPSG:4326 -t_srs:{srs_out} -r average -co COMPRESS=DEFLATE -co TILED=YES ' + \
                  '-co BIGTIFF=YES -of GTiff {src} {dest}'
        command = command.format(srs_out=EPSG_DEST, src=filepath_landsat, dest=filepath_tmp)
        command_line.run_command_line(command)
        # Cleanup
        shutil.move(filepath_tmp, filepath_landsat)
        file_lock.close()
        os.remove(filepath_lock)
        open(filepath_complete, 'w')


if __name__ == '__main__':
    reproject_landsat()
