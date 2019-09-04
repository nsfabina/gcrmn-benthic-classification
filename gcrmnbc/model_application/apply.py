import logging
import os
import shutil
from typing import List, NamedTuple

from bfgn.data_management import data_core
from bfgn.experiments import experiments
from bfgn.data_management import apply_model_to_data
from osgeo import gdal, osr

from gcrmnbc.model_application import data_bucket


_logger = logging.getLogger(__name__)

_DIR_SCRATCH_TMP = '/scratch/nfabina/gcrmn-benthic-classification/tmp_application'
_FILENAME_FEATURES_VRT = 'features.vrt'


class QuadPaths(NamedTuple):
    dir_quad: str
    filepath_lock: str
    filepath_features: str
    filepaths_quads: List[str]
    filepath_focal_quad: str
    filepath_prob: str
    filepath_mle: str


def apply_model_to_quad(
        quad_blob: data_bucket.QuadBlob,
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
        version_map: str
) -> None:
    _logger.info('Apply model to quad {}'.format(quad_blob.quad_focal))
    _logger.debug('Acquire file lock')
    quad_paths = _get_quad_paths(quad_blob, version_map)
    try:
        file_lock = open(quad_paths.filepath_lock, 'x')
    except OSError:
        _logger.debug('Skipping application, already in progress')
        return

    _logger.debug('Check if application is already complete')
    is_complete = data_bucket.check_is_quad_application_complete(quad_blob, version_map)
    if is_complete:
        _logger.debug('Skipping application, is already complete')
        return

    _logger.debug('Create temporary directory for data')
    _create_temporary_directory_for_data(quad_paths)

    # Want to clean up if any of the following fail
    try:
        _logger.debug('Download source data')
        data_bucket.download_source_data_for_quad_blob(quad_paths.dir_quad, quad_blob)

        _logger.debug('Create feature VRT')
        _create_feature_vrt(quad_paths)

        _logger.info('Generate class probabilities from model')
        _generate_class_probabilities_raster(quad_paths, data_container, experiment)

        _logger.info('Generating classification from class probabilities')
        _generate_class_mle_raster(quad_paths, data_container)

        _logger.info('Crop rasters to focal quad extent')
        _crop_class_rasters_to_focal_extent(quad_paths)

        _logger.info('Uploading classifications and probabilities')
        data_bucket.upload_model_class_probabilities_for_quad_blob(quad_paths.filepath_prob, quad_blob, version_map)
        data_bucket.upload_model_class_mle_for_quad_blob(quad_paths.filepath_prob, quad_blob, version_map)
        _logger.info('Application success for quad {}'.format(quad_blob.quad_focal))

    except Exception as error_:
        raise error_

    finally:
        _logger.debug('Removing temporary quad data from {}'.format(quad_paths.dir_quad))
        shutil.rmtree(quad_paths.dir_quad)
        _logger.debug('Closing and removing lock file at {}'.format(quad_paths.dir_quad))
        file_lock.close()
        os.remove(quad_paths.filepath_lock)
        _logger.debug('Lock file removed')


def _create_temporary_directory_for_data(quad_paths: QuadPaths) -> None:
    if os.path.exists(quad_paths.dir_quad):
        shutil.rmtree(quad_paths.dir_quad)  # Remove directory if it already exists, to start from scratch
    os.makedirs(quad_paths.dir_quad)


def _create_feature_vrt(quad_paths: QuadPaths) -> None:
    # TODO:  test manually
    # TODO?:  crop vrt extent to focal raster + some buffer, will save lots of time, but necessary?
    focal_raster = gdal.Open(quad_paths.filepath_focal_quad)
    focal_srs = osr.SpatialReference(wkt=focal_raster.GetProjection())
    vrt_options = gdal.BuildVRTOptions(outputSRS=focal_srs, VRTNodata=-9999)
    gdal.BuildVRT(quad_paths.filepath_features, quad_paths.filepaths_quads, options=vrt_options)


def _generate_class_probabilities_raster(
        quad_paths: QuadPaths,
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
) -> None:
    basename_prob = os.path.splitext(quad_paths.filepath_prob)[0]
    apply_model_to_data.apply_model_to_site(
        experiment.model, data_container, [quad_paths.filepath_features], basename_prob, exclude_feature_nodata=True)


def _generate_class_mle_raster(
        quad_paths: QuadPaths,
        data_container: data_core.DataContainer,
) -> None:
    basename_mle = os.path.splitext(quad_paths.filepath_mle)[0]
    apply_model_to_data.maximum_likelihood_classification(
        quad_paths.filepath_prob, data_container, basename_mle, creation_options=['TILED=YES', 'COMPRESS=DEFLATE'])


def _crop_class_rasters_to_focal_extent(quad_paths: QuadPaths) -> None:
    # TODO:  test manually
    # TODO?:  convert probabilities, multiply by 100 and store as integers? only needed to save space, potentially
    # Get raster parameters
    focal_raster = gdal.Open(quad_paths.filepath_focal_quad)
    focal_srs = osr.SpatialReference(wkt=focal_raster.GetProjection())
    cols = focal_raster.RasterXSize
    rows = focal_raster.RasterYSize
    llx, xres, _, y0, _, yres = focal_raster.GetGeoTransform()
    urx = llx + cols * xres
    y1 = y0 + rows * yres
    lly = min([y0, y1])
    ury = max([y0, y1])
    warp_options = gdal.WarpOptions(
        outputBounds=(llx, lly, urx, ury), srcSRS=focal_srs, dstSRS=focal_srs, outputType=gdal.GDT_Float32,
        creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'], srcNodata=-9999, dstNodata=-9999,
    )
    gdal.Warp(quad_paths.filepath_prob, quad_paths.filepath_prob, options=warp_options)
    gdal.Warp(quad_paths.filepath_mle, quad_paths.filepath_mle, options=warp_options)


def _get_quad_paths(quad_blob: data_bucket.QuadBlob, version_map: str) -> QuadPaths:
    dir_quad = os.path.join(_DIR_SCRATCH_TMP, quad_blob.quad_focal)
    filepath_lock = os.path.join(_DIR_SCRATCH_TMP, '{}.lock'.format(quad_blob.quad_focal))
    filepath_features = os.path.join(dir_quad, _FILENAME_FEATURES_VRT)
    filepaths_quads = [
        os.path.join(dir_quad, filename) for filename in os.listdir(dir_quad)
        if filename.endswith(data_bucket.FILENAME_SUFFIX_FOCAL)
        or filename.endswith(data_bucket.FILENAME_SUFFIX_CONTEXT)
    ]
    filepath_focal = [fp for fp in filepaths_quads if fp.endswith(data_bucket.FILENAME_SUFFIX_FOCAL)][0]
    filepath_prob = os.path.join(dir_quad, quad_blob.quad_focal + data_bucket.FILENAME_SUFFIX_PROB.format(version_map))
    filepath_mle = os.path.join(dir_quad, quad_blob.quad_focal + data_bucket.FILENAME_SUFFIX_MLE.format(version_map))
    return QuadPaths(
        dir_quad=dir_quad, filepath_lock=filepath_lock, filepath_features=filepath_features,
        filepaths_quads=filepaths_quads, filepath_focal_quad=filepath_focal, filepath_prob=filepath_prob,
        filepath_mle=filepath_mle,
    )
