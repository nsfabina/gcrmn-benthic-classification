import logging
import os
import re
import shlex
import shutil
import subprocess
from typing import NamedTuple

from bfgn.data_management import data_core
from bfgn.experiments import experiments
from bfgn.data_management import apply_model_to_data
import numpy as np
from osgeo import gdal, osr

from gcrmnbc.utils import data_bucket


_logger = logging.getLogger('model_global_application.apply')
_logger.setLevel('DEBUG')

_DIR_SCRATCH_TMP = '/scratch/nfabina/gcrmn-benthic-classification/tmp_global_application'


class QuadPaths(NamedTuple):
    dir_quad: str
    dir_for_upload: str
    filepath_lock: str
    filepath_focal_quad: str
    filepath_features: str
    filepath_prob: str
    filepath_mle: str
    filepath_shapefile: str


def apply_model_to_quad(
        quad_blob: data_bucket.QuadBlob,
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
        response_mapping: str,
        model_name: str,
        model_version: str
) -> None:
    if not os.path.exists(_DIR_SCRATCH_TMP):
        try:
            os.makedirs(_DIR_SCRATCH_TMP)
        except FileExistsError:
            pass

    _logger.info('Apply model to quad {}'.format(quad_blob.quad_focal))
    quad_paths = _get_quad_paths(quad_blob)

    _logger.debug('Check if application is already complete')
    is_complete = data_bucket.check_is_quad_model_application_complete(
        quad_blob, response_mapping, model_name, model_version)
    if is_complete:
        _logger.debug('Skipping application, is already complete')
        return

    _logger.debug('Acquire file lock')
    try:
        file_lock = open(quad_paths.filepath_lock, 'x')
    except OSError:
        _logger.debug('Skipping application, already in progress')
        return

    _logger.debug('Create temporary directory for data')
    _create_temporary_directory_for_data(quad_paths)

    # Want to clean up if any of the following fail
    try:
        _logger.debug('Download source data')
        data_bucket.download_model_application_input_data_for_quad_blob(quad_paths.dir_quad, quad_blob)

        _logger.debug('Create feature VRT')
        buffer = int(2 * experiment.config.data_build.window_radius - experiment.config.data_build.loss_window_radius)
        _create_feature_vrt(quad_paths, buffer)

        _logger.info('Generate model probabilities')
        try:
            _generate_model_probabilities_raster(quad_paths, data_container, experiment)
        except AttributeError:
            _logger.debug('Application unsuccessful, corrupt data found')
            data_bucket.upload_model_corrupt_data_notification_for_quad_blob(quad_blob)
            return

        _logger.info('Format model probabilities')
        _crop_model_probabilities_raster(quad_paths)
        _mask_model_probabilities_raster(quad_paths)

        _logger.info('Generating model classifications')
        _generate_model_classifications_raster(quad_paths, data_container)
        _mask_model_classifications_raster(quad_paths)
        includes_reef = _check_model_classifications_include_reef(quad_paths)

        if not includes_reef:
            _logger.debug('Application stopped early, no reef area found')
            data_bucket.upload_model_no_apply_notification_for_quad_blob(quad_blob)
            return

        _logger.info('Generating shapefile from classifications')
        _generate_model_classification_shapefile(quad_paths)

        _logger.info('Compress model probabilities and classifications')
        _scale_model_probabilities_raster(quad_paths)
        _scale_model_classifications_raster(quad_paths)

        _logger.info('Uploading model results')
        data_bucket.upload_model_application_results_for_quad_blob(
            quad_paths.dir_for_upload, quad_blob, response_mapping, model_name, model_version)

        _logger.info('Application success for quad {}'.format(quad_blob.quad_focal))
        raise AssertionError('Check if successful!')
        _logger.debug('Delete model results from other versions and any outdated notifications')
        data_bucket.delete_model_application_results_for_other_versions(
            quad_blob, response_mapping, model_name, model_version)
        data_bucket.delete_model_corrupt_data_notification_if_exists(quad_blob)

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
    os.makedirs(quad_paths.dir_for_upload)


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


def _generate_model_probabilities_raster(
        quad_paths: QuadPaths,
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
) -> None:
    basename_prob = os.path.splitext(quad_paths.filepath_prob)[0]
    apply_model_to_data.apply_model_to_site(
        experiment.model, data_container, [quad_paths.filepath_features], basename_prob, exclude_feature_nodata=True)


def _crop_model_probabilities_raster(quad_paths: QuadPaths) -> None:
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
    # Apply cropping - note that we can't overwrite so we need to create and then overwrite
    options_translate = gdal.TranslateOptions(
        projWin=(llx, ury, urx, lly), projWinSRS=focal_srs, outputSRS=focal_srs,
        creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'],
    )
    tmp_filepath = re.sub('.tif', '_tmp.tif', quad_paths.filepath_prob)
    gdal.Translate(tmp_filepath, quad_paths.filepath_prob, options=options_translate)
    os.rename(tmp_filepath, quad_paths.filepath_prob)


