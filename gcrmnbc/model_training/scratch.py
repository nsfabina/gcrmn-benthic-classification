from argparse import ArgumentParser
import os

from bfgn.data_management import data_core, sequences
from bfgn.reporting import reports
from bfgn.experiments import experiments

from gcrmnbc.utils import logs, paths, shared_configs


from gcrmnbc.utils import logs, shared_configs
import numpy as np
import keras.backend as K
from bfgn.architectures import config_sections
config_names = (
    'dense_unet_256_64_45_16', 'dense_unet_256_64_43_16', 'unet_256_64_45_16', 'unet_256_64_44_16',
    'dense_unet_256_64_44_16', 'unet_256_64_43_16'
)

def calc_stuff(model):
    shapes_concat = 0
    shapes_other = 0
    for l in model.layers:
        print(l.name, l.output_shape)
        single_layer_mem = 1
        for s in l.output_shape:
            if s is None:
                continue
            single_layer_mem *= s
        if l.name.startswith('concatenate'):
            shapes_concat += single_layer_mem
        else:
            shapes_other += single_layer_mem
    return shapes_other + shapes_concat


for config_name in config_names:
    response_mapping = 'lwr'
    filepath_config = os.path.join('../../../configs', config_name + '.yaml')
    config = shared_configs.build_dynamic_config(filepath_config, response_mapping)
    data_container = data_core.DataContainer(config)
    data_container.build_or_load_rawfile_data()
    data_container.build_or_load_scalers()
    data_container.load_sequences()  #custom_augmentations)
    num_features = len(data_container.feature_band_types)
    input_shape = (config.data_build.window_radius * 2, config.data_build.window_radius * 2, num_features)
    model = config_sections.create_model_from_architecture_config_section(
        config.model_training.architecture_name, config.architecture, input_shape
    )
    shapes_other = calc_stuff(model)
    time.sleep(2)
    trainable_count = np.sum([K.count_params(p) for p in set(model.trainable_weights)])
    non_trainable_count = np.sum([K.count_params(p) for p in set(model.non_trainable_weights)])
    assert K.floatx() == "float32"
    number_size = 4.0
    total_memory = number_size * (config.data_samples.batch_size * shapes_other + trainable_count + non_trainable_count)
    gbytes = np.round(total_memory / (1024.0 ** 3), 3)
    print(config_name, gbytes)
    import time
    time.sleep(2)

