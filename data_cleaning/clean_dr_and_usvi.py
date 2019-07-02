from collections import OrderedDict
import logging
import os
import sys
from typing import List

import fiona
import numpy as np
import shapely.geometry
from shapely.geometry.base import BaseGeometry
import shapely.ops


REEF_CLASSES = {
    'Coral Back-reef/flat', 'Coral Fore-reef', 'Coral Patch Deep', 'Coral Reef Crest', 'Gorgonian/Soft Coral',
    'Hardbottom with Algae', 'Sand Deep with sparse Macroalgae', 'Sand Shallow', 'Seagrass Dense', 'Seagrass Sparse'
}
BUFFERS_REEF = (75, )
BUFFERS_ADJACENT = (600, )

FILENAME_REEF = 'reef_{}.shp'
FILENAME_ADJACENT = 'adjacent_{}.shp'
FILENAME_LANDWATER = 'landwater_{}.shp'
SHAPEFILE_SCHEMA = {'properties': OrderedDict([('class', 'str:254')]), 'geometry': 'Polygon'}
PROPERTIES_REEF = OrderedDict([('class', 'reef')])
PROPERTIES_ADJACENT = OrderedDict([('class', 'reef_adjacent')])
PROPERTIES_LANDWATER = OrderedDict([('class', 'land_water')])


FILENAME_LOG = 'clean.log'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
logger.addHandler(_handler)
_handler = logging.FileHandler(FILENAME_LOG)
_handler.setFormatter(_formatter)
logger.addHandler(_handler)


def clean_dr():
    filepath_source = '../data/dr/DR_V1.shp'
    dir_out = '../data/dr/'
    filepath_reef = os.path.join(dir_out, FILENAME_REEF.format('buffer_75'))
    if not os.path.exists(filepath_reef):
        logger.info('Get reef multipolygon')
        reef_multipolygon = _get_reef_multipolygon(filepath_source)
        logger.info('Save reef multipolygons buffered')
        _save_cleaned_reef_multipolygons_for_review(reef_multipolygon, filepath_source, dir_out)
    logger.info('Save reef adjacent areas')
    _save_reef_adjacent_area_for_review(
        os.path.join(dir_out, FILENAME_REEF.format('buffer_75')), dir_out)
    _save_landwater_area_for_review(filepath_source, dir_out)
    _save_landwater_areas_clipped_for_review(filepath_source, dir_out)


def _get_reef_multipolygon(filepath: str) -> shapely.geometry.MultiPolygon:
    logger.info('Read features')
    with fiona.open(filepath) as source:
        reef_components = [feature for feature in source if feature['properties']['Class'] in REEF_CLASSES]
    logger.info('Get geometries')
    reef_components = _get_geometries_from_features(reef_components)
    logger.info('Clean geometries')
    reef_components = _clean_geometries(reef_components)
    logger.info('Union geometries')
    return shapely.ops.unary_union(reef_components)


def _save_cleaned_reef_multipolygons_for_review(
        reef_multipolygon: shapely.geometry.MultiPolygon,
        filepath_source: str,
        dir_out: str
) -> None:
    for buffer in BUFFERS_REEF:
        filepath_output = os.path.join(dir_out, FILENAME_REEF.format('buffer_{}'.format(buffer)))
        if os.path.exists(filepath_output):
            continue
        logger.info('Save reef with buffer of {}'.format(buffer))
        logger.info('Buffer reef')
        tmp_reef = reef_multipolygon.buffer(buffer).buffer(-buffer)
        logger.info('Clean geometries')
        tmp_reef = _clean_geometries([tmp_reef])
        logger.info('Write to shapefile')
        _write_geometries_to_shapefile(tmp_reef, [PROPERTIES_REEF] * len(tmp_reef), filepath_source, filepath_output)


def _save_reef_adjacent_area_for_review(
        filepath_reef_source: str,
        dir_out: str
) -> None:
    with fiona.open(filepath_reef_source) as source:
        reef_components = [feature for feature in source]
    reef_components = _get_geometries_from_features(reef_components)
    for buffer in BUFFERS_ADJACENT:
        filepath_output = os.path.join(dir_out, FILENAME_ADJACENT.format('buffer_{}'.format(buffer)))
        if os.path.exists(filepath_output):
            continue
        logger.info('Save reef adjacent area with buffer of {}'.format(buffer))
        logger.info('Buffer adjacent areas')
        tmp_adjacent = [component.buffer(buffer).difference(component) for component in reef_components]
        logger.info('Clean geometries')
        tmp_adjacent = _clean_geometries(tmp_adjacent)
        logger.info('Write to shapefile')
        _write_geometries_to_shapefile(
            tmp_adjacent, [PROPERTIES_ADJACENT] * len(tmp_adjacent), filepath_reef_source, filepath_output)
    return


