from pyramid.view import view_defaults
from pyramid.response import Response
from pyramid.httpexceptions import HTTPOk
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPInternalServerError

from .. catalog import get_package_list

from .. logger import getLogger
logger = getLogger(__name__)


@view_defaults(route_name='catalog')
class CatalogViews(object):

    def __init__(self, request):
        self.request = request

    def index(self):
        """
        Produce a list of packages stored in the global & local catalog
        Response format:
            Success:
            {   'status': 200,
                'packages': [ {'pkg1': 'test'},
                              {'pkg1': 'test'} ] }

            404:
            {   'status': 404, 'packages': [] }

            Other:
            {   'status': 500, 'errors': "Error messages detailing error(s)." }
        """
        logger.info("\n=== index ===")

        try:
            result = get_package_list()
            if result['status'] == 404:
                return {'status': 404, 'packages': []}
            else:
                return result

        except Exception as e:
            msg = "Exception getting package list. Details: {0}".format(e)
            logger.exception(msg)
            return {'status': 500, 'errors': msg}
