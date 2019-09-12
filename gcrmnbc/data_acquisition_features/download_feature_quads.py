import os
import re

from gcrmnbc.utils import data_bucket


DIR_TRAINING_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data'
DIR_DEST_FEATURES = os.path.join(DIR_TRAINING_DATA, 'clean')
DIR_SOURCE_RESPONSES = os.path.join(DIR_TRAINING_DATA, 'tmp')


def download_feature_quads() -> None:
    filenames = [filename for filename in os.listdir(DIR_SOURCE_RESPONSES) if filename.endswith('.shp')]
    quads = set([re.search(r'L15-\d{4}E-\d{4}N', filename).group() for filename in filenames])
    quad_blobs = [quad_blob for quad_blob in data_bucket.get_imagery_quad_blobs() if quad_blob.quad_focal in quads]
    for quad_blob in quad_blobs:
        data_bucket.download_model_training_input_data_for_quad_blob(DIR_DEST_FEATURES, quad_blob)


if __name__ == '__main__':
    download_feature_quads()
