from argparse import ArgumentParser
import joblib
import logging
import os
import re
import shutil
from typing import List

from bfgn.configuration import configs
from bfgn.data_management import data_core
from bfgn.experiments import experiments
import numpy as np
from osgeo import gdal, osr
import sklearn.ensemble

from gcrmnbc.application import application_millennium_project
from gcrmnbc.utils import data_bucket, logs, paths, shared_configs


# Hardcoded, too lazy to pass in as variable, don't know whether it'll always be the best model, whatever, handle later
FILENAME_BEST_CLASSIFIER = 'classifier_total_samples_model.joblib'


def run_application(config_name: str, label_experiment: str, response_mapping: str, model_version: str) -> None:
    config = shared_configs.build_dynamic_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    logger = logs.get_model_logger(
        logger_name='log_run_global_application', config_name=config_name, label_experiment=label_experiment,
        response_mapping=response_mapping,
    )
    # Get data and model objects
    logger.info('Create data and model objects')
    data_container = _load_dataset(config)
    experiment = _load_experiment(config, data_container)
    classifier = _load_classifier(config_name, label_experiment, response_mapping)
    logging.getLogger('bfgn').setLevel(logging.WARNING)  # Turn down BFGN logging
    # Get quad blobs and apply model
    logger.info('Get quad blobs')
    quad_blobs = data_bucket.get_imagery_quad_blobs()
    quad_blobs_sorted = dict()
    for quad_blob in quad_blobs:
        quad_blobs_sorted.setdefault(quad_blob.quad_focal, list()).append(quad_blob)
    logger.info('Apply model to quads')
    for idx_quad, (focal_quad, quad_blobs) in enumerate(sorted(quad_blobs_sorted.items(), key=lambda x: x[0])):
        logger.info('Apply model to quad {} ({} of {})'.format(focal_quad, 1+idx_quad, len(quad_blobs_sorted)))
        _apply_model_to_quad(
            quad_blobs=quad_blobs, data_container=data_container, experiment=experiment, classifier=classifier,
            label_experiment=label_experiment, response_mapping=response_mapping, model_name=config_name,
            model_version=model_version, logger=logger
        )


def _load_dataset(config: configs.Config) -> data_core.DataContainer:
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()
    return data_container


def _load_experiment(config: configs.Config, data_container: data_core.DataContainer) -> experiments.Experiment:
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)
    return experiment


def _load_classifier(
        config_name: str,
        label_experiment: str,
        response_mapping: str
) -> sklearn.ensemble.RandomForestClassifier:
    dir_classifier = paths.get_dir_validate_data_experiment_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    filepath_classifier = os.path.join(dir_classifier, FILENAME_BEST_CLASSIFIER)
    return joblib.load(filepath_classifier)


