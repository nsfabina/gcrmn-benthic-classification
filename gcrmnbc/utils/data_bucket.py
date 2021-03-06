import logging
import os
import re
from typing import Dict, List, NamedTuple, Tuple

from google.cloud import storage


_logger = logging.getLogger('model_global_application.data_bucket')
_logger.setLevel('DEBUG')

_DATA_PROJECT = 'coral-atlas'
_DATA_BUCKET = 'coral-atlas-data-share'
_DATA_PATH_SOURCE = 'coral_reefs_2018_visual_v1_mosaic/'
_DATA_PATH_DEST = 'gcrmn-global-map/'

FILENAME_SUFFIX_FEATURES = '_features.tif'

FILENAME_SUFFIX_FOCAL = '_focal.tif'
FILENAME_SUFFIX_CONTEXT = '_context.tif'

FILENAME_COMPLETE = 'application_complete'
FILENAME_NO_APPLY = 'no_apply'
FILENAME_CORRUPT = 'data_corrupt'


class _GCS(object):
    _client = None
    _bucket = None

    @property
    def client(self):
        if self._client is None:
            _logger.debug('Instantiating client')
            filepath_remote = '/home/nfabina/.gsutil/credentials_atlas'
            filepath_local = '/Users/nsfabina/.gsutil/credentials_atlas'
            assert os.path.exists(filepath_remote) or os.path.exists(filepath_local), \
                'gsutil credentials not found at {} or {}'.format(filepath_remote, filepath_local)
            filepath_creds = filepath_remote if os.path.exists(filepath_remote) else filepath_local
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = filepath_creds
            self._client = storage.Client(project=_DATA_PROJECT)
        return self._client

    @property
    def bucket(self):
        if self._bucket is None:
            _logger.debug('Getting source bucket:  {}'.format(_DATA_BUCKET))
            self._bucket = self.client.get_bucket(_DATA_BUCKET)
        return self._bucket


GCS = _GCS()


class QuadBlob(NamedTuple):
    blob: storage.Blob
    region: str
    quad_focal: str
    x: int
    y: int
    blobs_context: List[storage.Blob]


def get_imagery_quad_blobs() -> List[QuadBlob]:
    _logger.debug('Get quad blobs from bucket')
    raw_blobs = [blob for blob in GCS.bucket.list_blobs(prefix=_DATA_PATH_SOURCE)]
    _logger.debug('Found {} total blobs'.format(len(raw_blobs)))
    _logger.debug('Parse blobs')
    quad_blobs = _parse_blobs(raw_blobs, match_patterns=['.tif'])
    _logger.debug('Found {} relevant blobs'.format(len(quad_blobs)))
    _logger.debug('Update contextual blobs')
    quad_blobs = _update_contextual_blobs(quad_blobs)
    return quad_blobs


def get_reef_heat_and_outline_quad_blobs(model_version: str) -> Tuple[List[QuadBlob], List[QuadBlob]]:
    _logger.debug('Get quad blobs from bucket')
    raw_blobs = [blob for blob in GCS.bucket.list_blobs(prefix=_DATA_PATH_DEST)]
    _logger.debug('Found {} total blobs'.format(len(raw_blobs)))
    _logger.debug('Parse blobs')
    heat_blobs = _parse_blobs(raw_blobs, match_patterns=[model_version, 'reef_heat.tif'])
    outline_blobs = _parse_blobs(raw_blobs, match_patterns=[model_version, 'reef_outline.tif'])
    _logger.debug('Found {} and {} relevant blobs'.format(len(heat_blobs), len(outline_blobs)))
    _logger.debug('Update contextual blobs')
    heat_blobs = _update_contextual_blobs(heat_blobs)
    outline_blobs = _update_contextual_blobs(outline_blobs)
    return heat_blobs, outline_blobs


def _parse_blobs(raw_blobs: List[storage.Blob], match_patterns: List[str]) -> List[QuadBlob]:
    quad_blobs = list()
    for raw_blob in raw_blobs:
        # remove blobs which are not matches
        if not all([re.search(pattern, raw_blob.name) for pattern in match_patterns]):
            continue
        # parse quad information
        region = _get_region_data_path_from_blob_name(raw_blob.name)
        quad = get_quad_name_from_blob_name(raw_blob.name)
        x, y = _get_x_and_y_from_blob_name(raw_blob.name)
        # remove blobs which are in the test bucket
        if region == 'test':
            continue
        quad_blobs.append(QuadBlob(
            blob=raw_blob, region=region, quad_focal=quad, blobs_context=list(), x=int(x), y=int(y)
        ))
    return quad_blobs


