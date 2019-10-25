import logging
import os

from gcrmnbc.utils import paths


def get_logger(logger_name: str) -> logging.Logger:
    if logger_name.endswith('.py'):
        logger_name = os.path.splitext(logger_name)[0]
    logger = logging.getLogger(logger_name)
    logger.setLevel('DEBUG')
    formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(logger_name + '.log')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_model_logger(
        logger_name: str, config_name: str, label_experiment: str, response_mapping: str
) -> logging.Logger:
    log_out = os.path.join(
        paths.get_dir_model_experiment_config(config_name, label_experiment, response_mapping),
        logger_name
    )
    if not log_out.endswith('.log'):
        log_out += '.log'
    if not os.path.exists(os.path.dirname(log_out)):
        os.makedirs(os.path.dirname(log_out))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_out)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
