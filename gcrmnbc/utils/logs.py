import logging
import os
import sys


def get_logger(logger_name: str) -> logging.Logger:
    if logger_name.endswith('.py'):
        logger_name = os.path.splitext(logger_name)[0]
    logger = logging.getLogger(logger_name)
    logger.setLevel('DEBUG')
    formatter = logging.Formatter(fmt='%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(logger_name + '.log')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
