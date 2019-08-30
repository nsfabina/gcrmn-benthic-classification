from collections import namedtuple
import logging
from typing import List

from google.cloud import storage


_logger = logging.getLogger(__name__)

_DATA_PROJECT = 'coral-atlas'
_DATA_BUCKET_SOURCE = 'coral-atlas-data-share'
_DATA_BUCKET_DEST = ''
_DATA_PATH = 'coral_reefs_2018_visual_v1_mosaic'


class _GCS(object):
    _client = None
    _bucket_source = None
    _bucket_dest = None

    @property
    def client(self):
        if self._client is None:
            _logger.debug('Instantiating client')
            self._client = storage.Client(project=_DATA_PROJECT)
        return self._client

    @property
    def bucket_source(self):
        if self._bucket_source is None:
            _logger.debug('Getting source bucket:  {}'.format(_DATA_BUCKET_SOURCE))
            self._bucket_source = self.client.get_bucket(_DATA_BUCKET_SOURCE)
        return self._bucket_source

    @property
    def bucket_dest(self):
        if self._bucket_dest is None:
            _logger.debug('Getting dest bucket:  {}'.format(_DATA_BUCKET_DEST))
            self._bucket_dest = self.client.get_bucket(_DATA_BUCKET_DEST)
        return self._bucket_dest


GCS = _GCS()


QuadMetadata = namedtuple('QuadMetadata', ('dir_bucket', 'quad_focal', 'quads_context'))


def get_all_quad_metadata() -> List[QuadMetadata]:
    _logger.debug('')
    # Recurse bucket to find all regions with tifs
    # For each region, get all quad paths from below function
    pass


def _get_quad_metadata_for_region_bucket(dir_bucket: str) -> List[QuadMetadata]:
    _logger.debug('')
    # Get list of all quads
    # For each quad, get list of all contextual quads that exist
    # Return Quad
    pass


def download_source_data_for_quad(dir_dest: str, quad_metadata: QuadMetadata) -> None:
    _logger.debug('')
    # Download focal and contextual quads to location on scratch
    pass


def upload_model_classifications_for_quad(filepaths: List[str], quad_metadata: QuadMetadata) -> None:
    _logger.debug('')
    # Upload quad predictions to dest bucket
    pass
