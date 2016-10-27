import json
import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open

from .. deploy.deploy_status import DeploymentStatus
from .. deploy.package import Package
from .. logger import getLogger
logger = getLogger(__name__)


class DeployStatusTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

        self.pkg_name = 'package name'
        self.filename = '{0}.tar.gz'.format(self.pkg_name)
        self.cwd_path = '/foo/bar'
        self.pkg_path = '{0}/{1}'.format(self.cwd_path, self.filename)
        self.endpoint = 'http://api.0.0.0.0.xip.io/'
        self.dest_url = 'http://{0}.0.0.0.0.xip.io'.format(self.pkg_name)
        self.manifest = '{0}.json'.format(self.pkg_name)
        self.package1 = Package(self.pkg_name, self.pkg_path, self.endpoint)

        self.status_0 = DeploymentStatus()
        self.status_1 = DeploymentStatus(self.package1)

        self.json_obj = {
              "datetime": "2015-07-08 14:35:52.951490",
              "deploy_id": "6eeca9c0-257e-11e5-9760-985aeb8b7458",
              "destination": "http://node-env.15.125.107.133.xip.io",
              "deploy_status": "SUCCESS",
              "history": [],
              "package": "node-env",
            }
        self.contents = json.dumps(self.json_obj)

    def tearDown(self):
        testing.tearDown()

    def test_constructor(self):
        self.assertEqual(self.status_0.package, None)
        self.assertEqual(self.status_0.destination, '')
        self.assertEqual(self.status_0.package_name, 'N/A')
        self.assertEqual(self.status_0.swift, None)
        self.assertEqual(self.status_1.package, self.package1)
        self.assertEqual(self.status_1.destination, self.package1.destination)
        self.assertEqual(self.status_1.package_name, self.package1.name)
        self.assertEqual(self.status_1.swift, None)
        pass

    @patch('localapi.deploy.deploy_status.get_deployment_list')
    def test_get_all(self, mock_get_list):
        deployment_list = ['aaa', 'bbb']
        mock_get_list.return_value = deployment_list
        result_0 = self.status_0.get_all()
        result_1 = self.status_1.get_all()
        self.assertEqual(result_0, deployment_list)
        self.assertEqual(result_1, deployment_list)

    @patch('localapi.deploy.deploy_status.get_file_contents')
    def test_get_status(self, mock_get_contents):
        mock_get_contents.return_value = self.contents
        result = self.status_0.get_status('id')
        self.assertEqual(result, self.json_obj)

    @patch('localapi.deploy.deploy_status.get_file_contents')
    def test_get_status_exception(self, mock_get_contents):
        error_message = 'Exception on getting file contents'
        mock_get_contents.side_effect = Exception(error_message)
        result = self.status_0.get_status('id')
        self.assertRaises(Exception, error_message)

    @patch('localapi.deploy.deploy_status.save_file_contents')
    def test_set_status(self, mock_save_contents):
        mock_status = MagicMock()
        mock_status.return_value = self.json_obj
        self.status_0.get_status = mock_status
        result = self.status_0.set_status('id-0', 'FOO')
        self.assertEqual(result['deploy_status'], 'FOO')
        self.assertEqual(result['deploy_id'], 'id-0')
        pass
