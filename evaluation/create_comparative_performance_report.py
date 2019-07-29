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
        reef_name = re.sub('_', ' ', reef).title()

        lines.append('------------------------------------------------------------------------------------------------')
        lines.append('')
        lines.append(reef_name)
        lines.append('')
        lines.append('  Recall:  reef area which is detected correctly')
        lines.append('    UNEP:               {:8.1f} %'.format(100*unep_stats['recall']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} %'.format(config_name, 100*stats['recall']))
        lines.append('')

        lines.append('  Precision:  reef detections which are correct')
        lines.append('    UNEP:               {:8.1f} %'.format(100*unep_stats['precision']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} %'.format(config_name, 100*stats['precision']))
        lines.append('')

        lines.append('  Total area:         {:8.1f} km2  in convex hull around ACA reef'.format(
            unep_stats['total_area']))
        lines.append('')

        lines.append('Reef area')
        lines.append('  ACA:                {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['uq_reef_area'], 100*unep_stats['uq_reef_pct']))
        lines.append('')

        lines.append('  UNEP:          {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['unep_reef_area'], 100*unep_stats['unep_reef_pct']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} %'.format(config_name, 100*stats['asu_reef_pct']))
        lines.append('')

        lines.append('Reef detections')
        lines.append('  True positives')
        lines.append('    UNEP:         {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_tp'], 100*unep_stats['area_tp']/unep_stats['uq_reef_area']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name, stats['area_tp'], 100*stats['area_tp']/stats['uq_reef_area']))
        lines.append('')

        lines.append('  False positives')
        lines.append('    UNEP:         {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_fp'], 100*unep_stats['area_fp']/unep_stats['uq_reef_area']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name, stats['area_fp'], 100*stats['area_fp']/stats['uq_reef_area']))
        lines.append('')

        lines.append('Non-reef area')
        lines.append('  ACA:                {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['uq_nonreef_area'], 100*unep_stats['uq_nonreef_pct']))
        lines.append('')

        lines.append('  UNEP:          {:8.1f} km2 | {:4.1f} %  of total area'.format(
            unep_stats['unep_nonreef_area'], 100*unep_stats['unep_nonreef_pct']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} %'.format(config_name, 100*stats['asu_nonreef_pct']))
        lines.append('')

        lines.append('Non-reef detections')
        lines.append('  True negatives')
        lines.append('    UNEP:         {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_tn'], 100*unep_stats['area_tn']/unep_stats['uq_reef_area']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name, stats['area_tn'], 100*stats['area_tn']/stats['uq_reef_area']))
        lines.append('')

        lines.append('  False negatives')
        lines.append('    UNEP:         {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            unep_stats['area_fn'], 100*unep_stats['area_fn']/unep_stats['uq_reef_area']))
        for config_name, stats in asu_statistics:
            lines.append('    {:<20.s}:{:8.1f} km2 | {:4.1f} %  of reef area'.format(
                config_name, stats['area_fn'], 100*stats['area_fn']/stats['uq_reef_area']))
        lines.append('')

        lines.append('  Non-reef detections')
        lines.append('  True negatives:     {:8.1f} km2 | {:4.1f} % of non-reef area'.format(
            unep_stats['area_tn'], 100*unep_stats['area_tn']/unep_stats['uq_nonreef_area']))
        lines.append('  False negatives:    {:8.1f} km2 | {:4.1f} % of non-reef area'.format(
            unep_stats['area_fn'], 100*unep_stats['area_fn']/unep_stats['uq_nonreef_area']))
        lines.append('')
        lines.append('')

    num_reefs = len(unep_statistics)
    num_configs = len(asu_statistics)
    fig, ax = plt.subplots(figsize=(8.5, 2 + 3.25 * num_reefs * num_configs))
    ax.text(0, 0, '\n'.join(lines), **{'fontsize': 8, 'fontfamily': 'monospace'})
    ax.axis('off')
    plt.savefig(_FILEPATH_FIG_OUT)
