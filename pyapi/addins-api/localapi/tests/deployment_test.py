import os
import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open

from .. deployment import deploy_package, get_status
from .. logger import getLogger
logger = getLogger(__name__)


def set_status(status):
    logger.info('======= Setting status: "{0}" =======\n'.format(status))


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

        self.endpoint = 'endpoint'
        self.username = 'username',
        self.password = 'password',
        self.pkg_name = 'package name'
        self.cwd_path = '/foo'
        self.pkg_path = '/{0}/{1}.tar.gz'.format(self.cwd_path, self.pkg_name)
        self.data = {
            'deploy_id': 'id',
            'deploy_status': 'FOOBAR',
            'datetime': '',
            'package': self.pkg_name}

    def tearDown(self):
        testing.tearDown()

    @patch('localapi.deployment.swift.check_file_exists')
    @patch('tempfile.mkdtemp')
    def test_deploy_package(self, mock_mkdtemp, mock_check):
        mock_mkdtemp.return_value = self.cwd_path
        with patch(
                'localapi.deployment.Deployment',
                autospec=True) as deployment_class:
            mock_deploy = MagicMock()
            deployment_class.return_value = mock_deploy
            with patch(
                    'localapi.deployment.DeploymentStatus',
                    autospec=True) as status_class:
                mock_status = MagicMock()
                mock_status.set_status = MagicMock()
                status_class.return_value = mock_status
                result = deploy_package(
                        self.pkg_name,
                        self.endpoint, self.username, self.password)
                self.assertEqual(result['package'], self.pkg_name)
                self.assertEqual(result['status'], 202)
        pass

    @patch('localapi.deployment.swift.check_file_exists')
    @patch('tempfile.mkdtemp')
    def test_deploy_package_exception(self, mock_mkdtemp, mock_check):
        mock_mkdtemp.return_value = self.cwd_path
        error_message = 'Exception on mkdtemp'
        mock_mkdtemp.side_effect = Exception(error_message)
        with patch(
                'localapi.deployment.Deployment',
                autospec=True) as deployment_class:
            result = deploy_package(
                    self.pkg_name,
                    self.endpoint, self.username, self.password)
            self.assertRaises(Exception, mock_mkdtemp, error_message)
            self.assertEqual(result['status'], 500)
        pass

    def test_get_status(self):
        with patch(
                'localapi.deployment.DeploymentStatus',
                autospec=True) as status_class:
            mock_status = MagicMock()
            mock_status.get_status = MagicMock()
            mock_status.get_status.return_value = self.data
            status_class.return_value = mock_status
            result = get_status('id')
            self.assertEqual(result['status'], 200)
        pass

    def test_get_status_404(self):
        with patch(
                'localapi.deployment.DeploymentStatus',
                autospec=True) as status_class:
            mock_status = MagicMock()
            mock_status.get_status = MagicMock()
            mock_status.get_status.return_value = {}
            status_class.return_value = mock_status
            result = get_status('id')
            self.assertEqual(result['status'], 404)
        pass

    def test_get_status_exception(self):
        with patch(
                'localapi.deployment.DeploymentStatus',
                autospec=True) as status_class:
            mock_status = MagicMock()
            mock_status.get_status = MagicMock()
            error_message = 'Exception on get status'
            mock_status.get_status.side_effect = Exception(error_message)
            status_class.return_value = mock_status
            result = get_status('id')
            self.assertRaises(Exception, error_message)
            self.assertEqual(result['status'], 500)
        pass
