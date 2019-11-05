from argparse import ArgumentParser
import joblib
import os
from typing import Tuple

from bfgn.configuration import configs
from bfgn.data_management import data_core
from bfgn.experiments import experiments
import numpy as np
import sklearn.ensemble
import sklearn.metrics
from tqdm import tqdm

from gcrmnbc.application_mvp import submit_application_slurm
from gcrmnbc.utils import encodings_mp, logs, paths, shared_configs


config_name = 'dense_unet_128_64_42_16'
label_experiment = 'millennium_50_aug'
response_mapping = 'custom'


def run_validation(
        config_name: str,
        label_experiment: str,
        response_mapping: str,
        run_all: bool = False
) -> None:
    config = shared_configs.build_dynamic_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
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
        dir_out = paths.get_dir_validate_data_experiment_config(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        logger.debug('Apply model to validation data')
        model_probs, model_targets = _apply_model_to_validation_data(config, dir_out)
        logger.debug('Fit classifiers to model output and validate results')
        _fit_and_validate_classifiers_to_validation_probs_and_targets(
            model_probs=model_probs, model_targets=model_targets, dir_out=dir_out)

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


def _apply_model_to_validation_data(config: configs.Config, dir_out: str) -> Tuple[np.array, np.array]:
    # Prepare filepaths for validation
    filepath_probs_tmp = os.path.join(dir_out, 'probs.npy.tmp')
    filepath_probs = os.path.join(dir_out, 'probs.npy')
    filepath_targets_tmp = os.path.join(dir_out, 'targets.npy.tmp')
    filepath_targets = os.path.join(dir_out, 'targets.npy')
    if not os.path.exists(dir_out):
        os.makedirs(dir_out)
    if os.path.exists(filepath_probs) and os.path.exists(filepath_targets):
        return np.load(filepath_probs, mmap_mode='r'), np.load(filepath_targets, mmap_mode='r')
    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()
    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)
    # Prepare arrays for validation
    buffer = int(config.data_build.window_radius - config.data_build.loss_window_radius)
    validation_shape = list(data_container.validation_sequence.responses[0].shape)
    validation_shape[1] = int(validation_shape[1] - 2 * buffer)
    validation_shape[2] = int(validation_shape[2] - 2 * buffer)
    validation_shape = tuple(validation_shape)
    model_probs = np.memmap(filepath_probs_tmp, dtype=np.float32, mode='w+', shape=validation_shape)
    model_targets = np.memmap(filepath_targets_tmp, dtype=np.float32, mode='w+', shape=validation_shape)
    # Apply to validation data, process in chunks and store results in memmap arrays
    idx_start = 0
    num_batches = data_container.validation_sequence.__len__()
    for idx_batch in tqdm(range(num_batches), desc='Predict validation data'):
        # Get features and responses
        batch = data_container.validation_sequence.__getitem__(idx_batch)
        features = batch[0][0]
        responses = batch[1][0][:, buffer:-buffer, buffer:-buffer, :-1]
        # Predict
        probs = experiment.model.predict_on_batch(features)[:, buffer:-buffer, buffer:-buffer, :]
        # Insert into arrays
        idx_finish = idx_start + features.shape[0]
        model_probs[idx_start:idx_finish, ...] = probs
        model_targets[idx_start:idx_finish, ...] = responses
        idx_start = idx_finish
    # Save memmap arrays
    np.save(filepath_probs, model_probs)
    np.save(filepath_targets, model_targets)
    del model_probs, model_targets
    os.remove(filepath_probs_tmp)
    os.remove(filepath_targets_tmp)
    return np.load(filepath_probs, mmap_mode='r'), np.load(filepath_targets, mmap_mode='r')


def _fit_and_validate_classifiers_to_validation_probs_and_targets(
        model_probs: np.array,
        model_targets: np.array,
        dir_out: str
) -> None:
    _fit_and_validate_fixed_samples_per_class_classifier(
        model_probs=model_probs, model_targets=model_targets, dir_out=dir_out)
    _fit_and_validate_fixed_total_samples_classifier(
        model_probs=model_probs, model_targets=model_targets, dir_out=dir_out)


def _fit_and_validate_fixed_samples_per_class_classifier(
        model_probs: np.array,
        model_targets: np.array,
        dir_out: str
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
        filepath_basename_out=os.path.join(dir_out, 'classifier_sample_by_class')
    )


def _fit_and_validate_fixed_total_samples_classifier(
        model_probs: np.array,
        model_targets: np.array,
        dir_out: str
) -> None:
    # Get training indices
    num_samples = np.prod(model_probs.shape[:-1])
    num_drawn = 200000
    idx_train = np.random.choice(a=num_samples, size=num_drawn, replace=False)
    # Fit and validate
    _fit_and_validate_classifier(
        model_probs=model_probs, model_targets=model_targets, idx_train=idx_train,
        filepath_basename_out=os.path.join(dir_out, 'classifier_total_samples')
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
    num_samples = np.prod(model_probs.shape[:-1])
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
