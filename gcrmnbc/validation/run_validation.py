from argparse import ArgumentParser
import joblib
import os

import numpy as np
import sklearn.ensemble
import sklearn.metrics

from gcrmnbc.application_mvp import submit_application_slurm
from gcrmnbc.utils import encodings_mp, logs, paths


def run_validation(
        config_name: str,
        label_experiment: str,
        response_mapping: str,
        run_all: bool = False
) -> None:
    logger = logs.get_model_logger(
        logger_name='log_run_classification', config_name=config_name, label_experiment=label_experiment,
        response_mapping=response_mapping,
    )

    # Exit early if validation already finished
    filepath_complete = paths.get_filepath_validation_complete(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    if os.path.exists(filepath_complete):
        return

    # Exit early if classification in progress
    filepath_lock = paths.get_filepath_validation_lock(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        return

    try:
        filepath_probs = paths.get_filepath_applied_validation_probs(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        model_probs = np.load(filepath_probs, mmap_mode='r')
        filepath_targets = paths.get_filepath_applied_validation_targets(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        model_targets = np.load(filepath_targets, mmap_mode='r')
        _fit_and_validate_fixed_samples_per_class_classifier(model_probs=model_probs, model_targets=model_targets)
        _fit_and_validate_fixed_total_samples_classifier(model_probs=model_probs, model_targets=model_targets)

        # Create complete file to avoid rerunning in the future
        open(filepath_complete, 'w')

        # Start application if necessary
        if run_all:
            submit_application_slurm.submit_application_slurm(
                labels_experiments=label_experiment, response_mappings=response_mapping, num_jobs=1,
                config_names=config_name, run_all=run_all
            )
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)


def _fit_and_validate_fixed_samples_per_class_classifier(
        model_probs: np.array,
        model_targets: np.array
) -> None:
    # Get training indices
    num_classes = model_targets.shape[-1]
    num_drawn_per_class = 5000
    model_argmax = np.argmax(model_targets, axis=-1)
    idx_train = list()
    for idx_class in range(num_classes):
        idx_found = np.where(model_argmax.ravel() == idx_class)[0]
        idx_train.extend(np.random.choice(idx_found, min(num_drawn_per_class, len(idx_found)), replace=False))
    idx_train = np.array(idx_train)
    # Fit and validate
    _fit_and_validate_classifier(
        model_probs=model_probs, model_targets=model_targets, idx_train=idx_train,
        filepath_basename_out=os.path.join(os.path.dirname(model_probs), '_classifier_sample_by_class')
    )


def _fit_and_validate_fixed_total_samples_classifier(
        model_probs: np.array,
        model_targets: np.array
) -> None:
    # Get training indices
    num_samples = np.prod(model_probs.shape[:-1])
    num_drawn = 200000
    idx_train = np.random.choice(a=num_samples, size=num_drawn, replace=False)
    # Fit and validate
    _fit_and_validate_classifier(
        model_probs=model_probs, model_targets=model_targets, idx_train=idx_train,
        filepath_basename_out=os.path.join(os.path.dirname(model_probs), '_classifier_total_samples')
    )


def _fit_and_validate_classifier(
        model_probs: np.array,
        model_targets: np.array,
        idx_train: np.array,
        filepath_basename_out: str
) -> None:
    # Create model framework
    forest = sklearn.ensemble.RandomForestClassifier(
        n_estimators=200, criterion='gini', max_depth=40, min_samples_split=2, min_samples_leaf=1, max_features='sqrt',
        bootstrap=True, class_weight='balanced_subsample'
    )
    # Get reef class indices
    idx_reef_classes = list()
    mappings = sorted(encodings_mp.MAPPINGS_OUTPUT.items(), key=lambda x: x[0], reverse=False)
    for idx_class, (code_class, code_mapping) in enumerate(mappings):
        if code_mapping != encodings_mp.OUTPUT_CODE_REEF:
            continue
        idx_reef_classes.append(idx_class)
    # Fit model
    num_classes = model_probs.shape[-1]
    x = model_probs.reshape(-1, num_classes)[idx_train, ...]
    y = np.any(model_targets.reshape(-1, num_classes)[:, idx_reef_classes], axis=-1)[idx_train, ...]
    forest.fit(x, y)
    # Validate model and calculate performance
    num_samples = int(np.prod(model_probs.shape[:-1]))
    idx_test = np.array(list(set(np.arange(num_samples)).difference(idx_train)))
    x = model_probs.reshape(-1, num_classes)[idx_test, ...]
    test_predictions = forest.predict(x.copy())
    test_targets = np.any(model_targets.reshape(-1, num_classes)[:, idx_reef_classes], axis=-1)[idx_test, ...]
    report = sklearn.metrics.classification_report(test_targets, test_predictions)
    # Save model and results
    joblib.dump(forest, filepath_basename_out + '_model.joblib')
    with open(filepath_basename_out + '_report.txt', 'w') as file_:
        file_.write(report)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    run_validation(**args)
