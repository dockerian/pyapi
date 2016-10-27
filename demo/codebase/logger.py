import os
import logging
import logging.config
import logger_formatter
import yaml


def getLogger(name):
    # Set a basic level of logging
    logger = logging.basicConfig(level=logging.DEBUG)

    # Get the path to the logging config yaml
    logging_cfg = "{0}{1}".format(os.getcwd(), '/logging.yaml')

    # Load up the logger based on the configs
    if (os.path.exists(logging_cfg)):
        with open(logging_cfg, 'rt') as f:
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

        configs = ['conf', 'yaml']
        for cfg in configs:
            # Get the path to the logging config file
            config_file = "{0}/logging.{1}".format(os.getcwd(), cfg)
            # Load up the logger based on the configs
            if (os.path.exists(config_file)):
                if (cfg == 'yaml'):
                    with open(config_file, 'rt') as f:
                        config = yaml.load(f.read())
                        logging.config.dictConfig(config)
                else:
                    logging.config.fileConfig(config_file)
                # break

        self.addHandler(console_logging_handler)
        self.setLevel(logging.DEBUG)
        self.propagate = True
