from rsCNN.configuration import configs


_FILEPATH_TEMPLATE = 'config_template.yaml'


def create_configs() -> None:
    config_template = configs.create_config_from_file(_FILEPATH_TEMPLATE)

    for window_radius in (256, 128):
        for architecture_name in ('unet', 'dense_unet'):
            for block_structure in ([2, 2, 2, 2], [4, 4, 4]):
                for use_growth in (True, False):
                    # Create new config
                    config_template.data_build.window_radius = window_radius
                    config_template.data_build.loss_window_radius = int(window_radius / 2)
                    config_template.model_training.architecture_name = architecture_name
                    config_template.architecture.block_structure = block_structure
                    config_template.architecture.use_growth = use_growth

                    # Save config to file
                    basename = '{}_{}_{}'.format(architecture_name, window_radius, block_structure[0])
                    if use_growth is True:
                        basename += '_growth'
                    filepath = basename + '.yaml'
                    configs.save_config_to_file(config_template, filepath)


if __name__ == '__main__':
    create_configs()
