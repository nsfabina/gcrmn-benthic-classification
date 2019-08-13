import matplotlib.pyplot as plt
import re


def generate_pdf_summary_report(statistics: dict, label: str, filepath_out: str) -> None:
    lines = ['{} Reef Performance Summary'.format(label), '', '']

    for reef, stats in sorted(statistics.items()):
        reef_name = re.sub('_', ' ', reef).title()
        # Calculate precision and recall
        denominator = stats['pct_tp'] + stats['pct_fp']
        if denominator:
            precision = stats['pct_tp'] / denominator
        else:
            precision = None
        denominator = stats['pct_tp'] + stats['pct_fn']
        if denominator:
            recall = stats['pct_tp'] / denominator
        else:
            recall = None

        lines.append('------------------------------------------------------------------------------------------------')
        lines.append('')
        lines.append(reef_name)
        lines.append('')
        if recall:
            lines.append('  Recall:             {:8.1f} %  of actual reef area is detected by model'.format(100*recall))
        else:
            lines.append('  Recall:                     N/A')
        if precision:
            lines.append('  Precision:          {:8.1f} %  of model detections are actually reef'.format(100*precision))
        else:
            lines.append('  Precision:                  N/A')
        lines.append('')
        lines.append('  Total area:         {:8.1f} km2  in convex hull around ACA reef'.format(stats['total_area']))
        lines.append('')
        lines.append('  ACA reef:           {:8.1f} km2 | {:4.1f} %  of total area'.format(
            stats['groundtruth_reef_area'], 100*stats['groundtruth_reef_pct']))
        lines.append('  {} reef:          {}{:8.1f} km2 | {:4.1f} %  of total area'.format(
            label, ' ' if len(label) == 3 else '', stats['model_reef_area'], 100*stats['model_reef_pct']))
        lines.append('')
        lines.append('  Reef detections')
        lines.append('  True positives:     {:8.1f} km2 | {:4.1f} %  of reef area'.format(
            stats['area_tp'], 100*stats['area_tp']/stats['groundtruth_reef_area']))
        lines.append('  False positives:    {:8.1f} km2 | {:4.1f} %  of non-reef area'.format(
            stats['area_fp'], 100*stats['area_fp']/stats['groundtruth_nonreef_area']))
        lines.append('')
        lines.append('  ACA non-reef:       {:8.1f} km2 | {:4.1f} %  of total area'.format(
            stats['groundtruth_nonreef_area'], 100*stats['groundtruth_nonreef_pct']))
        lines.append('  {} non-reef:      {}{:8.1f} km2 | {:4.1f} %  of total area'.format(
            label, ' ' if len(label) == 3 else '', stats['model_nonreef_area'], 100*stats['model_nonreef_pct']))
        lines.append('')
        lines.append('  Non-reef detections')
        lines.append('  True negatives:     {:8.1f} km2 | {:4.1f} % of non-reef area'.format(
            stats['area_tn'], 100*stats['area_tn']/stats['groundtruth_nonreef_area']))
        lines.append('  False negatives:    {:8.1f} km2 | {:4.1f} % of reef area'.format(
            stats['area_fn'], 100*stats['area_fn']/stats['groundtruth_reef_area']))
        lines.append('')
        lines.append('')

    fig, ax = plt.subplots(figsize=(8.5, 2 + 3.25 * len(statistics)))
    ax.text(0, 0, '\n'.join(lines), **{'fontsize': 8, 'fontfamily': 'monospace'})
    ax.axis('off')
    plt.savefig(filepath_out)
