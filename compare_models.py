import os

from bfgn.reporting import comparisons


_DIR_MODELS = 'models'
_RESPONSE_MAPPING = 'lwr'


def compare_models() -> None:
    paths_histories_started = comparisons.walk_directories_for_model_histories([_DIR_MODELS])
    paths_histories_complete = list()
    for path_history in paths_histories_started:
        if _RESPONSE_MAPPING not in path_history:
            continue
        path_complete = os.path.join(os.path.dirname(path_history), 'classify.complete')
        if os.path.exists(path_complete):
            paths_histories_complete.append(path_history)

    comparisons.create_model_comparison_report(
        filepath_out=os.path.join(_DIR_MODELS, 'comparison_report_{}.pdf'.format(_RESPONSE_MAPPING)),
        paths_histories=paths_histories_complete
    )


if __name__ == '__main__':
    compare_models()
