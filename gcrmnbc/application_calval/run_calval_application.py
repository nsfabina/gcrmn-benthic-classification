from argparse import ArgumentParser
from logging import Logger
import os

import gdal
import numpy as np

from bfgn.data_management import apply_model_to_data, data_core
from bfgn.experiments import experiments

from gcrmnbc.application_calval import submit_calculation_slurm
from gcrmnbc.utils import encodings_mp, gdal_command_line, logs, paths, shared_configs


def run_application(config_name: str, label_experiment: str, response_mapping: str, run_all: bool = False) -> None:
    config = shared_configs.build_dynamic_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    logger = logs.get_model_logger(
        'log_run_calval_application', config_name=config_name, label_experiment=label_experiment,
        response_mapping=response_mapping,
    )

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Apply model
    dir_model_out = paths.get_dir_calval_data_experiment_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    reefs = sorted([reef for reef in os.listdir(paths.DIR_DATA_EVAL)])
    for idx_filepath, reef in enumerate(reefs):
        logger.debug('Applying model to reef {}'.format(reef))
        dir_reef_in = paths.get_dir_eval_data_experiment(reef=reef, label_experiment=label_experiment)
        dir_reef_out = os.path.join(dir_model_out, reef)
        _apply_to_raster(experiment, data_container, dir_reef_in, dir_reef_out, logger)

    # Create application.complete if all files are done
    are_reefs_complete = list()
    for reef in reefs:
        filepath_reef_complete = os.path.join(dir_model_out, reef, paths.FILENAME_APPLY_CALVAL_COMPLETE)
        are_reefs_complete.append(os.path.exists(filepath_reef_complete))
    if all(are_reefs_complete):
        filepath_model_complete = paths.get_filepath_calval_apply_complete(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        open(filepath_model_complete, 'w')
        if run_all and 'millennium' not in label_experiment:
            submit_calculation_slurm.submit_calculation_slurm(
                labels_experiments=label_experiment, response_mappings=response_mapping, recalculate=False)


def _apply_to_raster(
        experiment: experiments.Experiment,
        data_container: data_core.DataContainer,
        dir_reef_in: str,
        dir_reef_out: str,
        logger: Logger
) -> None:
    if not os.path.exists(dir_reef_out):
        try:
            os.makedirs(dir_reef_out)
        except FileExistsError:
            pass

    # Set filepaths
    filepath_probs_detail = os.path.join(dir_reef_out, 'calval_probs_detail.tif')
    filepath_probs_coarse = os.path.join(dir_reef_out, 'calval_probs_coarse.tif')
    filepath_mle_detail = os.path.join(dir_reef_out, 'calval_mle_detail.tif')
    filepath_mle_coarse = os.path.join(dir_reef_out, 'calval_mle_coarse.tif')
    filepath_heat = os.path.join(dir_reef_out, 'calval_reef_heat.tif')
    filepaths_out = (
        filepath_probs_detail, filepath_probs_coarse, filepath_mle_detail, filepath_mle_coarse, filepath_heat
    )
    filepath_lock = os.path.join(dir_reef_out, 'calval_apply.lock')
    filepath_complete = os.path.join(dir_reef_out, paths.FILENAME_APPLY_CALVAL_COMPLETE)
    filepath_features = os.path.join(dir_reef_in, 'features.vrt')

    # Return early if application is completed or in progress
    if all([os.path.exists(filepath) for filepath in filepaths_out]):
        logger.debug('Skipping application:  output files already exist')
        open(filepath_complete, 'w')
        return
    if os.path.exists(filepath_lock):
        logger.debug('Skipping application:  lock file already exists at {}'.format(filepath_lock))
        return

    # Acquire the file lock or return if we lose the race condition
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        logger.debug('Skipping application:  lock file acquired by another process at {}'.format(filepath_lock))
        return

    # Apply model to raster and clean up file lock
    try:
        # Create detailed outputs with all classes
        basename_probs = os.path.splitext(filepath_probs_detail)[0]
        basename_mle = os.path.splitext(filepath_mle_detail)[0]
        apply_model_to_data.apply_model_to_site(
            experiment.model, data_container, [filepath_features], basename_probs, exclude_feature_nodata=True)
        apply_model_to_data.maximum_likelihood_classification(
            filepath_probs_detail, data_container, basename_mle, creation_options=['TILED=YES', 'COMPRESS=DEFLATE'])
        _mask_and_compress_probs_raster(filepath_probs_detail, filepath_features, logger)
        _mask_and_compress_mle_raster(filepath_mle_detail, filepath_features, logger)
        # Create coarse outputs with only land/water/reef/notreef classes
        _create_probs_coarse(filepath_probs_detail, filepath_probs_coarse, logger)
        _create_mle_coarse(filepath_probs_coarse, filepath_mle_coarse, logger)
        _create_reef_only_heatmap(filepath_probs_coarse, filepath_heat, logger)
        logger.debug('Application success, removing lock file and placing complete file')
        open(filepath_complete, 'w')
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)
        logger.debug('Lock file removed')


def _mask_and_compress_probs_raster(filepath_probs: str, filepath_features: str, logger: Logger) -> None:
    command = 'gdal_calc.py -A {filepath_probs} --allBands=A -B {filepath_features} --B_band=1 ' + \
              '--outfile={filepath_probs} --NoDataValue=255 ' + \
              '--type=Byte --co=COMPRESS=DEFLATE --co=TILED=YES --overwrite  ' + \
              '--calc="A*100 * (B != -9999) + 255 * (B == -9999)"'
    command = command.format(filepath_probs=filepath_probs, filepath_features=filepath_features)
    gdal_command_line.run_gdal_command(command, logger)


def _mask_and_compress_mle_raster(filepath_mle: str, filepath_features: str, logger: Logger) -> None:
    command = 'gdal_calc.py -A {filepath_mle} --allBands=A -B {filepath_features} --B_band=1 ' + \
              '--outfile={filepath_mle} --NoDataValue=255 ' + \
              '--type=Byte --co=COMPRESS=DEFLATE --co=TILED=YES --overwrite  ' + \
              '--calc="A * (B != -9999) + 255 * (B == -9999)"'
    command = command.format(filepath_mle=filepath_mle, filepath_features=filepath_features)
    gdal_command_line.run_gdal_command(command, logger)


def _create_probs_coarse(filepath_probs_detail: str, filepath_probs_coarse: str, logger: Logger) -> None:
    logger.debug('Create coarse probabilities raster')
    raster_src = gdal.Open(filepath_probs_detail)
    # Get class mappings
    probabilities = dict()
    for idx_code, (code_model, code_output) in enumerate(sorted(encodings_mp.MAPPINGS_OUTPUT.items())):
        probabilities.setdefault(code_output, None)
        band = raster_src.GetRasterBand(idx_code + 1)
        arr = band.ReadAsArray()
        if probabilities[code_output] is None:
            probabilities[code_output] = arr
        else:
            probabilities[code_output] += arr
    probabilities = [probs for code_output, probs in sorted(probabilities.items())]
    # Write to file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(
        filepath_probs_coarse, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Int16
    )
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    for idx_code, probs in enumerate(probabilities):
        band_dest = raster_dest.GetRasterBand(idx_code + 1)
        band_dest.WriteArray(probs)
        band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest


def _create_mle_coarse(filepath_probs_coarse: str, filepath_mle_coarse: str, logger) -> None:
    logger.debug('Create coarse MLE raster')
    raster_src = gdal.Open(filepath_probs_coarse)
    probabilities = list()
    for idx_band in range(raster_src.RasterCount):
        band = raster_src.GetRasterBand(idx_band + 1)
        probabilities.append(band.ReadAsArray())
    probabilities = np.dstack(probabilities)
    classes = np.nanargmax(probabilities, axis=-1)
    # Write to file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(
        filepath_mle_coarse, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Int16
    )
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(classes)
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest


def _create_reef_only_heatmap(filepath_probs_coarse: str, filepath_heat: str, logger: Logger) -> None:
    logger.debug('Create reef heatmap raster')
    # Get reef class index
    all_classes = sorted(set(encodings_mp.MAPPINGS_OUTPUT.values()))
    idx_reef = all_classes.index(encodings_mp.OUTPUT_CODE_REEF)
    # Get reef class probs
    raster_src = gdal.Open(filepath_probs_coarse)
    band = raster_src.GetRasterBand(idx_reef + 1)
    probs = band.ReadAsArray()
    # Write to file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_heat, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Int16)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(probs)
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    run_application(**args)
