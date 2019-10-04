import argparse
import json
import os
import re
from typing import Callable, List, Tuple, Union

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import numpy as np

from gcrmnbc.utils import logs, paths


_logger = logs.get_logger(__file__)


_FILEPATH_UNEP_STATS = 'unep_statistics.json'

_FILENAME_FIG_OUT = 'comparative_report_{}_{}.pdf'


def create_comparative_performance_report(label_experiment: str, response_mapping: str) -> None:
    _logger.debug('Load UNEP statistics')
    with open(_FILEPATH_UNEP_STATS) as file_:
        unep_statistics = json.load(file_)

    _logger.debug('Load ASU statistics')
    asu_statistics = dict()
    dir_experiment = paths.get_dir_calval_data_experiment(label_experiment, response_mapping)
    for dir_config in os.listdir(dir_experiment):
        filepath_model_stats = os.path.join(dir_experiment, dir_config, paths.FILENAME_CALVAL_STATS)
        if not os.path.exists(filepath_model_stats):
            continue
        with open(filepath_model_stats) as file_:
            asu_statistics[dir_config] = json.load(file_)
    asu_statistics = _sort_models_by_average_fscore(asu_statistics)

    _logger.debug('Create report')
    lines = list(['Comparative Reef Performance Report', '{} reef mappings'.format(response_mapping), '', ''])

    # Calculate and print overall performance
    lines.append('')
    lines.append('  Performance Summary')
    lines.append('')
    lines.append('      Mean F-score')
    lines.append('')
    lines.append('          {:<50}{:>30}'.format('UNEP:', _get_fscore_average_str(unep_statistics)))
    for config_name, stats in asu_statistics:
        lines.append('          {:<50}{:>30}'.format(config_name+':', _get_fscore_average_str(stats)))
    lines.append('')

    lines.append('      Mean Recall:  actual reef area which is detected by the model')
    lines.append('')
    lines.append('          {:<50}{:>30}'.format('UNEP:', _get_recall_average_str(unep_statistics)))
    for config_name, stats in asu_statistics:
        lines.append('          {:<50}{:>30}'.format(config_name+':', _get_recall_average_str(stats)))
    lines.append('')

    lines.append('      Mean Precision:  model detections which are actually reef')
    lines.append('')
    lines.append('          {:<50}{:>30}'.format('UNEP:', _get_precision_average_str(unep_statistics)))
    for config_name, stats in asu_statistics:
        lines.append('          {:<50}{:>30}'.format(config_name+':', _get_precision_average_str(stats)))
    pages = list([lines])

    # Create sections for each reef
    for reef, unep_stats in sorted(unep_statistics.items()):
        lines = list()
        asu_reef_stats = [(config_name, stats.get(reef)) for config_name, stats in asu_statistics if stats.get(reef)]
        reef_name = re.sub('_', ' ', reef).title()

        # Header
        lines.append(reef_name)
        lines.append('')
        lines.append('')

        # Recall and precision
        lines.append('  Recall:  actual reef area which is detected by the model')
        lines.append('')
        lines.append('      {:<50}{:>30}'.format('UNEP:', _get_recall_str(unep_stats)))
        for config_name, stats in asu_reef_stats:
            lines.append('      {:<50}{:>30}'.format(config_name+':', _get_recall_str(stats)))
        lines.append('')

        lines.append('  Precision:  model detections which are actually reef')
        lines.append('')
        lines.append('      {:<50}{:>30}'.format('UNEP:', _get_precision_str(unep_stats)))
        for config_name, stats in asu_reef_stats:
            lines.append('      {:<50}{:>30}'.format(config_name+':', _get_precision_str(stats)))
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
        string = '{:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['groundtruth_reef_area'], 100*unep_stats['groundtruth_reef_pct'])
        lines.append('      {:<50}{:>30}'.format('ACA:', string))
        string = '{:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['model_reef_area'], 100*unep_stats['model_reef_pct'])
        lines.append('      {:<50}{:>30}'.format('UNEP:', string))
        for config_name, stats in asu_reef_stats:
            string = '{:8.1f} km2 | {:4.1f} %  of total area'.format(
                stats['model_reef_area'], 100*stats['model_reef_pct'])
            lines.append('      {:<50}{:>30}'.format(config_name+':', string))
        lines.append('')

        lines.append('  Reef detections')
        lines.append('')
        lines.append('      True positives')
        string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_tp'], 100*unep_stats['area_tp']/unep_stats['groundtruth_reef_area'])
        lines.append('          {:<50}{:>30}'.format('UNEP:', string))
        for config_name, stats in asu_reef_stats:
            string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                stats['area_tp'], 100*stats['area_tp']/stats['groundtruth_reef_area'])
            lines.append('          {:<50}{:>30}'.format(config_name+':', string))
        lines.append('')

        lines.append('      False positives')
        string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_fp'], 100*unep_stats['area_fp']/unep_stats['groundtruth_nonreef_area'])
        lines.append('          {:<50}{:>30}'.format('UNEP:', string))
        for config_name, stats in asu_reef_stats:
            string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                stats['area_fp'], 100*stats['area_fp']/stats['groundtruth_nonreef_area'])
            lines.append('          {:<50}{:>30}'.format(config_name+':', string))
        lines.append('')
        lines.append('')

        # Non-reef area and detections
        lines.append('  Non-reef area')
        lines.append('')
        string = '{:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['groundtruth_nonreef_area'], 100*unep_stats['groundtruth_nonreef_pct'])
        lines.append('      {:<50}{:>30}'.format('ACA:', string))
        string = '{:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['model_nonreef_area'], 100*unep_stats['model_nonreef_pct'])
        lines.append('      {:<50}{:>30}'.format('UNEP:', string))
        for config_name, stats in asu_reef_stats:
            string = '{:8.1f} km2 | {:4.1f} %  of total area'.format(
                stats['model_nonreef_area'], 100*stats['model_nonreef_pct'])
            lines.append('      {:<50}{:>30}'.format(config_name+':', string))
        lines.append('')

        lines.append('  Non-reef detections')
        lines.append('')
        lines.append('      True negatives')
        string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_tn'], 100*unep_stats['area_tn']/unep_stats['groundtruth_nonreef_area'])
        lines.append('          {:<50}{:>30}'.format('UNEP:', string))
        for config_name, stats in asu_reef_stats:
            string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                stats['area_tn'], 100*stats['area_tn']/stats['groundtruth_nonreef_area'])
            lines.append('          {:<50}{:>30}'.format(config_name+':', string))
        lines.append('')

        lines.append('      False negatives')
        string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_fn'], 100*unep_stats['area_fn']/unep_stats['groundtruth_reef_area'])
        lines.append('          {:<50}{:>30}'.format('UNEP:', string))
        for config_name, stats in asu_reef_stats:
            string = '{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                stats['area_fn'], 100*stats['area_fn']/stats['groundtruth_reef_area'])
            lines.append('          {:<50}{:>30}'.format(config_name+':', string))
        lines.append('')
        lines.append('')

    # Finalize figure and save
    filename_out = os.path.join(dir_experiment, _FILENAME_FIG_OUT.format(label_experiment, response_mapping))
    with PdfPages(filename_out) as pdf:
        height_per_line = 0.145
        for page in pages:
            fig, ax = plt.subplots(figsize=(8.5, 2.0 + height_per_line * len(page)))
            ax.text(0, 0, '\n'.join(lines), **{'fontsize': 8, 'fontfamily': 'monospace'})
            ax.axis('off')
            pdf.savefig(fig)


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


