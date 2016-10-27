import json
import StringIO
import sys
import traceback

from pyramid import httpexceptions
from pyramid.view import view_defaults

from .. import package
from common import swift

from common.logger import getLogger
logger = getLogger(__name__)


@view_defaults(route_name='packages')
class PackagesViews(object):

    def __init__(self, request):
        self.request = request

    def index(self):
        """
        Produce a list of packages stored in the global catalog:
        http://example.com/v1/products/{product_id}/packages
        """
        logger.info("======= index =======")

        try:
            # product_id is not used atm
            product_id = self.request.matchdict.get('product_id', None)
            if not product_id:
                return httpexceptions.HTTPBadRequest(
                    json_body={'errors': "Missing Product ID"})

            filters = self.request.params.get('filters')
            kwargs = {}
            if filters:
                kwargs['filters'] = filters
            result = package.get_package_list(**kwargs)

            if result['status'] == 200:
                return result
            else:
                return httpexceptions.HTTPNotFound(json_body={})

        except Exception as e:
            logger.exception(e)
            tb = traceback.format_exc()
            return httpexceptions.HTTPInternalServerError(
                    json_body={'errors': "{0}, {1}".format(e, tb)},
                    explanation=e,
                    detail=tb)

    def upload(self):
        """
        Enable the upload of a package to the global catalog:
        http://example.com/v1/products/{product_id}/packages
        """
        logger.info("======= upload =======")

        try:
            # Note: product_id is not used atm
            product_id = self.request.matchdict.get('product_id', None)
            if not product_id:
                return httpexceptions.HTTPBadRequest(
                    json_body={'errors': "Missing Product ID"})
            logger.info("Product ID: {0}".format(product_id))

            file_contents = self.request.params['fileupload']
            if file_contents is None:
                return httpexceptions.HTTPBadRequest(
                    json_body={'errors': "Missing file to upload"})
            file_name = file_contents.filename
            logger.info("Upload filename: {0}".format(file_name))

            result = package.save_package(file_name, file_contents)
            logger.debug(result)
            if result['status'] == 201:
                logger.info("Status of upload: 201")
                return httpexceptions.HTTPCreated(json_body={})
            else:
                logger.info("Status of upload: {0}".format(result['status']))
                return httpexceptions.HTTPInternalServerError(
                        json_body={'errors': result['errors']})

        except Exception as e:
            logger.exception(e)
            tb = traceback.format_exc()
            return httpexceptions.HTTPInternalServerError(
                    json_body={'errors': "{0}, {1}".format(e, tb)},
                    explanation=e,
                    detail=tb)


@view_defaults(route_name='package')
class PackageViews(object):

    def __init__(self, request):
        self.request = request

    def get(self):
        """
        Return a package stored in the global catalog:
        http://example.com/v1/products/{product_id}/packages/{package_id}
        """
        logger.info("======= get package =======")

        # product_id is not used atm
        product_id = self.request.matchdict.get('product_id', None)
        if not product_id:
            return httpexceptions.HTTPBadRequest(
                json_body={'errors': "Missing Product ID"})

        package_id = self.request.matchdict.get('package_id', None)
        if not package_id:
            return httpexceptions.HTTPBadRequest(
                json_body={'errors': "Missing Package ID"})

        pkg_filename = "{0}{1}".format(package_id, ".tar.gz")

        try:
            result = package.get_package(pkg_filename)
            if result["status"] and result["status"] == 404:
                return httpexceptions.HTTPNotFound()
            else:
                return httpexceptions.HTTPOk(
                    accept_ranges='bytes',
                    body=StringIO.StringIO(result['file_contents']).read(),
                    content_type="application/json")

        except Exception as e:
            logger.exception(e)
            tb = traceback.format_exc()
            return httpexceptions.HTTPInternalServerError(
                    json_body={'errors': "{0}, {1}".format(e, tb)},
                    explanation=e,
                    detail=tb)
