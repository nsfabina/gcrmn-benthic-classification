import os
import re

from tqdm import tqdm

from gcrmnbc.utils import data_bucket, logs, paths


_logger = logs.get_logger(__file__)


def download_training_feature_quads() -> None:
    _logger.debug('Download training feature quads')
    # Get list of response files from UQ training data
    filenames = [filename for filename in os.listdir(paths.DIR_DATA_TRAIN_UQ_RAW) if filename.endswith('.shp')]
    # Get list of response files from supplemental training data
    filenames.extend([filename for filename in os.listdir(paths.DIR_DATA_TRAIN_SUPP_RAW) if filename.endswith('.shp')])
    # Get list of of response files from Millennium Project training data
    filenames.extend([fn for fn in os.listdir(paths.DIR_DATA_TRAIN_MP_RAW) if fn.endswith('responses.shp')])
    quads = set()

    # Determine which quads are needed
    for filename in filenames:
        quad_name = re.search(r'L15-\d{4}E-\d{4}N', filename).group()
        if not quad_name:
            continue
        filepath_raw = os.path.join(paths.DIR_DATA_TRAIN_FEATURES_RAW, quad_name + '_features.tif')
        if os.path.exists(filepath_raw):
            continue
        quads.add(quad_name)

    # Get quad blobs and download
    quad_blobs = [quad_blob for quad_blob in data_bucket.get_imagery_quad_blobs() if quad_blob.quad_focal in quads]
    for quad_blob in tqdm(quad_blobs, desc='Downloading training data feature quads'):
        data_bucket.download_model_training_input_data_for_quad_blob(paths.DIR_DATA_TRAIN_FEATURES_CLEAN, quad_blob)


if __name__ == '__main__':
    download_training_feature_quads()