def _apply_model_to_quad(
        quad_blobs: List[data_bucket.QuadBlob],
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
        classifier: sklearn.ensemble.RandomForestClassifier,
        label_experiment: str,
        response_mapping: str,
        model_name: str,
        model_version: str,
        logger: logging.Logger
) -> None:
    quad_blob = quad_blobs[0]  # Quad blobs may have several quad blobs for a single quad, only need one
    logger.info('Apply model to quad {}'.format(quad_blob.quad_focal))

    # Set paths
    dir_tmp_apply = os.path.join(paths.DIR_DATA_GLOBAL_APPLY_TMP, quad_blob.quad_focal)
    dir_for_upload = os.path.join(dir_tmp_apply, 'for_upload')
    if '25' in label_experiment:
        suffix = '25'
    elif '50' in label_experiment:
        suffix = '50'
    dir_features = os.path.join(paths.DIR_DATA_GLOBAL, paths.SUBDIR_DATA_TRAIN_DOWNSAMPLE.format(suffix))
    filepath_features = os.path.join(dir_tmp_apply, 'features.vrt')
    filepath_noapply = os.path.join(paths.DIR_DATA_GLOBAL_NOAPPLY, quad_blob.quad_focal + '_no_apply')
    filepath_lock = os.path.join(paths.DIR_DATA_GLOBAL_APPLY_TMP, quad_blob.quad_focal + '.lock')
    filepath_focal_quad = os.path.join(dir_features, quad_blob.quad_focal + '_{}.tif'.format(suffix))
    filepaths_contextual_quads = list()
    for blob_context in quad_blob.blobs_context:
        quad = data_bucket.get_quad_name_from_blob_name(blob_context.name)
        filepath_context = os.path.join(dir_features, quad + '_{}.tif'.format(suffix))
        if os.path.exists(filepath_context):
            filepaths_contextual_quads.append(filepath_context)

    # Check if quad needs to be processed
    is_complete = all([
        data_bucket.check_is_quad_model_application_complete(qb, response_mapping, model_name, model_version)
        for qb in quad_blobs
    ])
    if is_complete:
        logger.debug('Skipping application, is already complete')
        return
    is_noapply = os.path.exists(filepath_noapply)
    if is_noapply:
        logger.debug('Skipping application, is noapply')
        return
    logger.debug('Acquire file lock')
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        logger.debug('Skipping application, already in progress')
        return

    logger.debug('Create temporary directory for data')
    if os.path.exists(dir_tmp_apply):
        shutil.rmtree(dir_tmp_apply)  # Remove directory if it already exists, to start from scratch
    os.makedirs(dir_for_upload)

    # Want to clean up if any of the following fail
    try:
        logger.debug('Create feature VRT')
        buffer = int(2 * experiment.config.data_build.window_radius - experiment.config.data_build.loss_window_radius)
        _create_feature_vrt(filepath_features, filepath_focal_quad, filepaths_contextual_quads, buffer)

        logger.debug('Apply model')
        application_millennium_project.apply_to_raster(
            experiment=experiment, data_container=data_container, classifier=classifier,
            filepath_features=filepath_features, dir_out=dir_for_upload
        )

        logger.debug('Remove detailed class rasters')
        filenames_output = ('probs_coarse.tif', 'mle_coarse.tif', 'reef_heat.tif', 'reef_outline.tif')
        for filename_remove in os.listdir(dir_for_upload):
            if filename_remove in filenames_output:
                continue
            os.remove(os.path.join(dir_for_upload, filename_remove))

        logger.debug('Crop output rasters')
        for filename_output in filenames_output:
            _crop_raster(os.path.join(dir_for_upload, filename_output), filepath_focal_quad)

        logger.debug('Check if quad contains reef')
        includes_reef = _check_model_classifications_include_reef(os.path.join(dir_for_upload, 'reef_outline.tif'))
        if not includes_reef:
            logger.debug('Application stopped early, no reef area found')
            for qb in quad_blobs:
                data_bucket.upload_model_no_apply_notification_for_quad_blob(qb)
            with open(filepath_noapply, 'w') as _:
                pass
            return

        logger.info('Uploading model results')
        for qb in quad_blobs:
            data_bucket.upload_model_application_results_for_quad_blob(
                dir_for_upload, qb, response_mapping, model_name, model_version)

        logger.info('Application success for quad {}'.format(quad_blob.quad_focal))
        # TODO
        # logger.debug('Delete model results from other versions and any outdated notifications')
        # data_bucket.delete_model_application_results_for_other_versions(
        #     quad_blob, response_mapping, model_name, model_version)
        for qb in quad_blobs:
            data_bucket.delete_model_corrupt_data_notification_if_exists(qb)

    except Exception as error_:
        raise error_

    finally:
        logger.debug('Removing temporary quad data from {}'.format(dir_tmp_apply))
        shutil.rmtree(dir_tmp_apply)
        logger.debug('Closing and removing lock file at {}'.format(dir_tmp_apply))
        file_lock.close()
        os.remove(filepath_lock)
        logger.debug('Lock file removed')


def _create_feature_vrt(
        filepath_vrt: str,
        filepath_focal_quad: str,
        filepaths_contextual_quads: List[str],
        buffer: int
) -> None:
    # Get raster parameters for building VRT
    focal_raster = gdal.Open(filepath_focal_quad)
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
    focal_raster = gdal.Open(filepath_focal_quad)
    focal_srs = osr.SpatialReference(wkt=focal_raster.GetProjection())
    filepaths_quads = [filepath_focal_quad] + filepaths_contextual_quads
    options_buildvrt = gdal.BuildVRTOptions(
        bandList=[1, 2, 3], outputBounds=(llx, lly, urx, ury), outputSRS=focal_srs, VRTNodata=-9999,
    )
    gdal.BuildVRT(filepath_vrt, filepaths_quads, options=options_buildvrt)


def _crop_raster(filepath_crop: str, filepath_focal_quad: str) -> None:
    # Get raster parameters for crop
    focal_raster = gdal.Open(filepath_focal_quad)
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
    tmp_filepath = re.sub('.tif', '_tmp.tif', filepath_crop)
    gdal.Translate(tmp_filepath, filepath_crop, options=options_translate)
    os.rename(tmp_filepath, filepath_crop)


def _check_model_classifications_include_reef(filepath_outline: str) -> bool:
    raster_src = gdal.Open(filepath_outline)
    band = raster_src.GetRasterBand(1)
    is_reef = band.ReadAsArray()
    return np.any(is_reef)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--model_version', required=True)
    args = vars(parser.parse_args())
    run_application(**args)
