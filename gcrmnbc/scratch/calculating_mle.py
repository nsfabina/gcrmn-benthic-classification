CODE_LAND = 0  # Dark brown
CODE_WATER_TERRESTRIAL = 1  # Light brown

CODE_WATER_SHALLOW = 10  # Light blue
CODE_WATER_DEEP = 11  # Dark blue

CODE_FOREREEF = 20   # Medium green
CODE_REEFFLAT_SHALLOW = 21  # Light green
CODE_REEFFLAT_VARIABLE = 22  # Light green
CODE_PINNACLES = 23  # Medium green
CODE_CONSTRUCTIONS = -9999  # Pink

CODE_NONREEF_SHALLOW = 30  # Light yellow
CODE_NONREEF_VARIABLE = 31  # Medium yellow
CODE_NONREEF_DEEP = 32  # Dark yellow


import gdal
import numpy as np
import os


filename_in = 'calval_probs.tif'
filename_mle_out = 'calval_mle_4.tif'
filename_prob_out = 'calval_heat.tif'


for dir_exp in ('millennium_25_aug', 'millennium_50_aug'):
    models = os.listdir(os.path.join(dir_exp, 'custom'))
    for model in models:
        dir_in = os.path.join(dir_exp, 'custom', model)
        reefs = os.listdir(dir_in)
        for reef in reefs:
            print(model, reef)
            filepath_in = os.path.join(dir_in, reef, filename_in)
            basename_out = os.path.join(dir_in, reef)
            process_file(filepath_in, basename_out)


def process_file(filepath_in, basename_out):
    raster_src = gdal.Open(filepath_in)
    # Set class indices
    idxs_land = (0, 1)
    idxs_water = (2, 3)
    idxs_reef = (4, 5, 6, 7)
    idxs_nonreef = (8, 9, 10)
    idxs_all = (idxs_land, idxs_water, idxs_reef, idxs_nonreef)
    # Get probabilities
    probs_all = list()
    for idxs_class in idxs_all:
        probs = None
        for idx_band in idxs_class:
            band = raster_src.GetRasterBand(idx_band + 1)
            arr = band.ReadAsArray()
            if probs is None:
                probs = arr
            else:
                probs += arr
        probs_all.append(probs)
    probs_all = np.dstack(probs_all)
    classes = np.nanargmax(probs_all, axis=-1)
    # Write to file argmax
    filepath_dest = os.path.join(basename_out, filename_mle_out)
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_dest, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Int16)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(classes)
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest
    # Write to file argmax
    filepath_dest = os.path.join(basename_out, filename_prob_out)
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_dest, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Int16)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(probs_all[..., 2])
    band_dest.SetNoDataValue(-9999)
    del band_dest, raster_dest

