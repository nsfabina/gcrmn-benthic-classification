from logging import Logger
import os

from bfgn.data_management import apply_model_to_data, data_core
from bfgn.experiments import experiments
import gdal
import numpy as np
import sklearn.ensemble

from gcrmnbc.utils import encodings_mp, gdal_command_line, logs, paths


_logger = logs.get_logger(__file__)


def apply_to_raster(
        experiment: experiments.Experiment,
        data_container: data_core.DataContainer,
        classifier: sklearn.ensemble.RandomForestClassifier,
        filepath_features: str,
        dir_out: str
) -> None:
    # Set filepaths
    filepath_probs_detail = os.path.join(dir_out, 'probs_detail.tif')
    filepath_probs_coarse = os.path.join(dir_out, 'probs_coarse.tif')
    filepath_mle_detail = os.path.join(dir_out, 'mle_detail.tif')
    filepath_mle_coarse = os.path.join(dir_out, 'mle_coarse.tif')
    filepath_heat = os.path.join(dir_out, 'reef_heat.tif')
    filepath_outline = os.path.join(dir_out, 'reef_outline.tif')
    filepaths_out = (
        filepath_probs_detail, filepath_probs_coarse, filepath_mle_detail, filepath_mle_coarse, filepath_heat
    )
    filepath_lock = os.path.join(dir_out, paths.FILENAME_APPLY_LOCK)
    filepath_complete = os.path.join(dir_out, paths.FILENAME_APPLY_COMPLETE)

    # Return early if application is completed or in progress
    if all([os.path.exists(filepath) for filepath in filepaths_out]):
        _logger.debug('Skipping application:  output files already exist')
        open(filepath_complete, 'w')
        return
    if os.path.exists(filepath_lock):
        _logger.debug('Skipping application:  lock file already exists at {}'.format(filepath_lock))
        return

    # Acquire the file lock or return if we lose the race condition
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        _logger.debug('Skipping application:  lock file acquired by another process at {}'.format(filepath_lock))
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
        # Create coarse outputs with only land/water/reef/notreef classes
        _create_probs_coarse(filepath_probs_detail, filepath_probs_coarse, _logger)
        _create_mle_coarse(filepath_probs_coarse, filepath_mle_coarse, _logger)
        _create_reef_only_heatmap(filepath_probs_coarse, filepath_heat, _logger)
        _create_reef_only_outline(filepath_probs_detail, filepath_outline, classifier, _logger)
        # Mask and compress files
        # TODO:  mask and compress probs detail doesn't work! end up with 0s
        _mask_and_compress_raster(filepath_probs_detail, filepath_features, _logger)
        _mask_and_compress_raster(filepath_probs_coarse, filepath_features, _logger)
        _mask_and_compress_raster(filepath_mle_detail, filepath_features, _logger)
        _mask_and_compress_raster(filepath_mle_coarse, filepath_features, _logger)
        _mask_and_compress_raster(filepath_heat, filepath_features, _logger)
        _mask_and_compress_raster(filepath_outline, filepath_features, _logger)
        _logger.debug('Application success, removing lock file and placing complete file')
        open(filepath_complete, 'w')
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)
        _logger.debug('Lock file removed')


def _mask_and_compress_raster(filepath_src: str, filepath_features: str, _logger: Logger) -> None:
    raster = gdal.Open(filepath_features)
    if raster.RasterCount == 3:
        band_nodata = 1
        value_nodata = -9999
    elif raster.RasterCount == 4:
        band_nodata = 4
        value_nodata = 0
    command = 'gdal_calc.py -A {filepath_src} --allBands=A -B {filepath_features} --B_band={band_nodata} ' + \
              '--outfile={filepath_probs} --NoDataValue=255 --type=Byte --co=COMPRESS=DEFLATE --co=TILED=YES ' + \
              '--overwrite --calc="A * (B != {value_nodata}) + 255 * (B == {value_nodata})"'
    command = command.format(
        filepath_src=filepath_src, filepath_features=filepath_features, band_nodata=band_nodata,
        value_nodata=value_nodata
    )
    gdal_command_line.run_gdal_command(command, _logger)


def _create_probs_coarse(filepath_probs_detail: str, filepath_probs_coarse: str, _logger: Logger) -> None:
    _logger.debug('Create coarse probabilities raster')
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
        filepath_probs_coarse, raster_src.RasterXSize, raster_src.RasterYSize, len(probabilities), gdal.GDT_Byte
    )
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    for idx_code, probs in enumerate(probabilities):
        band_dest = raster_dest.GetRasterBand(idx_code + 1)
        band_dest.WriteArray(100 * probs)
        band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest


def _create_mle_coarse(filepath_probs_coarse: str, filepath_mle_coarse: str, _logger) -> None:
    _logger.debug('Create coarse MLE raster')
    raster_src = gdal.Open(filepath_probs_coarse)
    probabilities = list()
    for idx_band in range(raster_src.RasterCount):
        band = raster_src.GetRasterBand(idx_band + 1)
        probabilities.append(band.ReadAsArray())
    probabilities = np.dstack(probabilities)
    classes = np.nanargmax(probabilities, axis=-1)
    # Write to file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_mle_coarse, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Byte)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(classes)
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest


def _create_reef_only_heatmap(filepath_probs_coarse: str, filepath_heat: str, _logger: Logger) -> None:
    _logger.debug('Create reef heatmap raster')
    # Get reef class index
    all_classes = sorted(set(encodings_mp.MAPPINGS_OUTPUT.values()))
    idx_reef = all_classes.index(encodings_mp.OUTPUT_CODE_REEF)
    # Get reef class probs
    raster_src = gdal.Open(filepath_probs_coarse)
    band = raster_src.GetRasterBand(idx_reef + 1)
    probs = band.ReadAsArray()
    # Write to file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_heat, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Byte)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(probs)
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest


def _create_reef_only_outline(
        filepath_probs_detail: str,
        filepath_outline: str,
        classifier: sklearn.ensemble.RandomForestClassifier,
        _logger: Logger
) -> None:
    _logger.debug('Create reef outline raster')
    # Get reef class probs
    model_probabilities = list()
    raster_src = gdal.Open(filepath_probs_detail)
    num_bands = raster_src.RasterCount
    for idx_band in range(num_bands):
        band = raster_src.GetRasterBand(idx_band + 1)
        model_probabilities.append(band.ReadAsArray())
    # Predict classes
    shape = model_probabilities[0].shape[:2]
    model_probabilities = np.dstack(model_probabilities).reshape(-1, num_bands)
    model_predictions = classifier.predict(model_probabilities).astype(int).reshape(shape)
    # Write to file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_outline, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Byte)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(model_predictions)
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest
