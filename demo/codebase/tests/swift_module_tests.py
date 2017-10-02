import logging
import unittest

import mock
from mock import Mock, MagicMock, patch
from pyramid import testing

import codebase.swift_module as swift

LOGGER = logging.getLogger(__name__)


class SwiftTests(unittest.TestCase):
    @patch('codebase.swift_module.get_auth_token')
    @patch('swiftclient.client.Connection')
    def setUp(self, mock_swift_connection, mock_get_auth_token):
        self.config = testing.setUp()
        self.auth_token = MagicMock()
        self.account_data = ([{}], [{'name': 'container1'}])
        self.container = 'container1'
        self.container_data = ([{}], [{'name': 'file1'}, {'name': 'file2'}])
        self.swift_url = 'http://0.0.0.0'
        self.setting = 'dummy setting'
        self.connection = Mock()
        mock_swift_connection.return_value = self.connection
        mock_get_auth_token.return_value = self.auth_token

        self.swift_cfg = swift.SwiftConfig(
            self.auth_token, self.swift_url, self.container)
        self.swift_cfg.connection.get_account.return_value = self.account_data

    def tearDown(self):
        testing.tearDown()

    @patch('swiftclient.client.Connection')
    def test_swift_config(self, mock_connection):
        self.assertEqual(self.swift_cfg.auth_token, self.auth_token)
        self.assertEqual(self.swift_cfg.swift_url, self.swift_url)
        self.assertEqual(self.swift_cfg.connection, self.connection)
        self.assertEqual(self.swift_cfg.container, self.container)

    @patch('swiftclient.client.Connection')
    def test_swift_config_exception(self, mock_connection):
        error_message = 'CONNECTION ERROR'
        mock_connection.side_effect = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            result = swift.SwiftConfig(
                self.auth_token, self.swift_url, self.container)
            self.assertEqual(str(cm.exception), error_message)

    def test_check_container_exception(self):
        error_message = 'GET ACCOUNT ERROR'
        self.swift_cfg.connection.get_account.side_effect \
            = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            result = swift.check_container(config=self.swift_cfg)
            self.assertEqual(str(cm.exception), error_message)
            self.assertFalse(result)

    @patch('codebase.swift_module.get_swift_config')
    def test_check_container_when_false(self, mock_get_config):
        self.swift_cfg.container = '-=#=-dummy-=#=-'
        mock_get_config.return_value = self.swift_cfg
        result = swift.check_container()
        self.assertFalse(result)

    @patch('codebase.swift_module.get_auth_token')
    @patch('swiftclient.client.Connection')
    def test_check_container_when_true(
            self, mock_swift_connection, mock_get_auth_token):
        mock_swift_connection.return_value = self.connection
        mock_get_auth_token.return_value = self.auth_token
        result = swift.check_container(config=self.swift_cfg)
        self.assertTrue(result)
        self.swift_cfg.container = '-=#=-none-=#=-'
        result = swift.check_container(config=self.swift_cfg)
        self.assertFalse(result)

    @patch('codebase.swift_module.get_swift_config')
    @patch('codebase.swift_module.check_container')
    def test_check_file_exists(self, mock_check_container, mock_get_config):
        mock_check_container.return_value = True
        mock_get_config.return_value = self.swift_cfg
        self.swift_cfg.connection.get_container = MagicMock()
        self.swift_cfg.connection.get_container.return_value = \
            self.container_data
        result = swift.check_file_exists('fileX')
        self.assertFalse(result)
        result = swift.check_file_exists('file1')
        self.assertTrue(result)

    @patch('codebase.swift_module.check_container')
    def test_check_file_exists_no_container(self, mock_check_container):
        mock_check_container.return_value = False
        result = swift.check_file_exists('filename', config=self.swift_cfg)
        self.assertFalse(result)

    @unittest.skip("on debug/troubleshooting")
    def test_ensure_container_exists(self):
        success = {'status': 200}

        def mock_put_success(container_name, response_dict):
            LOGGER.debug(
                'Called with {0} {1}'.format(container_name, response_dict))
            response_dict['status'] = success['status']

        with patch.object(
                self.swift_cfg.connection, 'get_account',
                return_value=self.account_data):
            with patch.object(
                    self.swift_cfg.connection, 'put_container',
                    side_effect=mock_put_success) as mocked_put:
                swift.ensure_container_exists(config=self.swift_cfg)
                mocked_put.assert_called()

    def test_ensure_container_exists_exception(self):
        error_message = 'PUT CONTAINER ERROR'

        with patch.object(
                self.swift_cfg.connection, 'get_account',
                return_value=self.account_data):
            with patch.object(
                    self.swift_cfg.connection, 'put_container',
                    side_effect=Exception(error_message)) as mocked_put:
                with self.assertRaises(Exception) as cm:
                    swift.ensure_container_exists(config=self.swift_cfg)
                    self.assertEqual(str(cm.exception), error_message)

    def test_get_file_contents(self):
        response = ([{}], '_filecontents')
        self.swift_cfg.connection.get_object = MagicMock()
        self.swift_cfg.connection.get_object.return_value = response
        result = swift.get_file_contents('file_name', config=self.swift_cfg)
        self.assertEqual(result, response[1])

    def test_get_file_contents_exeption(self):
        error_message = 'Exception on get object'
        self.swift_cfg.connection.get_object = MagicMock()
        self.swift_cfg.connection.get_object.side_effect = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            swift.get_file_contents('file_name', config=self.swift_cfg)
            self.assertEqual(str(cm.exception), error_message)

    def test_get_files_in_container(self):
        self.swift_cfg.connection.get_container = MagicMock()
        self.swift_cfg.connection.get_container.return_value = \
            self.container_data
        result = swift.get_files_in_container(config=self.swift_cfg)
        self.assertEqual(result, self.container_data[1])

    @patch('codebase.swift_module.settings')
    @patch('codebase.swift_module.get_auth_token')
    @patch('swiftclient.client.Connection')
    def test_get_swift_config(
            self, mock_connection, mock_get_auth_token, mock_settings):
        mock_connection.return_value = self.connection
        mock_get_auth_token.return_value = self.auth_token
        mock_settings.return_value = self.setting
        result = swift.get_swift_config()
        self.assertEqual(result.auth_token, self.auth_token)
        self.assertEqual(result.connection, self.connection)
        self.assertEqual(result.container, self.setting)
        self.assertEqual(result.swift_url, self.setting)

    @patch('mimetypes.guess_type')
    @patch('sys.getsizeof')
    def test_save_file(self, mock_getsizeof, mock_guess_type):
        success = {'status': 200}

        def mock_put_success(
                container_name, file_name, contents,
                content_length, content_type, response_dict):
            response_dict['status'] = success['status']

        mock_getsizeof.return_value = 999
        mock_guess_type.return_value = ['filetype']
        with mock.patch.object(
                self.swift_cfg.connection, 'put_object',
                side_effect=mock_put_success) as mocked_put:
            swift.check_container = MagicMock()
            swift.check_container.return_value = True
            filename = 'filename'
            contents = MagicMock()
            swift.save_file(filename, contents, config=self.swift_cfg)
            mocked_put.assert_called_with(
                self.container,
                filename, contents,
                content_length=999, content_type='filetype',
                response_dict=success)

    @patch('mimetypes.guess_type')
    @patch('sys.getsizeof')
    def test_save_file_Exception(
            self, mock_getsizeof, mock_guess_type):
        mock_getsizeof.return_value = 999
        mock_guess_type.return_value = ['filetype']
        error_message = "SWIFT PUT OBJECT ERROR"
        self.swift_cfg.connection.put_object.side_effect = \
            Exception(error_message)
        swift.check_container = MagicMock()
        swift.check_container.return_value = False
        with self.assertRaises(Exception) as cm:
            filename = 'filename'
            contents = MagicMock()
            swift.save_file(filename, contents, config=self.swift_cfg)
            self.assertEqual(str(cm.exception), error_message)
