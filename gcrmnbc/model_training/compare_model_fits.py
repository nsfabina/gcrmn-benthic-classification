import argparse
import os

from bfgn.reporting import comparisons

from gcrmnbc.utils import paths


def compare_model_fits(label_experiment: str, response_mapping: str) -> None:
    dir_model_version = paths.get_dir_model_experiment(label_experiment)
    raw_paths_histories = comparisons.walk_directories_for_model_histories([dir_model_version])
    paths_histories = list()
    for path_history in raw_paths_histories:
        path_complete = os.path.join(os.path.dirname(path_history), 'classify.complete')
        is_model_complete = os.path.exists(path_complete)
        is_model_relevant = '/{}_'.format(response_mapping) in path_history
        if not is_model_complete or not is_model_relevant:
            continue
        paths_histories.append(path_history)

    comparisons.create_model_comparison_report(
        filepath_out=os.path.join(dir_model_version, 'comparison_report_{}.pdf'.format(response_mapping)),
        paths_histories=paths_histories
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--label_experiment', type=str, required=True)
    parser.add_argument('--response_mapping', type=str, required=True)
    args = vars(parser.parse_args())
    compare_model_fits(**args)