def _mask_model_probabilities_raster(quad_paths: QuadPaths) -> None:
    command = 'gdal_calc.py -A {filepath_focal} --A_band=4 -B {filepath_prob} --B_band=1 --allBands=B ' + \
              '--outfile {outfile} --NoDataValue=-9999 --overwrite --quiet --calc="B * (A == 255) + -9999 * (A == 0)"'
    command = command.format(filepath_focal=quad_paths.filepath_focal_quad, filepath_prob=quad_paths.filepath_prob,
                             outfile=quad_paths.filepath_prob)
    subprocess.run(shlex.split(command))


def _generate_model_classifications_raster(
        quad_paths: QuadPaths,
        data_container: data_core.DataContainer,
) -> None:
    basename_mle = os.path.splitext(quad_paths.filepath_mle)[0]
    apply_model_to_data.maximum_likelihood_classification(
        quad_paths.filepath_prob, data_container, basename_mle, creation_options=['TILED=YES', 'COMPRESS=DEFLATE'])


def _mask_model_classifications_raster(quad_paths: QuadPaths) -> None:
    command = 'gdal_calc.py -A {filepath_focal} --A_band=4 -B {filepath_mle} --B_band=1 --allBands=B ' + \
              '--outfile {outfile} --NoDataValue=-9999 --overwrite --quiet --calc="B * (A == 255) + -9999 * (A == 0)"'
    command = command.format(filepath_focal=quad_paths.filepath_focal_quad, filepath_prob=quad_paths.filepath_mle,
                             outfile=quad_paths.filepath_mle)
    subprocess.run(shlex.split(command))


def _check_model_classifications_include_reef(quad_paths: QuadPaths) -> bool:
    raster = gdal.Open(quad_paths.filepath_mle)
    band = raster.GetRasterBand(1)
    classes = band.ReadAsArray()
    return np.any(classes == 3)


def _generate_model_classification_shapefile(quad_paths: QuadPaths) -> None:
    command = 'gdal_polygonize.py {filepath_mle} {filepath_shapefile} -q'.format(
        filepath_mle=quad_paths.filepath_mle, filepath_shapefile=quad_paths.filepath_shapefile)
    subprocess.run(shlex.split(command))


def _scale_model_probabilities_raster(quad_paths: QuadPaths) -> None:
    options_translate = gdal.TranslateOptions(
        outputType=gdal.GDT_Byte, creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'], scaleParams=[[0, 1, 0, 100]],
        noData=255,
    )
    tmp_filepath = re.sub('.tif', '_tmp.tif', quad_paths.filepath_prob)
    gdal.Translate(tmp_filepath, quad_paths.filepath_prob, options=options_translate)
    os.rename(tmp_filepath, quad_paths.filepath_prob)


def _scale_model_classifications_raster(quad_paths: QuadPaths) -> None:
    options_translate = gdal.TranslateOptions(
        outputType=gdal.GDT_Byte, creationOptions=['TILED=YES', 'COMPRESS=DEFLATE'], noData=255
    )
    tmp_filepath = re.sub('.tif', '_tmp.tif', quad_paths.filepath_mle)
    gdal.Translate(tmp_filepath, quad_paths.filepath_mle, options=options_translate)
    os.rename(tmp_filepath, quad_paths.filepath_mle)


def _get_quad_paths(quad_blob: data_bucket.QuadBlob) -> QuadPaths:
    # Directories
    dir_quad = os.path.join(_DIR_SCRATCH_TMP, quad_blob.quad_focal)
    dir_for_upload = os.path.join(dir_quad, 'for_upload')
    # Filepaths - for input files
    filepath_lock = os.path.join(_DIR_SCRATCH_TMP, '{}.lock'.format(quad_blob.quad_focal))
    filepath_focal_quad = os.path.join(dir_quad, quad_blob.quad_focal + data_bucket.FILENAME_SUFFIX_FOCAL)
    filepath_features = os.path.join(dir_quad, 'features.vrt')
    # Filepaths - for output files which are uploaded
    filepath_prob = os.path.join(dir_for_upload, '{}_model_probs.tif'.format(quad_blob.quad_focal))
    filepath_mle = os.path.join(dir_for_upload, '{}_model_class.tif'.format(quad_blob.quad_focal))
    filepath_shapefile = os.path.join(dir_for_upload, '{}_model_class.shp'.format(quad_blob.quad_focal))
    return QuadPaths(
        dir_quad=dir_quad, dir_for_upload=dir_for_upload, filepath_lock=filepath_lock,
        filepath_focal_quad=filepath_focal_quad, filepath_features=filepath_features, filepath_prob=filepath_prob,
        filepath_mle=filepath_mle, filepath_shapefile=filepath_shapefile,
    )
