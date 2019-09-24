import argparse
import json
import os

import fiona
import shapely.geometry
import shapely.ops

from gcrmnbc.application_calval import shared_report, shared_statistics
from gcrmnbc.utils import logs


_logger = logs.get_logger(__file__)


_FILEPATH_UQ_OUTLINE = '/scratch/nfabina/gcrmn-benthic-classification/evaluation_data/{}/clean/reef_outline_union.shp'

_DIR_STATS_OUT = '/scratch/nfabina/gcrmn-benthic-classification/applied_data/{}/{}'
_FILENAME_DATA_OUT = 'asu_statistics.json'
_FILENAME_FIG_OUT = 'asu_statistics.pdf'
_FILENAME_ASU_OUTLINE = 'calval_reefs.shp'


def calculate_asu_statistics(config_name: str, response_mapping: str, recalculate: bool = False) -> None:
    _logger.info('Calculate ASU statistics for {} {} with recalculate {}'.format(
        config_name, response_mapping, recalculate))
    dir_model = _DIR_STATS_OUT.format(config_name, response_mapping)
    filepath_data_out = os.path.join(dir_model, _FILENAME_DATA_OUT)
    filepath_fig_out = os.path.join(dir_model, _FILENAME_FIG_OUT)

    _logger.info('Calculating ASU statistics')
    if os.path.exists(filepath_data_out) and not recalculate:
        _logger.debug('Loading existing statistics')
        with open(filepath_data_out) as file_:
            statistics = json.load(file_)
    else:
        _logger.debug('Calculating statistics from scratch')
        statistics = dict()

    reefs = sorted([reef for reef in os.listdir(dir_model) if reef != 'calval_application.complete'])
    for reef in reefs:
        if reef in statistics and not recalculate:
            _logger.debug('Skipping {}:  already calculated'.format(reef))
            continue
        _logger.info('Calculating statistics for {}'.format(reef))
        statistics[reef] = _calculate_asu_statistics_for_reef(reef, config_name, response_mapping)
        _logger.debug('Saving statistics'.format(reef))
        with open(filepath_data_out, 'w') as file_:
            json.dump(statistics, file_)
    _logger.info('Calculations complete, generating report')
    shared_report.generate_pdf_summary_report(statistics, 'ASU', filepath_fig_out, config_name)
    _logger.info('Report generation complete')


def _calculate_asu_statistics_for_reef(reef: str, config_name: str, response_mapping: str) -> dict:
    _logger.debug('Load UQ reef features')
    uq = fiona.open(_FILEPATH_UQ_OUTLINE.format(reef))
    uq_reef = shapely.geometry.shape(next(iter(uq))['geometry'])
    x, y, w, z = uq_reef.bounds
    uq_bounds = shapely.geometry.Polygon([[x, y], [x, z], [w, z], [w, y]])

    _logger.debug('Load ASU reef features')
    dir_model = _DIR_STATS_OUT.format(config_name, response_mapping)
    filepath_asu_outline = os.path.join(dir_model, reef, _FILENAME_ASU_OUTLINE)
    asu_features = fiona.open(filepath_asu_outline)

    _logger.debug('Generate ASU reef multipolygons nearby UQ reef bounds')
    asu_geometries = list()
    for feature in asu_features:
        prediction = feature['properties']['DN']
        assert prediction in (0, 1), 'Reef predictions should either be 0 or 1, but found {}'.format(prediction)
        if prediction == 0:
            continue  # reef == 1, nonreef == 0
        geometry = shapely.geometry.shape(feature['geometry'])
        if geometry.intersects(uq_bounds):
            asu_geometries.append(geometry)
    asu_reef = shapely.ops.unary_union(asu_geometries)
    return shared_statistics.calculate_model_performance_statistics(asu_reef, uq_reef)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--recalculate', action='store_true')
    args = parser.parse_args()
    calculate_asu_statistics(args.config_name, args.response_mapping, args.recalculate)
