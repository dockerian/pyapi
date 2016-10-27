from pyramid.config import Configurator

from views import home_views
from views import package_views

from common.logger import getLogger
logger = getLogger(__name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    logger.info('= main :: settings = %s', settings)

    config = Configurator(settings=settings)

    # Home
    config.add_route('home', '/')
    config.add_view(home_views.HomeViews, attr='get', request_method='GET',
                    renderer='json')

    # Packages API - collection
    config.add_route('packages',
                     '/v1/products/{product_id}/packages')
    config.add_view(package_views.PackagesViews, attr='index',
                    request_method='GET', renderer='json')

    config.add_view(package_views.PackagesViews, attr='upload',
                    request_method='POST', renderer='json')

    # Packages API - individual item
    config.add_route('package',
                     '/v1/products/{product_id}/packages/{package_id}')
    config.add_view(package_views.PackageViews, attr='get',
                    request_method='GET', renderer='json')

    # Lastly, we scan the config and make the app
    config.scan()
    return config.make_wsgi_app()
