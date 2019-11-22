import os
import shutil

from tqdm import tqdm

from gcrmnbc.utils import EPSG_DEST
from gcrmnbc.utils import command_line, paths


def reproject_landsat() -> None:
    # Convert all landsat imagery to the desired projection to avoid recalculating this later, takes ~5 mins per file
    filepaths_landsat = [os.path.join(paths.DIR_DATA_LANDSAT_ORIG, f) for f in os.listdir(paths.DIR_DATA_LANDSAT_ORIG)
                         if f.endswith('.tif')]
    for filepath_landsat in tqdm(filepaths_landsat):
        # Prepare paths
        filepath_lock = filepath_landsat + '.lock'
        filepath_complete = filepath_landsat + '.complete'
        if os.path.exists(filepath_complete):
            continue
        try:
            file_lock = open(filepath_lock, 'x')
        except:
            continue
        # Translate each band individually to avoid OOM errors
        filepaths_bands = list()
        for idx_band in range(1, 6):
            filepath_band = os.path.splitext(filepath_landsat)[0] + '_{}.tif'.format(idx_band)
            command = 'gdal_translate -of GTiff -a_srs EPSG:{srs_out} -co COMPRESS=DEFLATE -co TILED=YES ' + \
                      '-co BIGTIFF=YES {src} {dest}'
            command = command.format(srs_out=EPSG_DEST, src=filepath_landsat, dest=filepath_band)
            command_line.run_command_line(command)
            filepaths_bands.append(filepath_band)
        # Merge bands
        filepath_tmp = filepath_landsat + '.tmp'
        command = 'gdal_merge.py -o {dest} -separate -co COMPRESS=DEFLATE -co TILED=YES -co BIGTIFF=YES {srcs}'.format(
            dest=filepath_tmp, srcs=' '.join(filepaths_bands))
        command_line.run_command_line(command)
        # Cleanup
        shutil.move(filepath_tmp, filepath_landsat)
        for filepath in filepaths_bands:
            os.remove(filepath)
        file_lock.close()
        os.remove(filepath_lock)
        open(filepath_complete, 'w')


if __name__ == '__main__':
    reproject_landsat()
