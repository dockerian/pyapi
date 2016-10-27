from pyramid.view import view_defaults
from pyramid.response import Response
from pyramid.httpexceptions import HTTPOk
from pyramid.httpexceptions import HTTPNotFound, HTTPInternalServerError


from .. catalog import install_package

from .. logger import getLogger
logger = getLogger(__name__)


@view_defaults(route_name='catalog_item')
class CatalogItemViews(object):

    def __init__(self, request):
        self.request = request

    def install(self):
        """
        Install a package from the global catalog into the local catalog
        """
        logger.info("======= install =======")

        try:
            package_name = self.request.params['package_name']
            if package_name is not None and len(package_name) > 1:
                install_package(package_name)
                return HTTPOk
            else:
                return HTTPInternalServerError(
                    explanation="Package name must be specified")

        except Exception as e:
            message = "Exception installing a package to the local catalog"
            logger.exception(message)
            details = "Details: {0}".format(e)
            return HTTPInternalServerError(
                explanation=message, details=details)
