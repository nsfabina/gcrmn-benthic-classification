import logging
import os
import sys

import fiona

from gcrmnbc.utils import data_bucket, encodings


_logger = logging.getLogger(__name__)
_logger.setLevel('DEBUG')
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.FileHandler('rasterize_response_quads.log')
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data/tmp'


def remove_response_shapefiles_with_no_reef() -> None:
    filepaths = [os.path.join(DIR_DATA, filename) for filename in os.listdir(DIR_DATA)
                 if filename.endswith('responses.shp')]
    for idx_filepath, filepath in enumerate(filepaths):
        _logger.debug('Reviewing shapefile {} of {}'.format(1+idx_filepath, len(filepaths)))
        classes = set()
        with fiona.open(filepath) as features:
            for feature in features:
                classes.add(feature['properties']['class_code'])
            if encodings.REEF_TOP in classes or encodings.NOT_REEF_TOP in classes:
                _logger.debug('Found reef classes in {}'.format(filepath))
                continue
            _logger.debug('Removing associated files, found NO reef classes in {}'.format(filepath))
            basename = os.path.splitext(os.path.basename(filepath))[0]
            for filename in os.listdir(DIR_DATA):
                if not filename.startswith(basename):
                    continue
                _logger.debug('Remove file {}'.format(filename))
                os.remove(os.path.join(DIR_DATA, filename))


if __name__ == '__main__':
    remove_response_shapefiles_with_no_reef()
