import json
import logging
import os
import re
import sys

import matplotlib.pyplot as plt


_logger = logging.getLogger(__name__)
_logger.setLevel('DEBUG')
_formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)


_FILEPATH_UNEP_STATS = 'unep_statistics.json'
_DIR_ASU = '/scratch/nfabina/gcrmn-benthic-classification/training_data_applied'
_FILEPATH_ASU_STATS = os.path.join(_DIR_ASU, '{}/lwr/asu_statistics.json')
_FILEPATH_FIG_OUT = 'comparative_report.pdf'


def create_comparative_performance_report() -> None:
    _logger.debug('Load UNEP statistics')
    with open(_FILEPATH_UNEP_STATS) as file_:
        unep_statistics = json.load(file_)

    _logger.debug('Load ASU statistics')
    asu_statistics = dict()
    for config_name in os.listdir(_DIR_ASU):
        with open(_FILEPATH_ASU_STATS.format(config_name)) as file_:
            asu_statistics[config_name] = json.load(file_)
    asu_statistics = sorted(asu_statistics.items())

    _logger.debug('Create report')
    lines = ['Reef Performance Comparisons', '', '']

    for reef, unep_stats in sorted(unep_statistics.items()):
        asu_reef_stats = [(config_name, stats[reef]) for config_name, stats in asu_statistics]
        reef_name = re.sub('_', ' ', reef).title()

        lines.append('------------------------------------------------------------------------------------------------')
        lines.append('')
        lines.append(reef_name)
        lines.append('')
        lines.append('')

        lines.append('  Recall:  actual reef area which is detected by the model')
        lines.append('')
        lines.append('      UNEP:               {}'.format(_get_recall_str(unep_stats)))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('      {:<20}{}'.format(config_name + ':', _get_recall_str(reef_stats)))
        lines.append('')

        lines.append('  Precision:  model detections which are actually reef')
        lines.append('')
        lines.append('      UNEP:               {}'.format(_get_precision_str(unep_stats)))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('      {:<20}{}'.format(config_name + ':', _get_precision_str(reef_stats)))
        lines.append('')
        lines.append('')

        lines.append('  Total area:            {:8.1f} km2  in convex hull around ACA reef'.format(
            unep_stats['total_area']))
        lines.append('')
        lines.append('')

        lines.append('  Reef area')
        lines.append('      ACA:                {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['groundtruth_reef_area'], 100*unep_stats['groundtruth_reef_pct']))
        lines.append('      UNEP:               {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['model_reef_area'], 100*unep_stats['model_reef_pct']))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('      {:<20}{:8.1f} km2 | {:4.1f} %  of total area'.format(
                config_name + ':', reef_stats['model_reef_area'], 100*reef_stats['model_reef_pct']))
        lines.append('')

        lines.append('  Reef detections')
        lines.append('      True positives')
        lines.append('          UNEP:               {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_tp'], 100*unep_stats['area_tp']/unep_stats['groundtruth_reef_area']))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('          {:<20}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name + ':', reef_stats['area_tp'], 100*reef_stats['area_tp']/reef_stats['groundtruth_reef_area']))
        lines.append('')

        lines.append('      False positives')
        lines.append('          UNEP:               {:8.1f} km2 | {:4.1f} %  of non-reef area'.format(
            unep_stats['area_fp'], 100*unep_stats['area_fp']/unep_stats['groundtruth_nonreef_area']))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('          {:<20}{:8.1f} km2 | {:4.1f} %  of non-reef area'.format(
                config_name + ':', reef_stats['area_fp'], 100*reef_stats['area_fp']/reef_stats['groundtruth_nonreef_area']))
        lines.append('')
        lines.append('')

        lines.append('  Non-reef area')
        lines.append('      ACA:                {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['groundtruth_nonreef_area'], 100*unep_stats['groundtruth_nonreef_pct']))
        lines.append('      UNEP:               {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['model_nonreef_area'], 100*unep_stats['model_nonreef_pct']))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('      {:<20}{:8.1f} km2 | {:4.1f} %  of total area'.format(
                config_name + ':', reef_stats['model_nonreef_area'], 100*reef_stats['model_nonreef_pct']))
        lines.append('')

        lines.append('  Non-reef detections')
        lines.append('      True negatives')
        lines.append('          UNEP:               {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_tn'], 100*unep_stats['area_tn']/unep_stats['groundtruth_nonreef_area']))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('          {:<20}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name + ':', reef_stats['area_tn'], 100*reef_stats['area_tn']/reef_stats['groundtruth_nonreef_area']))
        lines.append('')

        lines.append('      False negatives')
        lines.append('          UNEP:               {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_fn'], 100*unep_stats['area_fn']/unep_stats['groundtruth_reef_area']))
        for config_name, reef_stats in asu_reef_stats:
            lines.append('          {:<20}{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name + ':', reef_stats['area_fn'], 100*reef_stats['area_fn']/reef_stats['groundtruth_reef_area']))
        lines.append('')
        lines.append('')

    height_per_line = 0.145
    fig, ax = plt.subplots(figsize=(8.5, 2.0 + height_per_line * len(lines)))
    ax.text(0, 0, '\n'.join(lines), **{'fontsize': 8, 'fontfamily': 'monospace'})
    ax.axis('off')
    plt.savefig(_FILEPATH_FIG_OUT)


def _get_precision_str(statistics: dict) -> str:
    denominator = statistics['pct_tp'] + statistics['pct_fp']
    if denominator:
        precision = 100 * statistics['pct_tp'] / denominator
        precision_str = '{:8.1f} %'.format(precision)
    else:
        precision_str = '        NA'
    return precision_str


def _get_recall_str(statistics: dict) -> str:
    denominator = statistics['pct_tp'] + statistics['pct_fn']
    if denominator:
        recall = 100 * statistics['pct_tp'] / denominator
        recall_str = '{:8.1f} %'.format(recall)
    else:
        recall_str = '        NA'
    return recall_str

 
if __name__ == '__main__':
    create_comparative_performance_report()

