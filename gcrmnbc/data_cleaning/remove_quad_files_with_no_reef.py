import os

import fiona

from gcrmnbc.utils import encodings, logs


_logger = logs.get_logger(__file__)

DIR_DATA = '/scratch/nfabina/gcrmn-benthic-classification/training_data/tmp'


def remove_response_shapefiles_with_no_reef() -> None:
    filepaths = [os.path.join(DIR_DATA, filename) for filename in os.listdir(DIR_DATA)
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
            for filename in os.listdir(DIR_DATA):
                if not filename.startswith(basename):
                    continue
                _logger.debug('Remove file {}'.format(filename))
                os.remove(os.path.join(DIR_DATA, filename))


if __name__ == '__main__':
    remove_response_shapefiles_with_no_reef()
