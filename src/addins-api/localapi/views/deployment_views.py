import json
import traceback

from pyramid.httpexceptions import HTTPOk, HTTPAccepted
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.response import Response
from pyramid.view import view_defaults

from .. deploy.deploy_status import DeploymentStatus
from .. deployment import deploy_package, get_status
from .. logger import getLogger
logger = getLogger(__name__)


@view_defaults(route_name='deployment', renderer='json')
class DeploymentViews(object):

    def __init__(self, request):
        logger.debug('======= deployment request: {0}'.format(request))
        logger.debug('request.matchdict: {0}'.format(request.matchdict))
        logger.debug('request.params: {0}'.format(request.params))
        self.request = request

    def __get_deploy_request_params(self):
        """
        Get and check request parameters for deployment
        """
        err = ""
        package_name = self.request.params.get('package', '').strip()
        dest = self.request.params.get('dest', '').strip()
        username = self.request.params.get('username', '').strip()
        password = self.request.params.get('password', '').strip()

        if (not package_name):
            err = "Missing package (name) parameter"
        elif (not dest):
            err = "Missing dest: destination endpoint url"
        elif (not username):
            err = "Missing username parameter"
        elif (not password):
            err = "Missing password"
        return [err, package_name, dest, username, password]

    def __get_deployment_id_in_request(self):
        """
        Get and check parameters for status request
        """
        deployment_id = ''
        if ('id' in self.request.matchdict.keys()):
            deployment_id = self.request.matchdict['id']
        if (not deployment_id):
            deployment_id = self.request.params.get('id', '').strip()
        return deployment_id

    def index(self):
        logger.debug("======= index =======")
        deployment_status = DeploymentStatus()
        deployment_list = deployment_status.get_all()
        # ToDo [zhuyux]: To render content as application/ja
        body = json.dumps(deployment_list, sort_keys=True)
        response = HTTPOk()
        response.content_type = 'application/json; charset=UTF-8'
        response.body = body
        return response

    def deploy(self):
        """
        Deploy a package to destination
        """
        logger.debug("======= deploy =======")

        try:
            err, pkg_name, dest, email, passwd = \
                    self.__get_deploy_request_params()
            if (err):
                return HTTPBadRequest(err)

            result = deploy_package(pkg_name, dest, email, passwd)

            if result['status'] == 202:
                deployment_id = result['deployment_id']
                status_url = 'deployment/{0}'.format(deployment_id)
                contents = json.dumps(result, sort_keys=True)
                response = HTTPAccepted()
                response.headers = {
                    'Content-Type': 'application/json; charset=UTF-8',
                    'Location': status_url}
                response.body = contents
                return response
            elif result['status'] == 404:
                msg = 'Cannot find package "{0}" installed.'.format(pkg_name)
                return HTTPNotFound(detail=msg)
            else:
                return HTTPInternalServerError(detail=result['errors'])

        except Exception as e:
            stack_info = traceback.format_exc()
            logger.exception(stack_info)
            return HTTPInternalServerError(detail=stack_info)

    def status(self):
        """
        Get the status of a package deployment
        """
        logger.debug("======= status =======")

        try:
            deployment_id = self.__get_deployment_id_in_request()
            if (not deployment_id):
                return self.index()

            result = get_status(deployment_id)
            logger.debug(result)
            if result['status'] == 200 and result['data']:
                detail = result['data']
                status = '{0}'.format(detail['deploy_status'])
                dest_url = '{0}'.format(detail['destination'])
                contents = json.dumps(result['data'], sort_keys=True)
                response = HTTPOk()
                response.headers = {
                    'Content-Type': 'application/json; charset=UTF-8',
                    'Deployment-Status': status,
                    'Location': dest_url}
                response.body = contents
                return response
            elif result['status'] == 404:
                detail = 'No deployment found for {0}'.format(deployment_id)
                return HTTPNotFound(detail=detail)
            else:
                detail = 'Failed to get deployment status for {0}'.format(
                    deployment_id)
                return HTTPInternalServerError(detail=detail)

        except Exception as e:
            tb_info = traceback.format_exc()
            msg = 'Exception on getting deployment status.\n'.format(tb_info)
            logger.exception(msg)
            return HTTPInternalServerError(detail=tb_info)