def _update_contextual_blobs(quad_blobs: List[QuadBlob]) -> List[QuadBlob]:
    blobs_sorted: Dict[int, Dict[int, QuadBlob]] = dict()
    for quad_blob in quad_blobs:
        blobs_sorted.setdefault(quad_blob.x, dict())[quad_blob.y] = quad_blob

    updated = list()
    for blob_focal in quad_blobs:
        # Get x and y values for adjacent quads
        xs_focal = list(range(-1 + blob_focal.x, 2 + blob_focal.x))
        ys_focal = list(range(-1 + blob_focal.y, 2 + blob_focal.y))
        for x in xs_focal:
            for y in ys_focal:
                if x == blob_focal.x and y == blob_focal.y:
                    continue  # Quad is same as focal
                blob_candidate = blobs_sorted.get(x, dict()).get(y)
                if blob_candidate is None:
                    continue
                blob_focal.blobs_context.append(blob_candidate.blob)
        updated.append(blob_focal)
    return updated


def _prune_completed_quad_blobs(
        quad_blobs: List[QuadBlob],
        response_mapping: str,
        model_name: str,
        model_version: str
) -> List[QuadBlob]:
    pruned = list()
    for quad_blob in quad_blobs:
        is_complete = check_is_quad_model_application_complete(quad_blob, response_mapping, model_name, model_version)
        if not is_complete:
            pruned.append(quad_blob)
    return pruned


def check_is_quad_model_application_complete(
        quad_blob: QuadBlob,
        response_mapping: str,
        model_name: str,
        model_version: str
) -> bool:
    blob_complete = _get_application_complete_blob(quad_blob, response_mapping, model_name, model_version)
    blob_no_apply = _get_no_apply_blob(quad_blob)
    return blob_complete.exists() or blob_no_apply.exists()


def download_model_training_input_data_for_quad_blob(dir_dest: str, quad_blob: QuadBlob) -> None:
    _logger.debug('Download source data for quad blob')
    filepath_focal = os.path.join(dir_dest, quad_blob.quad_focal + FILENAME_SUFFIX_FEATURES)
    if os.path.exists(filepath_focal):
        _logger.debug('Quad already downloaded for {}'.format(filepath_focal))
        return
    _logger.debug('Download focal quad to {}'.format(filepath_focal))
    quad_blob.blob.download_to_filename(filepath_focal)


def download_model_application_input_data_for_quad_blob(dir_dest: str, quad_blob: QuadBlob) -> None:
    _logger.debug('Download source data for quad blob')
    filepath_focal = os.path.join(dir_dest, quad_blob.quad_focal + FILENAME_SUFFIX_FOCAL)
    _logger.debug('Download focal quad to {}'.format(filepath_focal))
    quad_blob.blob.download_to_filename(filepath_focal)

    _logger.debug('Download {} contextual quads'.format(len(quad_blob.blobs_context)))
    for blob_context in quad_blob.blobs_context:
        quad_context = get_quad_name_from_blob_name(blob_context.name)
        filepath_context = os.path.join(dir_dest, quad_context + FILENAME_SUFFIX_CONTEXT)
        _logger.debug('Download contextual quad to {}'.format(filepath_context))
        blob_context.download_to_filename(filepath_context)


def upload_model_application_results_for_quad_blob(
        dir_results: str,
        quad_blob: QuadBlob,
        response_mapping: str,
        model_name: str,
        model_version: str
) -> None:
    _logger.debug('Upload model results for quad blob {}'.format(quad_blob.quad_focal))
    blob_name_application = _get_application_path_for_model_results(
        quad_blob, response_mapping, model_name, model_version)
    for filename in os.listdir(dir_results):
        filepath = os.path.join(dir_results, filename)
        blob_name = os.path.join(blob_name_application, filename)
        blob = storage.Blob(blob_name, GCS.bucket)
        blob.upload_from_filename(filepath)
    blob_complete = _get_application_complete_blob(quad_blob, response_mapping, model_name, model_version)
    blob_complete.upload_from_string('')


