import logging
import os
import shutil

from bfgn.data_management import data_core
from bfgn.experiments import experiments
from bfgn.data_management import apply_model_to_data

from gcrmnbc.model_application import data_bucket


_logger = logging.getLogger(__name__)

_DIR_SCRATCH_TMP = '/scratch/nfabina/gcrmn-benthic-classification/tmp_application'


def apply_model_to_quad(
        quad_metadata: data_bucket.QuadMetadata,
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
        version_map: str
) -> None:
    _logger.info('Apply model to quad {}'.format(quad_metadata.quad_focal))
    _logger.debug('Acquire file lock')
    filepath_lock = os.path.join(_DIR_SCRATCH_TMP, '{}.lock'.format(quad_metadata.quad_focal))
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        _logger.debug('Skipping application, already in progress')
        return

    _logger.debug('Create temporary directory for data')
    dir_quad = os.path.join(_DIR_SCRATCH_TMP, quad_metadata.quad_focal)
    if os.path.exists(dir_quad):
        shutil.rmtree(dir_quad)  # Remove directory if it already exists, to start from scratch
    os.makedirs(dir_quad)

    # Want to clean up if any of the following fail
    try:
        _logger.debug('Download source data')
        data_bucket.download_source_data_for_quad(dir_quad, quad_metadata)

        _logger.debug('Create VRT with appropriate bounds')
        # TODO

        _logger.info('Generating class probabilities from model')
        filepath_apply = os.path.join(dir_quad, quad_metadata.quad_focal + '.tif')
        filepath_prob = os.path.join(dir_quad, quad_metadata.quad_focal + '_prob_{}.tif'.format(version_map))
        basename_prob = os.path.splitext(filepath_prob)[0]
        apply_model_to_data.apply_model_to_site(
            experiment.model, data_container, [filepath_apply], basename_prob, exclude_feature_nodata=True)

        _logger.info('Generating classification from class probabilities')
        filepath_mle = os.path.join(dir_quad, quad_metadata.quad_focal + '_mle_{}.tif'.format(version_map))
        basename_mle = os.path.splitext(filepath_mle)[0]
        apply_model_to_data.maximum_likelihood_classification(
            filepath_prob, data_container, basename_mle, creation_options=['TILED=YES', 'COMPRESS=DEFLATE'])

        _logger.info('Uploading classifications and probabilities')
        data_bucket.upload_model_classifications_for_quad([filepath_prob, filepath_mle], quad_metadata)
        _logger.info('Application success for quad {}'.format(quad_metadata.quad_focal))

    except Exception as error_:
        raise error_

    finally:
        _logger.debug('Removing temporary quad data from {}'.format(dir_quad))
        shutil.rmtree(dir_quad)
        _logger.debug('Closing and removing lock file at {}'.format(dir_quad))
        file_lock.close()
        os.remove(filepath_lock)
        _logger.debug('Lock file removed')
