import os
import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open

from .. deploy.deploy import Deployment
from .. deploy.helion_cli import HelionCliComposer
from .. deploy.batch import Batch
from .. logger import getLogger
logger = getLogger(__name__)


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

        self.cli_composer = HelionCliComposer(
            'endpoint',
            'username',
            'password',
            '/cwd')
        self.deploy_status = Mock()
        self.package = Mock(cwd='/foo', name='bar', path='/foo/bar.tar.gz')
        self.pkg_name = 'package name'
        self.use_package_path = True
        self.deploy = Deployment(
            self.package, self.cli_composer, self.deploy_status,
            self.use_package_path)

    def tearDown(self):
        testing.tearDown()

    def test_deploy_constructor(self):
        self.use_package_path = False
        deploy = Deployment(
            self.package, self.cli_composer, self.deploy_status,
            self.use_package_path)
        deploy.get_package_batch()

        self.assertEqual(len(deploy.batch.batch_cmds), 5)
        self.assertNotEqual(deploy.cwd, self.package.cwd)
        self.assertEqual(deploy.cli_composer, self.cli_composer)
        self.assertEqual(deploy.cwd_use_package_path, self.use_package_path)
        self.assertEqual(deploy.deploy_status, self.deploy_status)
        self.assertEqual(deploy.package, self.package)

    def test_deploy_constructor_use_package_path(self):
        self.deploy.get_package_batch()
        self.assertEqual(len(self.deploy.batch.batch_cmds), 4)
        self.assertEqual(self.deploy.cwd, self.package.cwd)
        self.assertEqual(self.deploy.cli_composer, self.cli_composer)
        self.assertEqual(
            self.deploy.cwd_use_package_path, self.use_package_path)
        self.assertEqual(self.deploy.deploy_status, self.deploy_status)
        self.assertEqual(self.deploy.package, self.package)

    @patch('shutil.rmtree')
    def test_cleanup(self, mock_rmtree):
        self.deploy.cleanup()
        self.assertTrue(mock_rmtree.called)

    @patch('shutil.rmtree')
    def test_cleanup_exception(self, mock_rmtree):
        error_message = "Exception on delete_directory_tree"
        mock_rmtree.side_effect = Exception(error_message)
        self.deploy.cleanup()
        self.assertRaises(Exception, error_message)

    @patch('shutil.rmtree')
    def test_deploy(self, mock_rmtree):
        with patch('localapi.deploy.deploy.BatchProcess', autospec=True) as \
                batch_process_class:
            mock_process = MagicMock()
            mock_process.execute = MagicMock()
            batch_process_class.return_value = mock_process
            self.deploy.set_status = MagicMock()
            self.deploy.download_package = MagicMock()
            self.deploy.deploy()
            self.assertTrue(mock_process.execute.called)
            self.assertTrue(mock_rmtree.called)

    @patch('shutil.rmtree')
    def test_deploy_exception(self, mock_rmtree):
        with patch('localapi.deploy.deploy.BatchProcess', autospec=True) as \
                batch_process_class:
            mock_process = MagicMock()
            mock_process.execute = MagicMock()
            error_message = 'Exception on batch process execute'
            mock_process.execute.side_effect = Exception(error_message)
            batch_process_class.return_value = mock_process
            self.deploy.set_status = MagicMock()
            self.deploy.download_package = MagicMock()
            self.deploy.deploy()
            self.assertTrue(mock_process.execute.called)
            self.assertRaises(Exception, error_message)
            self.assertTrue(mock_rmtree.called)

    @patch('tempfile.mkdtemp')
    @patch('localapi.deploy.deploy.swift.get_file_contents')
    def test_download_package(self, mock_get_file, mock_mkdtemp):
        cwd = '/foo/bar'
        mock_mkdtemp.return_value = cwd
        package_path = '{0}/{1}.tar.gz'.format(cwd, self.pkg_name)
        with patch('__builtin__.open', mock_open(), create=True):
            with open('foo', 'w') as handle:
                handle.write()
                result = self.deploy.download_package()
                self.assertEqual(result, self.deploy.package.path)
        pass

    @patch('tempfile.mkdtemp')
    @patch('localapi.deploy.deploy.delete_directory_tree')
    @patch('localapi.deploy.deploy.swift.get_file_contents')
    def test_download_package_exception(
                self, mock_get_file, mock_deltree, mock_mkdtemp):
        error_message = 'Exception on get file contents'
        mock_get_file.side_effect = Exception(error_message)
        try:
            result = self.deploy.download_package()
        except Exception:
            pass
        finally:
            pass
            self.assertRaises(Exception, error_message)
            self.assertTrue(mock_get_file.called)
        pass
