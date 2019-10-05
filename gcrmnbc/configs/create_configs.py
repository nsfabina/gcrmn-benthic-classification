import argparse
import os

from bfgn.configuration import configs

from gcrmnbc.utils import paths


_FILEPATH_TEMPLATE_UNET = 'config_template_unet.yaml'
_FILEPATH_TEMPLATE_FLAT = 'config_template_flatnet.yaml'


def create_configs(print_size_estimate: bool = False) -> None:
    _create_unet_configs(print_size_estimate)
    _create_flatnet_configs(print_size_estimate)


def _create_unet_configs(print_size_estimate: bool = False) -> None:
    config_template = configs.create_config_from_file(_FILEPATH_TEMPLATE_UNET)

    # Please see previous versions of this file for other configs that have been tested
    window_radius = 128
    loss_window_radius = 64
    architecture_name = 'dense_unet'
    all_filters = (4, 8, 4, 8, 16)
    all_growths = (True, True, False, False, False)
    all_batch_norms = (True, False)
    all_block_structures = (
        [4, 4],
        [4, 4, 4],
        [6, 6],
        [6, 6, 6],
        [8, 8],
        [8, 8, 8],
    )
    for filters, use_growth in zip(all_filters, all_growths):
        created_build_only = False
        for use_bn in all_batch_norms:
            for block_structure in all_block_structures:
                # Create new config
                config_template.data_build.window_radius = window_radius
                config_template.data_build.loss_window_radius = loss_window_radius
                config_template.model_training.architecture_name = architecture_name
                config_template.architecture.block_structure = block_structure
                config_template.architecture.filters = filters
                config_template.architecture.use_batch_norm = use_bn
                config_template.architecture.use_growth = use_growth

                # Test that models aren't too large -- hacky!
                if print_size_estimate:
                    from bfgn.experiments import experiments
                    config_template.data_build.dir_out = '.'
                    config_template.model_training.dir_out = '.'
                    config_template.architecture.n_classes = 5
                    config_template.architecture.block_structure = tuple(block_structure)
                    experiment = experiments.Experiment(config_template)
                    experiment._build_new_model((2*window_radius, 2*window_radius, 5))
                    print('unet', window_radius, loss_window_radius, architecture_name, block_structure, filters)
                    print(experiment.calculate_model_memory_footprint(config_template.data_samples.batch_size))
                    print()
                    os.remove('config.yaml')
                    os.remove('model.h5')
                    os.remove('log.out')

                # Save config to file
                configs.save_config_to_file(config_template, paths.get_filepath_config_from_config(config_template))

                # Save config for build only
                if not created_build_only:
                    configs.save_config_to_file(
                        config_template, paths.get_filepath_build_only_config_from_config(config_template))
                    created_build_only = True


def _create_flatnet_configs(print_size_estimate: bool = False) -> None:
    config_template = configs.create_config_from_file(_FILEPATH_TEMPLATE_FLAT)

    # Please see previous versions of this file for other configs that have been tested
    window_radius = 128
    loss_window_radius = 64
    all_num_layers = (8, 16, 24)
    all_filters = (16, 32)
    all_batch_norms = (True, False)
    for num_layers in all_num_layers:
        created_build_only = False
        for filters in all_filters:
            for batch_norm in all_batch_norms:
                # Create new config
                config_template.data_build.window_radius = window_radius
                config_template.data_build.loss_window_radius = loss_window_radius
                config_template.architecture.num_layers = num_layers
                config_template.architecture.filters = filters
                config_template.architecture.use_batch_norm = batch_norm

                # Test that models aren't too large -- hacky!
                if print_size_estimate:
                    from bfgn.experiments import experiments
                    config_template.data_build.dir_out = '.'
                    config_template.model_training.dir_out = '.'
                    config_template.architecture.n_classes = 5
                    experiment = experiments.Experiment(config_template)
                    experiment._build_new_model((2*window_radius, 2*window_radius, 5))
                    print('flat net', window_radius, loss_window_radius, num_layers, filters, batch_norm)
                    print(experiment.calculate_model_memory_footprint(config_template.data_samples.batch_size))
                    print()
                    os.remove('config.yaml')
                    os.remove('model.h5')
                    os.remove('log.out')

                # Save config to file
                configs.save_config_to_file(config_template, paths.get_filepath_config_from_config(config_template))

                # Save config for build only
                if not created_build_only:
                    configs.save_config_to_file(
                        config_template, paths.get_filepath_build_only_config_from_config(config_template))
                    created_build_only = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--print_size_estimate', action='store_true')
    args = parser.parse_args()
    create_configs(args.print_size_estimate)
