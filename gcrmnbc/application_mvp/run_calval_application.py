from argparse import ArgumentParser
import os

from bfgn.data_management import data_core
from bfgn.experiments import experiments

from gcrmnbc.application import application_millennium_project
from gcrmnbc.application_mvp import submit_calculation_slurm
from gcrmnbc.utils import logs, paths, shared_configs


def run_application(config_name: str, label_experiment: str, response_mapping: str, run_all: bool = False) -> None:
    config = shared_configs.build_dynamic_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    logger = logs.get_model_logger(
        'log_run_calval_application', config_name=config_name, label_experiment=label_experiment,
        response_mapping=response_mapping,
    )

    # Build dataset
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()

    # Build experiment
    experiment = experiments.Experiment(config)
    experiment.build_or_load_model(data_container)

    # Apply model
    dir_model_out = paths.get_dir_calval_data_experiment_config(
        config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
    reefs = sorted([reef for reef in os.listdir(paths.DIR_DATA_EVAL)])
    for idx_filepath, reef in enumerate(reefs):
        logger.debug('Applying model to reef {}'.format(reef))
        dir_reef_in = paths.get_dir_eval_data_experiment(reef=reef, label_experiment=label_experiment)
        filepath_features = os.path.join(dir_reef_in, 'features.vrt')
        dir_reef_out = os.path.join(dir_model_out, reef)
        if not os.path.exists(dir_reef_out):
            try:
                os.makedirs(dir_reef_out)
            except FileExistsError:
                pass
        application_millennium_project.apply_to_raster(
            experiment=experiment, data_container=data_container, filepath_features=filepath_features,
            dir_out=dir_reef_out
        )

    # Create application.complete if all files are done
    are_reefs_complete = list()
    for reef in reefs:
        filepath_reef_complete = os.path.join(dir_model_out, reef, paths.FILENAME_APPLY_COMPLETE)
        are_reefs_complete.append(os.path.exists(filepath_reef_complete))
    if all(are_reefs_complete):
        filepath_model_complete = paths.get_filepath_calval_apply_complete(
            config_name=config_name, label_experiment=label_experiment, response_mapping=response_mapping)
        open(filepath_model_complete, 'w')
        if run_all and 'millennium' not in label_experiment:
            submit_calculation_slurm.submit_calculation_slurm(
                labels_experiments=label_experiment, response_mappings=response_mapping, recalculate=False)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--config_name', required=True)
    parser.add_argument('--label_experiment', required=True)
    parser.add_argument('--response_mapping', required=True)
    parser.add_argument('--run_all', action='store_true')
    args = vars(parser.parse_args())
    run_application(**args)