def _save_landwater_area_for_review(
        filepath_source: str,
        dir_out: str
) -> None:
    filepath_output = os.path.join(dir_out, FILENAME_LANDWATER.format('unclipped'))
    if os.path.exists(filepath_output):
        return
    logger.info('Read features')
    with fiona.open(filepath_source) as source:
        other_components = [feature for feature in source if feature['properties']['Class'] not in REEF_CLASSES]
    logger.info('Get geometries')
    other_components = _get_geometries_from_features(other_components)
    logger.info('Clean geometries')
    other_components = _clean_geometries(other_components)
    logger.info('Merge small geometries')
    other_components = _merge_small_landwater_geometries(other_components)
    logger.info('Save shapefile')
    _write_geometries_to_shapefile(
        other_components, [PROPERTIES_LANDWATER] * len(other_components), filepath_source, filepath_output)


def _merge_small_landwater_geometries(geometries: List[BaseGeometry]) -> List[shapely.geometry.Polygon]:
    finalized = list()
    unmerged = list()
    mean_area = np.mean(np.array([geometry.area for geometry in geometries]))
    for geometry in geometries:
        if geometry.area > mean_area:
            finalized.append(geometry)
        else:
            unmerged.append(geometry)
    finalized = _clean_geometries(finalized)
    merged = shapely.ops.unary_union(unmerged)
    cleaned = _clean_geometries(merged)
    return finalized + cleaned


def _save_landwater_areas_clipped_for_review(filepath_source: str, dir_out: str) -> None:
    logger.info('Read features')
    filepath_output = os.path.join(dir_out, FILENAME_LANDWATER.format('clipped'))
    if os.path.exists(filepath_output):
        return
    logger.info('Read features')
    with fiona.open(os.path.join(dir_out, FILENAME_LANDWATER.format('unclipped'))) as source:
        landwater_components = [feature for feature in source]
    logger.info('Get geometries')
    landwater_components = _get_geometries_from_features(landwater_components)
    logger.info('Read features')
    with fiona.open(os.path.join(dir_out, FILENAME_ADJACENT.format('buffer_600'))) as source:
        adjacent_components = [feature for feature in source]
    logger.info('Create multipolygon for adjacent')
    adjacent_components = shapely.geometry.MultiPolygon(adjacent_components)
    logger.info('Calculate overlap')
    landwater_components = [landwater.intersection(adjacent_components) for landwater in landwater_components]
    logger.info('Clean geometries')
    landwater_components = _clean_geometries(landwater_components)
    logger.info('Save shapefile')
    _write_geometries_to_shapefile(
        landwater_components, [PROPERTIES_LANDWATER] * len(landwater_components), filepath_source, filepath_output)


def _get_geometries_from_features(features: List[dict]) -> List[BaseGeometry]:
    return [shapely.geometry.asShape(feature['geometry']) for feature in features]


def _clean_geometries(geometries: List[BaseGeometry]) -> List[shapely.geometry.Polygon]:
    geometries = [geometry if geometry.is_valid else geometry.buffer(0) for geometry in geometries]
    return _convert_geometries_to_polygons(geometries)


def _convert_geometries_to_polygons(geometries: List[BaseGeometry]) -> List[shapely.geometry.Polygon]:
    polygons = list()
    for geometry in geometries:
        type_ = geometry.geom_type
        if type_ == 'Polygon':
            polygons.append(geometry)
        elif type_ == 'MultiPolygon':
            polygons.extend(list(geometry))
        elif type_ in ('LineString', 'Point'):
            continue
        elif type_ == 'GeometryCollection':
            polygons.extend(_convert_geometries_to_polygons(list(geometry)))
        else:
            raise AssertionError('Unexpected geometry type:  {}'.format(type_))
    return polygons


def _write_geometries_to_shapefile(
        geometries: List[shapely.geometry.Polygon],
        properties: List[dict],
        filepath_source: str,
        filepath_output: str
) -> None:
    with fiona.open(filepath_source) as source:
        with fiona.open(filepath_output, 'w', driver=source.driver, crs=source.crs, schema=SHAPEFILE_SCHEMA) as output:
            for geometry, property in zip(geometries, properties):
                output.write({'geometry': shapely.geometry.mapping(geometry), 'properties': property})


if __name__ == '__main__':
    clean_dr()
