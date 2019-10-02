import argparse
import os

from bfgn.configuration import configs

from gcrmnbc.utils import paths


_FILEPATH_TEMPLATE = 'config_template.yaml'


def create_configs(print_size_estimate: bool = False) -> None:
    config_template = configs.create_config_from_file(_FILEPATH_TEMPLATE)

    # Please see previous version of this file for other configs that have been tested
    # The current configs are those which make the most sense with downsampled data, after testing that and finding
    # it successful
    window_radius = 128
    filters = 16
    for loss_window_radius in (48, 64):
        created_build_only = False
        for architecture_name in ('unet', 'dense_unet'):
            for block_structure in ([4, 4, 4, 4], [4, 4, 4], [4, 4]):
                # Create new config
                config_template.data_build.window_radius = window_radius
                config_template.data_build.loss_window_radius = loss_window_radius
                config_template.model_training.architecture_name = architecture_name
                config_template.architecture.block_structure = block_structure
                config_template.architecture.filters = filters

                # Test that models aren't too large -- hacky!
                if print_size_estimate:
                    from bfgn.experiments import experiments
                    config_template.data_build.dir_out = '.'
                    config_template.model_training.dir_out = '.'
                    config_template.architecture.n_classes = 5
                    config_template.architecture.block_structure = tuple(block_structure)
                    experiment = experiments.Experiment(config_template)
                    experiment._build_new_model((2*window_radius, 2*window_radius, 5))
                    print(window_radius, loss_window_radius, architecture_name, block_structure, filters)
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
