"""
# codebase __init__
"""

import requests
from pyramid.config import Configurator

from logger import getLogger

# pylint: disable=unused-import.
LOGGER = getLogger(__name__)

requests.packages.urllib3.disable_warnings()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    LOGGER.info('= main :: settings = %s', settings)

    config = Configurator(settings=settings)

    # Home
    config.add_route('home', '/')

    # Lastly, we scan the config and make the app
    # config.scan()

    return config.make_wsgi_app()
