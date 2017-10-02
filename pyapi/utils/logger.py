"""
logger module

@author: Jason Zhu <jason.zhuyx@gmail.com>
"""

import os
import logging
import logging.config
import yaml


def get_logger(name, level=logging.DEBUG):
    """
    Get a logger and load logging.yaml config file if exists
    """
    # Set a basic level of logging
    logging.basicConfig(level=level)

    # Get the path to the logging config yaml
    dir_py_file = os.path.dirname(os.path.realpath(__file__))
    dir_project = os.path.dirname(dir_py_file)
    cfg_logging = os.path.join(dir_project, 'logging.yaml')

    # Load up the logger based on the configs
    if os.path.exists(cfg_logging):
        with open(cfg_logging, 'rt') as file_handle:
            config = yaml.load(file_handle.read())
            logging.config.dictConfig(config)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def raise_ni(method_name):
    """
    Raise NotImplementedError on specified method name
    """
    raise NotImplementedError(
        'must implement {} in derived class'.format(method_name))
