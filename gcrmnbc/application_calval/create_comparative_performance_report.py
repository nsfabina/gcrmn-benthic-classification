import argparse
import json
import os
import re
from typing import Union

import matplotlib.pyplot as plt
import numpy as np

from gcrmnbc.utils import logs


_logger = logs.get_logger(__file__)


_FILEPATH_UNEP_STATS = 'unep_statistics.json'
_DIR_ASU = '/scratch/nfabina/gcrmn-benthic-classification/applied_data'
_FILEPATH_ASU_STATS = os.path.join(_DIR_ASU, '{}/{}/asu_statistics.json')
_FILEPATH_FIG_OUT = 'comparative_report_{}.pdf'


def create_comparative_performance_report(response_mapping: str) -> None:
    _logger.debug('Load UNEP statistics')
    with open(_FILEPATH_UNEP_STATS) as file_:
        unep_statistics = json.load(file_)

    _logger.debug('Load ASU statistics')
    asu_statistics = dict()
    for config_name in os.listdir(_DIR_ASU):
        filepath_model_stats = _FILEPATH_ASU_STATS.format(config_name, response_mapping)
        if not os.path.exists(filepath_model_stats):
            continue
        with open(filepath_model_stats) as file_:
            asu_statistics[config_name] = json.load(file_)
    asu_statistics = sorted(asu_statistics.items())

    _logger.debug('Create report')
    lines = list(['Comparative Reef Performance Report', '{} reef mappings'.format(response_mapping), '', ''])

    # Calculate and print overall performance
    lines.append('------------------------------------------------------------------------------------------------')
    lines.append('')
    lines.append('  Performance Summary')
    lines.append('')
    lines.append('      Mean Recall:  actual reef area which is detected by the model')
    lines.append('')
    lines.append('          {:<24}{}'.format('UNEP:', _get_recall_average_str(unep_statistics)))
    for config_name, stats in asu_statistics:
        lines.append('          {:<24}{}'.format(config_name+':', _get_recall_average_str(stats)))
    lines.append('')

    lines.append('      Mean Precision:  model detections which are actually reef')
    lines.append('')
    lines.append('          {:<24}{}'.format('UNEP:', _get_precision_average_str(unep_statistics)))
    for config_name, stats in asu_statistics:
        lines.append('          {:<24}{}'.format(config_name+':', _get_precision_average_str(stats)))
    lines.append('')
    lines.append('')

    # Create sections for each reef
    for reef, unep_stats in sorted(unep_statistics.items()):
        asu_reef_stats = [(config_name, stats.get(reef)) for config_name, stats in asu_statistics if stats.get(reef)]
        reef_name = re.sub('_', ' ', reef).title()

        # Header
        lines.append('------------------------------------------------------------------------------------------------')
        lines.append('')
        lines.append(reef_name)
        lines.append('')
        lines.append('')

        # Recall and precision
        lines.append('  Recall:  actual reef area which is detected by the model')
        lines.append('')
        lines.append('      {:<24}{}'.format('UNEP:', _get_recall_str(unep_stats)))
        for config_name, stats in asu_reef_stats:
            lines.append('      {:<24}{}'.format(config_name+':', _get_recall_str(stats)))
        lines.append('')

        lines.append('  Precision:  model detections which are actually reef')
        lines.append('')
        lines.append('      {:<24}{}'.format('UNEP:', _get_precision_str(unep_stats)))
        for config_name, stats in asu_reef_stats:
            lines.append('      {:<24}{}'.format(config_name+':', _get_precision_str(stats)))
        lines.append('')
        lines.append('')

        # Total area
        lines.append('  Total area:            {:8.1f} km2  in convex hull around ACA reef'.format(
            unep_stats['total_area']))
        lines.append('')
        lines.append('')

        # Reef area and detections
        lines.append('  Reef area')
        lines.append('')
        lines.append('      {:<24}{:8.1f} km2 | {:4.1f} %  of total area'.format(
            'ACA:', unep_stats['groundtruth_reef_area'], 100*unep_stats['groundtruth_reef_pct']))
        lines.append('      {:<24}{:8.1f} km2 | {:4.1f} %  of total area'.format(
            'UNEP:', unep_stats['model_reef_area'], 100*unep_stats['model_reef_pct']))
        for config_name, stats in asu_reef_stats:
            lines.append('      {:<24}{:8.1f} km2 | {:4.1f} %  of total area'.format(
                config_name+':', stats['model_reef_area'], 100*stats['model_reef_pct']))
        lines.append('')

        lines.append('  Reef detections')
        lines.append('')
        lines.append('      True positives')
        lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            'UNEP:', unep_stats['area_tp'], 100*unep_stats['area_tp']/unep_stats['groundtruth_reef_area']))
        for config_name, stats in asu_reef_stats:
            lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name+':', stats['area_tp'], 100*stats['area_tp']/stats['groundtruth_reef_area']))
        lines.append('')

        lines.append('      False positives')
        lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of non-reef area'.format(
            'UNEP:', unep_stats['area_fp'], 100*unep_stats['area_fp']/unep_stats['groundtruth_nonreef_area']))
        for config_name, stats in asu_reef_stats:
            lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of non-reef area'.format(
                config_name+':', stats['area_fp'], 100*stats['area_fp']/stats['groundtruth_nonreef_area']))
        lines.append('')
        lines.append('')

        # Non-reef area and detections
        lines.append('  Non-reef area')
        lines.append('')
        lines.append('      {:<24}{:8.1f} km2 | {:4.1f} %  of total area'.format(
            'ACA:', unep_stats['groundtruth_nonreef_area'], 100*unep_stats['groundtruth_nonreef_pct']))
        lines.append('      {:<24}{:8.1f} km2 | {:4.1f} %  of total area'.format(
            'UNEP:', unep_stats['model_nonreef_area'], 100*unep_stats['model_nonreef_pct']))
        for config_name, stats in asu_reef_stats:
            lines.append('      {:<24}{:8.1f} km2 | {:4.1f} %  of total area'.format(
                config_name+':', stats['model_nonreef_area'], 100*stats['model_nonreef_pct']))
        lines.append('')

        lines.append('  Non-reef detections')
        lines.append('')
        lines.append('      True negatives')
        lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            'UNEP:', unep_stats['area_tn'], 100*unep_stats['area_tn']/unep_stats['groundtruth_nonreef_area']))
        for config_name, stats in asu_reef_stats:
            lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name+':', stats['area_tn'], 100*stats['area_tn']/stats['groundtruth_nonreef_area']))
        lines.append('')

        lines.append('      False negatives')
        lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            'UNEP:', unep_stats['area_fn'], 100*unep_stats['area_fn']/unep_stats['groundtruth_reef_area']))
        for config_name, stats in asu_reef_stats:
            lines.append('          {:<24}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name+':', stats['area_fn'], 100*stats['area_fn']/stats['groundtruth_reef_area']))
        lines.append('')
        lines.append('')

    # Finalize figure and save
    height_per_line = 0.145
    fig, ax = plt.subplots(figsize=(8.5, 2.0 + height_per_line * len(lines)))
    ax.text(0, 0, '\n'.join(lines), **{'fontsize': 8, 'fontfamily': 'monospace'})
    ax.axis('off')
    plt.savefig(_FILEPATH_FIG_OUT.format(response_mapping))


def _get_precision_str(reef_statistics: dict) -> str:
    if reef_statistics is None:
        return '        Not calculated'
    precision = _calculate_precision(reef_statistics)
    if precision:
        precision_str = '{:8.1f} %'.format(precision)
    else:
        precision_str = '        NA'
    return precision_str


def _get_recall_str(reef_statistics: dict) -> str:
    if reef_statistics is None:
        return '        Not calculated'
    recall = _calculate_recall(reef_statistics)
    if recall:
        recall_str = '{:8.1f} %'.format(recall)
    else:
        recall_str = '        NA'
    return recall_str


def _get_precision_average_str(model_statistics: dict) -> str:
    precisions = list()
    weights = list()
    for reef_statistics in model_statistics.values():
        precision = _calculate_precision(reef_statistics)
        if precision is None:
            continue
        precisions.append(precision)
        weights.append(reef_statistics['groundtruth_reef_area'])
    unweighted = np.mean(precisions)
    weighted = np.average(precisions, weights=weights)
    return '{:4.1f} %  |  {:4.1f} %  weighted by area'.format(unweighted, weighted)


def _get_recall_average_str(model_statistics: dict) -> str:
    recalls = list()
    weights = list()
    for reef_statistics in model_statistics.values():
        recall = _calculate_recall(reef_statistics)
        if recall is None:
            continue
        recalls.append(recall)
        weights.append(reef_statistics['groundtruth_reef_area'])
    unweighted = np.mean(recalls)
    weighted = np.average(recalls, weights=weights)
    return '{:4.1f} %  |  {:4.1f} %  weighted by area'.format(unweighted, weighted)


def _calculate_precision(reef_statistics: dict) -> Union[float, None]:
    if reef_statistics is None:
        return None
    denominator = reef_statistics['pct_tp'] + reef_statistics['pct_fp']
    if denominator:
        precision = 100 * reef_statistics['pct_tp'] / denominator
    else:
        precision = None
    return precision


def _calculate_recall(reef_statistics: dict) -> Union[float, None]:
    if reef_statistics is None:
        return None
    denominator = reef_statistics['pct_tp'] + reef_statistics['pct_fn']
    if denominator:
        recall = 100 * reef_statistics['pct_tp'] / denominator
    else:
        recall = None
    return recall


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--response_mapping', type=str, required=True)
    args = parser.parse_args()
    create_comparative_performance_report(args.response_mapping)
