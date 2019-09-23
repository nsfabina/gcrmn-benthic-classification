import argparse
import json
import os

import fiona
import shapely.geometry
import shapely.ops

from gcrmnbc.application_calval import shared_report, shared_statistics
from gcrmnbc.utils import logs


_logger = logs.get_logger(__file__)


_DIR_BASE = '/scratch/nfabina/gcrmn-benthic-classification/'

_FILEPATH_UQ_OUTLINE = os.path.join(_DIR_BASE, 'training_data/{}/clean/reef_outline.shp')

_DIR_CONFIG = os.path.join(_DIR_BASE, 'training_data_applied/{}/lwr')
_DIR_REEFS = os.path.join(_DIR_CONFIG, 'reefs')
_FILENAME_SUFFIX_ASU_OUTLINE = 'calval_reefs.shp'
_FILEPATH_DATA_OUT = os.path.join(_DIR_CONFIG, 'asu_statistics.json')
_FILEPATH_FIG_OUT = os.path.join(_DIR_CONFIG, 'asu_statistics.pdf')


def calculate_asu_statistics(config_name: str, recalculate: bool = False) -> None:
    _logger.info('Calculate ASU statistics for {} with recalculate {}'.format(config_name, recalculate))
    filepath_data_out = _FILEPATH_DATA_OUT.format(config_name)

    _logger.info('Calculating ASU statistics')
    if os.path.exists(filepath_data_out) and not recalculate:
        _logger.debug('Loading existing statistics')
        with open(filepath_data_out) as file_:
            statistics = json.load(file_)
    else:
        _logger.debug('Calculating statistics from scratch')
        statistics = dict()

    reefs = sorted([dir_reef for dir_reef in os.listdir(_DIR_REEFS.format(config_name))])
    for reef in reefs:
        if reef in statistics and not recalculate:
            _logger.debug('Skipping {}:  already calculated'.format(reef))
            continue
        _logger.info('Calculating statistics for {}'.format(reef))
        statistics[reef] = _calculate_asu_statistics_for_reef(reef, config_name)
        _logger.debug('Saving statistics'.format(reef))
        with open(filepath_data_out, 'w') as file_:
            json.dump(statistics, file_)
    _logger.info('Calculations complete, generating report')
    shared_report.generate_pdf_summary_report(statistics, 'ASU', _FILEPATH_FIG_OUT.format(config_name), config_name)
    _logger.info('Report generation complete')


def _calculate_asu_statistics_for_reef(reef: str, config_name: str) -> dict:
    _logger.debug('Load UQ reef features')
    uq = fiona.open(_FILEPATH_UQ_OUTLINE.format(reef))

    _logger.debug('Load ASU reef features')
    dir_asu_outline = os.path.join(_DIR_REEFS.format(config_name), reef)
    filepaths = [os.path.join(dir_asu_outline, filename) for filename in os.listdir(dir_asu_outline)
                 if filename.endswith(_FILENAME_SUFFIX_ASU_OUTLINE)]
    individual_asu = [fiona.open(filepath) for filepath in filepaths]

    _logger.debug('Generate UQ reef multipolygon')
    uq_reef = shapely.ops.unary_union([shapely.geometry.shape(feature['geometry']) for feature in uq])

    _logger.debug('Generate UQ reef bounds')
    x, y, w, z = uq_reef.bounds
    uq_bounds = shapely.geometry.Polygon([[x, y], [x, z], [w, z], [w, y]])

    _logger.debug('Generate ASU reef multipolygons nearby UQ reef bounds')
    individual_asu_reefs = list()
    for asu in individual_asu:
        shapes = list()
        for feature in asu:
            prediction = feature['properties']['DN']
            assert prediction in (0, 1), 'Reef predictions should either be 0 or 1, but found {}'.format(prediction)
            if prediction == 0:
                continue  # Reef == 1, nonreef == 0
            shape = shapely.geometry.shape(feature['geometry'])
            if shape.intersects(uq_bounds):
                shapes.append(shape)
        individual_asu_reefs.append(shapely.ops.unary_union(shapes))
    asu_reef = shapely.ops.unary_union(individual_asu_reefs)
    del individual_asu_reefs

    return shared_statistics.calculate_model_performance_statistics(asu_reef, uq_reef)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_names')
    parser.add_argument('-f', dest='recalculate', action='store_true')
    args = parser.parse_args()
    if args.config_names:
        config_names = args.config_names
    else:
        config_names = os.listdir(os.path.join(_DIR_BASE, 'training_data_applied'))
    for config_name in config_names:
        calculate_asu_statistics(config_name, args.recalculate)