def _get_fscore_average_str(model_statistics: dict) -> str:
    return _get_stat_average_str(model_statistics, _calculate_fscore)


def _get_precision_average_str(model_statistics: dict) -> str:
    return _get_stat_average_str(model_statistics, _calculate_precision)


def _get_recall_average_str(model_statistics: dict) -> str:
    return _get_stat_average_str(model_statistics, _calculate_recall)


def _get_stat_average_str(model_statistics: dict, calculator: Callable) -> str:
    values = list()
    weights = list()
    for reef_statistics in model_statistics.values():
        value = calculator(reef_statistics)
        if value is None:
            continue
        values.append(value)
        weights.append(reef_statistics['groundtruth_reef_area'])
    unweighted = np.mean(values)
    weighted = np.average(values, weights=weights)
    return '{:4.1f} %  |  {:4.1f} %  by area'.format(unweighted, weighted)


def _sort_models_by_average_fscore(all_statistics: dict) -> List[Tuple[str, dict]]:
    fscores = dict()
    for model_name, model_stats in all_statistics.items():
        values = list()
        weights = list()
        for reef_statistics in model_stats.values():
            values.append(_calculate_fscore(reef_statistics))
            weights.append(reef_statistics['groundtruth_reef_area'])
        if any([v is None for v in values]):
            continue
        fscores[model_name] = np.average(values, weights=weights)
    names_sorted = [name for name, score in sorted(fscores.items(), key=lambda x: x[1])]
    return [(model_name, all_statistics[model_name]) for model_name in names_sorted]


def _calculate_fscore(reef_statistics: dict) -> Union[float, None]:
    precision = _calculate_precision(reef_statistics)
    recall = _calculate_recall(reef_statistics)
    if precision is None or recall is None:
        return None
    return 2 * precision * recall / (precision + recall)


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
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    args = vars(parser.parse_args())
    create_comparative_performance_report(**args)
