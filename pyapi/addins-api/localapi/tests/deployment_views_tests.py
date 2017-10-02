import json
import mock
import unittest
import uuid

from mock import Mock, MagicMock, patch, mock_open
from pyramid.testing import DummyRequest, DummyResource, setUp, tearDown
from pyramid.response import Response

from .. views.deployment_views import DeploymentViews

from .. logger import *
logger = getLogger(__name__)


class DeploymentViewsTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

        self.deploy_failure = {'status': 500, 'errors': 'error_message'}
        self.deploy_code404 = {'status': 404, 'errors': 'not found'}
        self.deploy_success = {
            'status': 202,
            'deployment_id': 'deployment_id',
            'deploy_status': 'deployment_status',
            'destination': 'destination_url',
            'package': 'package_name'}
        self.params_missing_dest = {'package': 'package'}
        self.params_missing_package = {'dest': 'dest'}
        self.params_missing_user = {'dest': 'd', 'package': 'p'}
        self.params_missing_pass = {
            'dest': 'd', 'package': 'p', 'username': 'u'}
        self.params_deploy = {
            'dest': 'dest',
            'package': 'package',
            'username': 'username',
            'password': 'password'}
        self.params_status = {'id': 'aaaa'}
        self.status_result = {
            'status': 200,
            'data': self.deploy_success
        }

        request = DummyRequest()
        request.matchdict = {'id': '{0}'.format(uuid.uuid1())}
        request.params = self.params_deploy
        self.the_view = DeploymentViews(request)

    def tearDown(self):
        tearDown()

    def test_index(self):
        all_list = ["aaa", "bbb"]
        with patch(
                'localapi.views.deployment_views.DeploymentStatus',
                autospec=True) as status_class:
            mock_status = MagicMock()
            mock_status.get_all = MagicMock()
            mock_status.get_all.return_value = all_list
            status_class.return_value = mock_status
            response = self.the_view.index()
            data = json.loads(response.body)
            self.assertEqual(data, all_list)

    @patch('localapi.views.deployment_views.deploy_package')
    def test_deploy(self, mock_deploy_package):
        deployment_id = self.deploy_success['deployment_id']
        mock_deploy_package.return_value = self.deploy_success
        response = self.the_view.deploy()
        self.assertTrue('accepted' in '{0}'.format(response))

    @patch('localapi.views.deployment_views.deploy_package')
    def test_deploy_exception(self, mock_deploy_package):
        error_message = 'Exception on deploy_package'
        mock_deploy_package.side_effect = Exception(error_message)
        response = self.the_view.deploy()
        self.assertRaises(Exception, error_message)

    @patch('localapi.views.deployment_views.deploy_package')
    def test_deploy_fail(self, mock_deploy_package):
        error = self.deploy_code404['errors']
        mock_deploy_package.return_value = self.deploy_code404
        response = self.the_view.deploy()
        self.assertEqual('404 Not Found', response.status)

    @patch('localapi.views.deployment_views.get_status')
    def test_status(self, mock_get_status):
        status = self.deploy_success['deploy_status']
        request = DummyRequest()
        request.params = self.params_status
        test_view = DeploymentViews(request)
        mock_get_status.return_value = self.status_result
        response = test_view.status()
        self.assertTrue(status in response.body)

    @patch('localapi.views.deployment_views.get_status')
    def test_status_fail(self, mock_get_status):
        status = self.deploy_success['deploy_status']
        request = DummyRequest()
        request.params = self.params_status
        test_view = DeploymentViews(request)
        mock_get_status.return_value = self.deploy_code404
        response = test_view.status()
        body = '{0}'.format(response)
        self.assertEqual('404 Not Found', response.status)
        self.assertTrue(self.params_status['id'] in body)

    @patch('localapi.views.deployment_views.get_status')
    def test_status_not_found(self, mock_get_status):
        status = self.deploy_success['deploy_status']
        request = DummyRequest()
        request.params = self.params_status
        test_view = DeploymentViews(request)
        mock_get_status.return_value = self.deploy_failure
        response = test_view.status()
        body = '{0}'.format(response)
        self.assertEqual('500 Internal Server Error', response.status)
