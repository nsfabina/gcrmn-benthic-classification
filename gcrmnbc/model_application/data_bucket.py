import logging
import os
import re
from typing import List, NamedTuple, Tuple

from google.cloud import storage


_logger = logging.getLogger(__name__)

_DATA_PROJECT = 'coral-atlas'
_DATA_BUCKET_SOURCE = 'coral-atlas-data-share'
_DATA_BUCKET_DEST = ''
_DATA_PATH = 'coral_reefs_2018_visual_v1_mosaic/'

FILENAME_SUFFIX_FOCAL = '_focal.tif'
FILENAME_SUFFIX_CONTEXT = '_context.tif'
FILENAME_SUFFIX_PROB = '_prob_{}.tif'
FILENAME_SUFFIX_MLE = '_mle_{}.tif'


class _GCS(object):
    _client = None
    _bucket_source = None
    _bucket_dest = None

    @property
    def client(self):
        if self._client is None:
            _logger.debug('Instantiating client')
            filepath_remote = '/home/nfabina/.gsutil/credentials_atlas'
            filepath_local = '/Users/nfabina/.gsutil/credentials_atlas'
            assert os.path.exists(filepath_remote) or os.path.exists(filepath_local), \
                'gsutil credentials not found at {} or {}'.format(filepath_remote, filepath_local)
            filepath_creds = filepath_remote if os.path.exists(filepath_remote) else filepath_local
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = filepath_creds
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


class QuadBlob(NamedTuple):
    blob: storage.Blob
    region: str
    quad_focal: str
    x: int
    y: int
    blobs_context: List[storage.Blob]


def get_quad_blobs(version_map: str) -> List[QuadBlob]:
    _logger.debug('Get quad blobs from bucket')
    raw_blobs = [blob for blob in GCS.bucket_source.list_blobs(prefix=_DATA_PATH)]
    _logger.debug('Found {} total blobs'.format(len(raw_blobs)))
    _logger.debug('Parse blobs')
    quad_blobs = _parse_blobs(raw_blobs)
    _logger.debug('Found {} relevant blobs'.format(len(quad_blobs)))
    _logger.debug('Update contextual blobs')
    quad_blobs = _update_contextual_blobs(quad_blobs)
    _logger.debug('Prune completed quads')
    quad_blobs = _prune_completed_quad_blobs(quad_blobs, version_map)
    _logger.debug('Found {} incomplete quads'.format(len(quad_blobs)))
    return quad_blobs


def _parse_blobs(raw_blobs: List[storage.Blob]) -> List[QuadBlob]:
    blobs = list()
    for raw_blob in raw_blobs:
        # Remove blobs which are not quads
        if not raw_blob.name.endswith('.tif'):
            continue
        # Parse quad information
        region = _get_region_data_path_from_blob_name(raw_blob.name)
        quad = _get_quad_name_from_blob_name(raw_blob.name)
        x, y = _get_x_and_y_from_blob_name(raw_blob.name)
        # Remove blobs which are in the test bucket
        if region == 'test':
            continue
        blobs.append(QuadBlob(blob=raw_blob, region=region, quad_focal=quad, blobs_context=list(), x=int(x), y=int(y)))
    return blobs


def _update_contextual_blobs(quad_blobs: List[QuadBlob]) -> List[QuadBlob]:
    updated = list()
    for blob_focal in quad_blobs:
        # Get x and y values for adjacent quads
        xs_focal = list(range(-1 + blob_focal.x, 2 + blob_focal.x))
        ys_focal = list(range(-1 + blob_focal.y, 2 + blob_focal.y))
        for blob_candidate in quad_blobs:
            if blob_candidate.x not in xs_focal or blob_candidate.y not in ys_focal:
                continue  # Quad is not adjacent
            if blob_candidate.x == blob_focal.x and blob_candidate.y == blob_focal.y:
                continue  # Quad is same as focal
            blob_focal.blobs_context.append(blob_candidate.blob)
        updated.append(blob_focal)
    return updated


