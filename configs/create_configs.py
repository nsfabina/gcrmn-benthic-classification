from bfgn.configuration import configs


_FILEPATH_TEMPLATE = 'config_template.yaml'


def create_configs() -> None:
    config_template = configs.create_config_from_file(_FILEPATH_TEMPLATE)

    for window_radius in (128, ):  #192, 256):
        created_build_only = False
        for architecture_name in ('unet', 'dense_unet'):
            for block_structure in ([2, 2, 2, 2], [2, 2, 2], [4, 4, 4], [4, 4]):
                for filters in (4, 8, 12, 16):
                    # Create new config
                    config_template.data_build.window_radius = window_radius
                    config_template.data_build.loss_window_radius = int(window_radius / 2)
                    config_template.model_training.architecture_name = architecture_name
                    config_template.architecture.block_structure = block_structure
                    config_template.architecture.filters = filters

                    # Save config to file
                    basename = '{}_{}_{}{}_{}'.format(
                        architecture_name, window_radius, block_structure[0], len(block_structure), filters)
                    filepath = basename + '.yaml'
                    configs.save_config_to_file(config_template, filepath)

                    # Save config for build only
                    if not created_build_only:
                        configs.save_config_to_file(config_template, 'build_only_{}.yaml'.format(window_radius))
                        created_build_only = True


if __name__ == '__main__':
    create_configs()
