import argparse
import json
import logging
import os
import time

import fiona
import shapely.geometry
import shapely.ops

from gcrmnbc.application_calval import shared_report, shared_statistics
from gcrmnbc.utils import logs, paths


_FILEPATH_UQ_OUTLINE = os.path.join(paths.DIR_DATA_EVAL, '{}/clean/reef_outline_union.shp')

_FILENAME_ASU_OUTLINE = 'calval_reefs.shp'


def calculate_asu_statistics(
        config_name: str,
        label_experiment: str,
        response_mapping: str,
        recalculate: bool = False
) -> None:
    logger = logs.get_model_logger(
        logger_name='log_calculate_asu_statistics', config_name=config_name, label_experiment=label_experiment,
        response_mapping=response_mapping
    )

    logger.info('Calculate ASU statistics for {} {} {} with recalculate {}'.format(
        config_name, label_experiment, response_mapping, recalculate))
    dir_model = paths.get_dir_calval_data_experiment_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    filepath_data_out = os.path.join(dir_model, paths.FILENAME_CALVAL_STATS)
    filepath_fig_out = os.path.join(dir_model, paths.FILENAME_CALVAL_FIGS)

    logger.debug('Calculating ASU statistics')
    if os.path.exists(filepath_data_out) and not recalculate:
        logger.debug('Loading existing statistics')
        with open(filepath_data_out) as file_:
            statistics = json.load(file_)
    else:
        logger.debug('Calculating statistics from scratch')
        statistics = dict()

    reefs = sorted([reef for reef in os.listdir(dir_model) if os.path.isdir(os.path.join(dir_model, reef))])
    logger.debug('Calculating statistics for reefs: {}'.format(reefs))
    for reef in reefs:
        if reef in statistics and not recalculate:
            logger.debug('Skipping {}:  already calculated'.format(reef))
            continue
        logger.debug('Calculating statistics for {}'.format(reef))
        statistics[reef] = _calculate_asu_statistics_for_reef(reef, dir_model, logger)
        logger.debug('Saving statistics'.format(reef))
        with open(filepath_data_out, 'w') as file_:
            json.dump(statistics, file_)
    logger.debug('Calculations complete, generating report')
    shared_report.generate_pdf_summary_report(statistics, 'ASU', filepath_fig_out, config_name)
    logger.debug('Report generation complete')


def _calculate_asu_statistics_for_reef(reef: str, dir_model: str, logger: logging.Logger) -> dict:
    logger.debug('Load UQ reef features')
    uq = fiona.open(_FILEPATH_UQ_OUTLINE.format(reef))
    uq_reef = shapely.geometry.shape(next(iter(uq))['geometry'])
    uq_reef_bounds = uq_reef.convex_hull

    logger.debug('Load ASU reef features')
    filepath_asu_outline = os.path.join(dir_model, reef, _FILENAME_ASU_OUTLINE)
    asu_features = fiona.open(filepath_asu_outline)

    logger.debug('Parse ASU features near UQ reef bounds')
    asu_polygons = list()
    for idx_feature, feature in enumerate(asu_features):
        geom_type = feature['geometry']['type']
        assert geom_type == 'Polygon', 'Reef features are expected to all be polygons, but found {}'.format(geom_type)
        polygon = shapely.geometry.shape(feature['geometry'])
        if polygon.intersects(uq_reef_bounds):
            asu_polygons.append(polygon)
    asu_reef = shapely.geometry.MultiPolygon(asu_polygons)

    logger.debug('Calculate performance statistics')
    time_start = time.time()
    stats = shared_statistics.calculate_model_performance_statistics(asu_reef, uq_reef)
    logger.debug('Total time:  {}'.format(time.time() - time_start))
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--recalculate', action='store_true')
    args = vars(parser.parse_args())
    calculate_asu_statistics(**args)