def _prune_completed_quad_blobs(quad_blobs: List[QuadBlob], version_map: str) -> List[QuadBlob]:
    pruned = list()
    for quad_blob in quad_blobs:
        is_complete = check_is_quad_application_complete(quad_blob, version_map)
        if not is_complete:
            pruned.append(quad_blob)
    return pruned


def check_is_quad_application_complete(quad_blob: QuadBlob, version_map: str) -> bool:
    # Check if probability raster exists, if not, quad must be processed and we don't need to check MLE raster
    blob_prob = _get_model_class_probabilities_blob(quad_blob, version_map)
    if not blob_prob.exists():
        return False
    # Check if MLE raster exists, if not, quad must be processed, even if probability raster exists
    blob_mle = _get_model_class_mle_blob(quad_blob, version_map)
    if not blob_mle.exists():
        return False
    return True


def download_source_data_for_quad_blob(dir_dest: str, quad_blob: QuadBlob) -> None:
    _logger.debug('Download source data for quad blob')
    filepath_focal = os.path.join(dir_dest, quad_blob.quad_focal + FILENAME_SUFFIX_FOCAL)
    _logger.debug('Download focal quad to {}'.format(filepath_focal))
    quad_blob.blob.download_to_filename(filepath_focal)

    _logger.debug('Download {} contextual quads'.format(len(quad_blob.blobs_context)))
    for blob_context in quad_blob.blobs_context:
        quad_context = _get_quad_name_from_blob_name(blob_context.name)
        filepath_context = os.path.join(dir_dest, quad_context + FILENAME_SUFFIX_CONTEXT)
        _logger.debug('Download contextual quad to {}'.format(filepath_context))
        blob_context.download_to_filename(filepath_context)


def _get_region_data_path_from_blob_name(blob_name: str) -> str:
    name_region_quad = blob_name.split(_DATA_PATH)[1]
    split_region_quad = name_region_quad.split('/')
    return '/'.join(split_region_quad[:-1])


def _get_quad_name_from_blob_name(blob_name: str) -> str:
    name_region_quad = blob_name.split(_DATA_PATH)[1]
    split_region_quad = name_region_quad.split('/')
    return split_region_quad[-1].split('.tif')[0]


def _get_x_and_y_from_blob_name(blob_name: str) -> Tuple[str, str]:
    quad = _get_quad_name_from_blob_name(blob_name)
    _, _, x, _, y, _ = re.split('-|[A-Z]', quad)
    return x, y


def upload_model_class_probabilities_for_quad_blob(filepath: str, quad_blob: QuadBlob, version_map: str) -> None:
    _logger.debug('Upload model class probablities for quad blob {}'.format(quad_blob.quad_focal))
    blob_upload = _get_model_class_probabilities_blob(quad_blob, version_map)
    blob_upload.upload_from_filename(filepath)


def upload_model_class_mle_for_quad_blob(filepath: str, quad_blob: QuadBlob, version_map: str) -> None:
    _logger.debug('Upload model class MLE for quad blob {}'.format(quad_blob.quad_focal))
    blob_upload = _get_model_class_mle_blob(quad_blob, version_map)
    blob_upload.upload_from_filename(filepath)


def _get_model_class_probabilities_blob(quad_blob: QuadBlob, version_map: str) -> storage.Blob:
    name = re.sub('\.tif', FILENAME_SUFFIX_PROB.format(version_map), quad_blob.blob.name)
    return storage.Blob(name, GCS.bucket_dest)


def _get_model_class_mle_blob(quad_blob: QuadBlob, version_map: str) -> storage.Blob:
    name = re.sub('\.tif', FILENAME_SUFFIX_MLE.format(version_map), quad_blob.blob.name)
    return storage.Blob(name, GCS.bucket_dest)