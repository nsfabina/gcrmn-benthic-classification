import os

import fiona

from gcrmnbc.utils import encodings, logs, paths


_logger = logs.get_logger(__file__)


def remove_response_shapefiles_with_no_reef() -> None:
    raise AssertionError('This script has not been tested since being updated, be careful')
    filepaths = [os.path.join(paths.DIR_DATA_TRAIN_RAW, filename) for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW)
                 if filename.endswith('responses.shp')]
    for idx_filepath, filepath in enumerate(filepaths):
        _logger.debug('Reviewing shapefile {} of {}'.format(1+idx_filepath, len(filepaths)))
        reef_classes = (encodings.MAPPINGS[encodings.REEF_TOP], encodings.MAPPINGS[encodings.NOT_REEF_TOP])
        with fiona.open(filepath) as features:
            for feature in features:
                class_code = feature['properties']['class_code']
                if class_code in reef_classes:
                    _logger.debug('Found reef classes in {}'.format(filepath))
                    continue
            _logger.debug('Removing associated files, found NO reef classes in {}'.format(filepath))
            basename = os.path.splitext(os.path.basename(filepath))[0]
            for filename in os.listdir(paths.DIR_DATA_TRAIN_RAW):
                if not filename.startswith(basename):
                    continue
                _logger.debug('Remove file {}'.format(filename))
                os.remove(os.path.join(paths.DIR_DATA_TRAIN_RAW, filename))


if __name__ == '__main__':
    remove_response_shapefiles_with_no_reef()
