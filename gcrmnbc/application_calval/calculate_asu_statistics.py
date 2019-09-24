import argparse
import json
import os
import time

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

    _logger.debug('Calculating ASU statistics')
    if os.path.exists(filepath_data_out) and not recalculate:
        _logger.debug('Loading existing statistics')
        with open(filepath_data_out) as file_:
            statistics = json.load(file_)
    else:
        _logger.debug('Calculating statistics from scratch')
        statistics = dict()

    reefs = sorted([reef for reef in os.listdir(dir_model) if os.path.isdir(os.path.join(dir_model, reef))])
    _logger.debug('Calculating statistics for reefs: {}'.format(reefs))
    for reef in reefs:
        if reef in statistics and not recalculate:
            _logger.debug('Skipping {}:  already calculated'.format(reef))
            continue
        _logger.debug('Calculating statistics for {}'.format(reef))
        statistics[reef] = _calculate_asu_statistics_for_reef(reef, config_name, response_mapping)
        _logger.debug('Saving statistics'.format(reef))
        with open(filepath_data_out, 'w') as file_:
            json.dump(statistics, file_)
    _logger.debug('Calculations complete, generating report')
    shared_report.generate_pdf_summary_report(statistics, 'ASU', filepath_fig_out, config_name)
    _logger.debug('Report generation complete')


def _calculate_asu_statistics_for_reef(reef: str, config_name: str, response_mapping: str) -> dict:
    _logger.debug('Load UQ reef features')
    uq = fiona.open(_FILEPATH_UQ_OUTLINE.format(reef))
    uq_reef = shapely.geometry.shape(next(iter(uq))['geometry'])
    uq_reef_bounds = uq_reef.convex_hull

    _logger.debug('Load ASU reef features')
    dir_model = _DIR_STATS_OUT.format(config_name, response_mapping)
    filepath_asu_outline = os.path.join(dir_model, reef, _FILENAME_ASU_OUTLINE)
    asu_features = fiona.open(filepath_asu_outline)

    _logger.debug('Parse ASU features near UQ reef bounds')
    asu_polygons = list()
    for idx_feature, feature in enumerate(asu_features):
        geom_type = feature['geometry']['type']
        assert geom_type == 'Polygon', 'Reef features are expected to all be polygons, but found {}'.format(geom_type)
        polygon = shapely.geometry.shape(feature['geometry'])
        if polygon.intersects(uq_reef_bounds):
            asu_polygons.append(polygon)
    asu_reef = shapely.geometry.MultiPolygon(asu_polygons)

    _logger.debug('Calculate performance statistics')
    time_start = time.time()
    stats = shared_statistics.calculate_model_performance_statistics(asu_reef, uq_reef)
    _logger.debug('Total time:  {}'.format(time.time() - time_start))
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--recalculate', action='store_true')
    args = parser.parse_args()
    calculate_asu_statistics(args.config_name, args.response_mapping, args.recalculate)