def upload_model_no_apply_notification_for_quad_blob(quad_blob: QuadBlob) -> None:
    _logger.debug('Upload no apply notification for quad blob {}'.format(quad_blob.quad_focal))
    no_apply_blob = _get_no_apply_blob(quad_blob)
    no_apply_blob.upload_from_string('')


def upload_model_corrupt_data_notification_for_quad_blob(quad_blob: QuadBlob) -> None:
    _logger.debug('Upload corrupt data notification for quad blob {}'.format(quad_blob.quad_focal))
    corrupt_blob = _get_corrupt_data_blob(quad_blob)
    corrupt_blob.upload_from_string('')


def delete_model_corrupt_data_notification_if_exists(quad_blob: QuadBlob) -> None:
    corrupt_blob = _get_corrupt_data_blob(quad_blob)
    if corrupt_blob.exists():
        _logger.debug('Delete corrupt data notification for quad blob {}'.format(quad_blob.quad_focal))
        corrupt_blob.delete()


def delete_model_application_results_for_other_versions(
        quad_blob: QuadBlob,
        model_name: str,
        current_model_version: str
) -> None:
    # TODO:  test when we need to remove data, wait until then for examples to work on
    # TODO:  add model name to the paths
    raise AssertionError('remove_model_results needs to be tested')
    application_path_quad = _get_application_path_for_quad(quad_blob) + '/'
    for blob in GCS.bucket.list_blobs(prefix=application_path_quad):
        with_prefix_removed = re.sub(application_path_quad, '', blob.name)
        is_other_version = not with_prefix_removed.startswith(current_model_version)
        if is_other_version:
            blob.delete()


def _get_region_data_path_from_blob_name(blob_name: str) -> str:
    if _DATA_PATH_SOURCE in blob_name:
        splitter = _DATA_PATH_SOURCE
    elif _DATA_PATH_DEST in blob_name:
        splitter = _DATA_PATH_DEST
    after_bucket_prefix = re.split(splitter, blob_name)[1]
    before_quad_name = re.split(r'/L15-\d{4}E-\d{4}N', after_bucket_prefix)[0]
    return before_quad_name


def get_quad_name_from_blob_name(blob_name: str) -> str:
    return re.search(r'L15-\d{4}E-\d{4}N', blob_name).group()


def _get_x_and_y_from_blob_name(blob_name: str) -> Tuple[str, str]:
    quad = get_quad_name_from_blob_name(blob_name)
    _, x, y = re.split('-', quad)
    return x[:-1], y[:-1]


def _get_application_path_for_quad(quad_blob: QuadBlob) -> str:
    original_name = quad_blob.blob.name
    with_new_path_prefix = re.sub(_DATA_PATH_SOURCE, _DATA_PATH_DEST, original_name)
    without_tif_extension = re.sub(r'\.tif', '', with_new_path_prefix)
    return without_tif_extension


def _get_application_path_for_model_results(
        quad_blob: QuadBlob,
        response_mapping: str,
        model_name: str,
        model_version: str
) -> str:
    application_path_quad = _get_application_path_for_quad(quad_blob)
    with_model_ids = os.path.join(application_path_quad, response_mapping, model_name, model_version)
    return with_model_ids


def _get_application_complete_blob(
        quad_blob: QuadBlob,
        response_mapping: str,
        model_name: str,
        model_version: str
) -> storage.Blob:
    application_blob_name = _get_application_path_for_model_results(
        quad_blob, response_mapping, model_name, model_version)
    application_complete_name = os.path.join(application_blob_name, FILENAME_COMPLETE)
    return storage.Blob(application_complete_name, GCS.bucket)


def _get_no_apply_blob(quad_blob: QuadBlob) -> storage.Blob:
    application_path_quad = _get_application_path_for_quad(quad_blob)
    no_apply_name = os.path.join(application_path_quad, FILENAME_NO_APPLY)
    return storage.Blob(no_apply_name, GCS.bucket)


def _get_corrupt_data_blob(quad_blob: QuadBlob) -> storage.Blob:
    application_path_quad = _get_application_path_for_quad(quad_blob)
    corrupt_name = os.path.join(application_path_quad, FILENAME_CORRUPT)
    return storage.Blob(corrupt_name, GCS.bucket)
