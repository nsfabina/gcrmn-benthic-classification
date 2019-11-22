import os
import shutil

from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line, paths


SRS_OUTPUT = 3857


def reproject_landsat() -> None:
    # Convert all landsat imagery to the desired projection to avoid recalculating this later, takes ~5 mins per file
    filepaths_landsat = [os.path.join(paths.DIR_DATA_LANDSAT_ORIG, f) for f in os.listdir(paths.DIR_DATA_LANDSAT_ORIG)]
    for filepath_landsat in tqdm(filepaths_landsat):
        filepath_tmp = filepath_landsat + '.tmp'
        filepath_lock = filepath_landsat + '.lock'
        filepath_complete = filepath_landsat + '.complete'
        if os.path.exists(filepath_complete):
            continue
        try:
            file_lock = open(filepath_lock, 'x')
        except:
            continue
        command = 'gdal_translate -of GTiff -a_srs EPSG:{srs_out} -co COMPRESS=DEFLATE -co TILED=YES ' + \
                  '-co BIGTIFF=YES {src} {dest}'
        command = command.format(srs_out=SRS_OUTPUT, src=filepath_landsat, dest=filepath_tmp)
        gdal_command_line.run_gdal_command(command)
        shutil.move(filepath_tmp, filepath_landsat)
        os.remove(file_lock)
        open(filepath_complete, 'w')


if __name__ == '__main__':
    reproject_landsat()
