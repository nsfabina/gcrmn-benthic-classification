import logging
import os
import re
import shutil
from typing import NamedTuple

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
    if not os.path.exists(_DIR_SCRATCH_TMP):
        try:
            os.makedirs(_DIR_SCRATCH_TMP)
        except FileExistsError:
            pass
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
        buffer = int(2 * experiment.config.data_build.window_radius - experiment.config.data_build.loss_window_radius)
        _create_feature_vrt(quad_paths, buffer)

        _logger.info('Generate class probabilities from model')
        _generate_class_probabilities_raster(quad_paths, data_container, experiment)

        _logger.info('Generating classification from class probabilities')
        _generate_class_mle_raster(quad_paths, data_container)

        _logger.info('Crop rasters to focal quad extent')
        _crop_and_scale_class_rasters(quad_paths)

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


def _create_feature_vrt(quad_paths: QuadPaths, buffer: int) -> None:
    # Get raster parameters for building VRT
    focal_raster = gdal.Open(quad_paths.filepath_focal_quad)
    cols = focal_raster.RasterXSize
    rows = focal_raster.RasterYSize
    llx, xres, _, y0, _, yres = focal_raster.GetGeoTransform()
    urx = llx + cols * xres
    y1 = y0 + rows * yres
    lly = min([y0, y1])
    ury = max([y0, y1])

    # Modify raster parameters to build in buffer
    llx -= buffer * xres
    urx += buffer * xres
    lly += buffer * yres
    ury -= buffer * yres

    # Build VRT
    focal_raster = gdal.Open(quad_paths.filepath_focal_quad)
    focal_srs = osr.SpatialReference(wkt=focal_raster.GetProjection())
    filepaths_quads = [
        os.path.join(quad_paths.dir_quad, filename) for filename in os.listdir(quad_paths.dir_quad)
        if filename.endswith(data_bucket.FILENAME_SUFFIX_FOCAL)
        or filename.endswith(data_bucket.FILENAME_SUFFIX_CONTEXT)
    ]
    options_buildvrt = gdal.BuildVRTOptions(
        bandList=[1, 2, 3], outputBounds=(llx, lly, urx, ury), outputSRS=focal_srs, VRTNodata=-9999
    )
    gdal.BuildVRT(quad_paths.filepath_features, filepaths_quads, options=options_buildvrt)


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


def _crop_and_scale_class_rasters(quad_paths: QuadPaths) -> None:
    # Get raster parameters for crop
    focal_raster = gdal.Open(quad_paths.filepath_focal_quad)
    focal_srs = osr.SpatialReference(wkt=focal_raster.GetProjection())
    cols = focal_raster.RasterXSize
    rows = focal_raster.RasterYSize
    llx, xres, _, y0, _, yres = focal_raster.GetGeoTransform()
    urx = llx + cols * xres
    y1 = y0 + rows * yres
    lly = min([y0, y1])
    ury = max([y0, y1])
    # Apply translation to probabilities
    options_translate = gdal.TranslateOptions(
        projWin=(llx, ury, urx, lly), projWinSRS=focal_srs, outputSRS=focal_srs, noData=-9999,
        creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'],
    )
    tmp_filepath = re.sub('.tif', '_tmp.tif', quad_paths.filepath_prob)
    gdal.Translate(tmp_filepath, quad_paths.filepath_prob, options=options_translate)
    os.rename(tmp_filepath, quad_paths.filepath_prob)
    # Apply translation to MLE
    options_translate = gdal.TranslateOptions(
        outputType=gdal.GDT_Int16, projWin=(llx, ury, urx, lly), projWinSRS=focal_srs, outputSRS=focal_srs,
        noData=-9999, creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'],
    )
    tmp_filepath = re.sub('.tif', '_tmp.tif', quad_paths.filepath_mle)
    gdal.Translate(tmp_filepath, quad_paths.filepath_mle, options=options_translate)
    os.rename(tmp_filepath, quad_paths.filepath_mle)


def _get_quad_paths(quad_blob: data_bucket.QuadBlob, version_map: str) -> QuadPaths:
    dir_quad = os.path.join(_DIR_SCRATCH_TMP, quad_blob.quad_focal)
    filepath_lock = os.path.join(_DIR_SCRATCH_TMP, '{}.lock'.format(quad_blob.quad_focal))
    filepath_features = os.path.join(dir_quad, _FILENAME_FEATURES_VRT)
    filepath_focal = os.path.join(dir_quad, quad_blob.quad_focal + data_bucket.FILENAME_SUFFIX_FOCAL)
    filepath_prob = os.path.join(dir_quad, quad_blob.quad_focal + data_bucket.FILENAME_SUFFIX_PROB.format(version_map))
    filepath_mle = os.path.join(dir_quad, quad_blob.quad_focal + data_bucket.FILENAME_SUFFIX_MLE.format(version_map))
    return QuadPaths(
        dir_quad=dir_quad, filepath_lock=filepath_lock, filepath_features=filepath_features,
        filepath_focal_quad=filepath_focal, filepath_prob=filepath_prob, filepath_mle=filepath_mle,
    )
