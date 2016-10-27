import requests

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound

from logger import getLogger
logger = getLogger(__name__)

requests.packages.urllib3.disable_warnings()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    logger.info('= main :: settings = %s', settings)

    config = Configurator(settings=settings)

    # Home
    config.add_route('home', '/')

    # Lastly, we scan the config and make the app
    # config.scan()

    return config.make_wsgi_app()
