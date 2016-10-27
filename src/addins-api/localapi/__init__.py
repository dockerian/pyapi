import requests

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound

from views.home_views import HomeViews
from views.catalog_views import CatalogViews
from views.catalog_item_views import CatalogItemViews
from views.deployment_views import DeploymentViews

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
    config.add_view(
        HomeViews, attr='get', request_method='GET', renderer='json')

    # Catalog
    config.add_route('catalog', '/v1/catalog')
    config.add_view(
        CatalogViews, attr='index', request_method='GET', renderer='json')

    # Catalog Item
    config.add_route('catalog_item', '/v1/catalog_item')
    config.add_view(
        CatalogItemViews, attr='install', request_method='POST')

    # Deployment
    config.add_route('deployment', '/v1/deployment')
    config.add_route('deployment_slash_id', '/v1/deployment/{id}')

    config.add_view(
            DeploymentViews,
            attr='status', request_method='GET', renderer='json',
            route_name='deployment_slash_id')
    config.add_view(
            DeploymentViews,
            attr='status', request_method='HEAD', renderer='json')
    config.add_view(
            DeploymentViews,
            attr='deploy', request_method='POST', renderer='json')
    config.add_view(
            DeploymentViews,
            attr='index', request_method='GET', renderer='json')

    # Lastly, we scan the config and make the app
    config.scan()
    return config.make_wsgi_app()
