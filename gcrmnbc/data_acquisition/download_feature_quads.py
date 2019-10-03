import os
import re

from gcrmnbc.utils import data_bucket, logs, paths


_logger = logs.get_logger(__file__)


def download_feature_quads() -> None:
    _logger.debug('Download feature quads')
    filenames = [filename for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW) if filename.endswith('.shp')]
    filenames.extend([filename for filename in os.listdir(paths.DIR_DATA_TRAIN_CLEAN) if filename.endswith('.shp')])
    quads = set([re.search(r'L15-\d{4}E-\d{4}N', filename).group() for filename in filenames])
    quad_blobs = [quad_blob for quad_blob in data_bucket.get_imagery_quad_blobs() if quad_blob.quad_focal in quads]
    for idx_blob, quad_blob in enumerate(quad_blobs):
        _logger.debug('Downloading blob {} of {}'.format(1+idx_blob, len(quad_blobs)))
        data_bucket.download_model_training_input_data_for_quad_blob(paths.DIR_DATA_TRAIN_RAW, quad_blob)


if __name__ == '__main__':
    download_feature_quads()
