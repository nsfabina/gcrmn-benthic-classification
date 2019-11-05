from argparse import ArgumentParser
import os

from bfgn.data_management import data_core, sequences
from bfgn.reporting import reports
from bfgn.experiments import experiments
import numpy as np

from gcrmnbc.validation import submit_validation_slurm
from gcrmnbc.model_training import submit_classification_slurm
from gcrmnbc.utils import logs, paths, shared_configs


def run_classification(
        config_name: str,
        label_experiment: str,
        response_mapping: str,
        build_only: bool = False,
        run_all: bool = False
) -> None:
    config = shared_configs.build_dynamic_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    logger = logs.get_model_logger(
        logger_name='log_run_classification', config_name=config_name, label_experiment=label_experiment,
        response_mapping=response_mapping,
    )

    # Create directories if necessary
    if not os.path.exists(config.data_build.dir_out):
        os.makedirs(config.data_build.dir_out)
    if not os.path.exists(config.model_training.dir_out):
        os.makedirs(config.model_training.dir_out)

    # Exit early if classification already finished -- assume build is finished too
    filepath_complete = paths.get_filepath_classify_complete(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    if os.path.exists(filepath_complete):
        return

    # Exit early if classification in progress
    filepath_lock = paths.get_filepath_classify_lock(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    try:
        file_lock = open(filepath_lock, 'x')
    except OSError:
        return

    try:
        # Build dataset
        data_container = data_core.DataContainer(config)
        data_container.build_or_load_rawfile_data()
        data_container.build_or_load_scalers()
        augs = None
        if label_experiment.endswith('_aug'):
            num_features = len(data_container.feature_band_types)
            assert num_features == 3, 'Is this not just RGB? Augmentations only work with RGB'
            augs = sequences.sample_custom_augmentations_constructor(num_features, config.data_build.window_radius)
        data_container.load_sequences(augs)

        # Build experiment
        experiment = experiments.Experiment(config)
        experiment.build_or_load_model(data_container)

        # Create preliminary model report before training
        reporter = reports.Reporter(data_container, experiment, config)
        try: 
            reporter.create_model_report()
        except:
            pass
        if build_only:
            filepath_built = paths.get_filepath_build_complete(
                config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
            open(filepath_built, 'w')
            if run_all:
                submit_classification_slurm.submit_classification_slurm(
                    labels_experiments=label_experiment, response_mappings=response_mapping, config_names=None,
                    config_regex=None, build_only=False, run_all=run_all
                )
            return

        # Train model
        experiment.fit_model_with_data_container(data_container, resume_training=True)

        # Build dataset for validation
        data_container = data_core.DataContainer(config)
        data_container.build_or_load_rawfile_data()
        data_container.build_or_load_scalers()
        augs = None
        data_container.load_sequences(augs)

        # Apply model to validation data
        filepath_probs = paths.get_filepath_applied_validation_probs(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        filepath_targets = paths.get_filepath_applied_validation_targets(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        _apply_model_to_validation_data(
            data_container=data_container, experiment=experiment, filepath_probs=filepath_probs,
            filepath_targets=filepath_targets
        )

        try: 
            reporter.create_model_report()
        except:
            pass

        # Create complete file to avoid rerunning in the future, close and remove lock file
        open(filepath_complete, 'w')

        # Start validation if necessary
        if run_all:
            submit_validation_slurm.submit_validation_slurm(
                labels_experiments=label_experiment, response_mappings=response_mapping, config_names=config_name,
                run_all=run_all
            )
    except Exception as error_:
        raise error_
    finally:
        file_lock.close()
        os.remove(filepath_lock)


def _apply_model_to_validation_data(
        data_container: data_core.DataContainer,
        experiment: experiments.Experiment,
        filepath_probs: str,
        filepath_targets: str
) -> None:
    # Prepare filepaths
    filepath_probs_tmp = filepath_probs + '.tmp'
    filepath_targets_tmp = filepath_targets + '.tmp'
    if not os.path.exists(os.path.dirname(filepath_probs)):
        os.makedirs(os.path.dirname(filepath_probs))
    # Prepare arrays for validation
    buffer = int(data_container.config.data_build.window_radius - data_container.config.data_build.loss_window_radius)
    validation_shape = list(data_container.validation_sequence.responses[0].shape)
    validation_shape[1] = int(validation_shape[1] - 2 * buffer)
    validation_shape[2] = int(validation_shape[2] - 2 * buffer)
    validation_shape = tuple(validation_shape)
    model_probs = np.memmap(filepath_probs_tmp, dtype=np.float32, mode='w+', shape=validation_shape)
    model_targets = np.memmap(filepath_targets_tmp, dtype=np.float32, mode='w+', shape=validation_shape)
    # Apply to validation data, process in chunks and store results in memmap arrays
    idx_start = 0
    num_batches = data_container.validation_sequence.__len__()
    for idx_batch in range(num_batches):
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


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--build_only', action='store_true')
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    run_classification(**args)
