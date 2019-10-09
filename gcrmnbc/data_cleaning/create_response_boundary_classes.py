import os
import re

import gdal
import numpy as np
import skimage.segmentation
from tqdm import tqdm

from gcrmnbc.utils import encodings, logs, paths


_logger = logs.get_logger(__file__)

_LABEL_EDGE = -8888


def create_response_boundary_classes() -> None:
    _logger.info('Create response boundary classes')
    subdirs_data = ('downsample_50', )
    thicknesses = (3, )
    for subdir_data, thickness in zip(subdirs_data, thicknesses):
        dir_data = os.path.join(paths.DIR_DATA_TRAIN, subdir_data)
        filepaths_srcs = [
            os.path.join(dir_data, fn) for fn in os.listdir(dir_data)
            if fn.endswith('responses_lwr.tif') or fn.endswith('responses_lwrn.tif')
        ]
        for filepath_src in tqdm(sorted(filepaths_srcs), desc='Create boundary classes for {}'.format(subdir_data)):
            _logger.debug('Processing file:  {}'.format(filepath_src))
            filepath_dest = re.sub('.tif', 'b.tif', filepath_src)
            if os.path.exists(filepath_dest):
                continue
            _create_response_boundary_classes_for_filepath(filepath_src, filepath_dest, thickness)


def _create_response_boundary_classes_for_filepath(filepath_src: str, filepath_dest: str, thickness: int) -> None:
    # Open original data
    raster_src = gdal.Open(filepath_src)
    band_src = raster_src.GetRasterBand(1)
    original = band_src.ReadAsArray()
    # Add boundaries
    with_boundaries = _add_class_boundaries(original, thickness)
    # Write output file
    driver = raster_src.GetDriver()
    raster_dest = driver.Create(filepath_dest, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Int16)
    raster_dest.SetProjection(raster_src.GetProjection())
    raster_dest.SetGeoTransform(raster_src.GetGeoTransform())
    band_dest = raster_dest.GetRasterBand(1)
    band_dest.WriteArray(with_boundaries)
    band_dest.SetNoDataValue(-9999)
    del band_dest, band_src, raster_dest, raster_src


def _add_class_boundaries(original: np.array, thickness: int) -> np.array:
    # Calculate edges
    classes = (encodings.LAND, encodings.WATER, encodings.REEF_TOP, encodings.NOT_REEF_TOP)
    class_edges = dict()
    for class_ in classes:
        class_image = original.copy()
        class_image[class_image != encodings.MAPPINGS[class_]] = 0
        class_edges[class_] = _get_edges(class_image, thickness)
    del class_image
    # Add class boundaries
    combinations = (
        (encodings.LAND, encodings.WATER, encodings.EDGE_LW),
        (encodings.LAND, encodings.REEF_TOP, encodings.EDGE_LR),
        (encodings.LAND, encodings.NOT_REEF_TOP, encodings.EDGE_LN),
        (encodings.WATER, encodings.REEF_TOP, encodings.EDGE_WR),
        (encodings.WATER, encodings.NOT_REEF_TOP, encodings.EDGE_WN),
        (encodings.REEF_TOP, encodings.NOT_REEF_TOP, encodings.EDGE_RN),
    )
    for class_a, class_b, edge_ab in combinations:
        idx_edge = np.logical_and(class_edges[class_a], class_edges[class_b])
        original[idx_edge] = encodings.MAPPINGS[edge_ab]
    return original


def _get_edges(arr: np.array, thickness: int) -> np.array:
    edges = arr.copy()
    for idx_thick in range(thickness):
        edges[skimage.segmentation.find_boundaries(edges, connectivity=2, mode='thick')] = _LABEL_EDGE
    return edges


if __name__ == '__main__':
    create_response_boundary_classes()

