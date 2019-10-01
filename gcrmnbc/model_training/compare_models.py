import argparse
import os

from bfgn.reporting import comparisons


_DIR_MODELS = '../models'


def compare_models(response_mapping: str) -> None:
    paths_histories_started = comparisons.walk_directories_for_model_histories([_DIR_MODELS])
    paths_histories_complete = list()
    for path_history in paths_histories_started:
        regex_response = '/lwr/'
        path_complete = os.path.join(os.path.dirname(path_history), 'classify.complete')
        if regex_response not in path_history or not os.path.exists(path_complete):
            continue
        paths_histories_complete.append(path_history)

    comparisons.create_model_comparison_report(
        filepath_out='comparison_report_{}.pdf'.format(response_mapping),
        paths_histories=paths_histories_complete
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--response_mapping', type=str, required=True)
    args = parser.parse_args()
    compare_models(args.response_mapping)
