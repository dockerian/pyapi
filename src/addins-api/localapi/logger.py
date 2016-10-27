import os
import logging
import logging.config
import logger_formatter
import yaml


def getLogger(name):

    # Get the path to the logging config yaml
    path = "{0}{1}".format(os.getcwd(), '/logging.yaml')

    # Set a basic level of logging
    logger = logging.basicConfig(level=logging.DEBUG)

    # Load up the logger based on the configs
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logger = logging.config.dictConfig(config)

    return logging.getLogger(name)


class Logger(logging.Logger):
    def __init__(self, name):
        colored_formatter = logger_formatter.LoggingFormatter(use_color=True)
        console_logging_handler = logging.StreamHandler()
        console_logging_handler.setFormatter(colored_formatter)
        console_logging_handler.setLevel(logging.DEBUG)

        logging.Logger.__init__(self, name, logging.DEBUG)
        logging.config.fileConfig('logging.conf')
        self.addHandler(console_logging_handler)
        self.setLevel(logging.DEBUG)
        self.propagate = True
