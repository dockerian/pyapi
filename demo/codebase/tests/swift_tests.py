import logging
import mock
import os
import StringIO
import sys
import tarfile
import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open
from swiftclient.exceptions import ClientException

from codebase.swift import Swift
logger = logging.getLogger(__name__)


class SwiftClassTests(unittest.TestCase):
    @patch('swiftclient.client.Connection')
    def setUp(self, mock_connection):
        self.config = testing.setUp()
        self.auth_token = Mock()
        self.account_data = ([{}], [{'name': 'container1'}])
        self.container = 'container1'
        self.container_data = ([{}], [{'name': 'file1'}, {'name': 'file2'}])
        self.swift_url = 'http://0.0.0.0'
        self.connection = Mock()
        # patch('codebase.swift.Swift.get_connection',
        #       return_value=self.connection
        mock_connection.return_value = self.connection
        self.swift = Swift(
            self.auth_token, self.swift_url, self.container)

    def tearDown(self):
        testing.tearDown()

    @patch('swiftclient.client.Connection')
    def test_constructor(self, mock_connection):
        self.assertEqual(self.swift.auth_token, self.auth_token)
        self.assertEqual(self.swift.swift_url, self.swift_url)
        self.assertEqual(self.swift.connection, self.connection)
        self.assertEqual(self.swift.container, self.container)

    @patch('swiftclient.client.Connection')
    def test_connection_exception(self, mock_connection):
        error_message = 'CONNECTION ERROR'
        mock_connection.side_effect = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            result = Swift(self.auth_token, self.swift_url, self.container)
            self.assertEqual(str(cm.exception), error_message)

    def test_check_container_exception(self):
        name = 'foo'
        error_message = 'PUT CONTAINER ERROR'
        self.swift.connection.get_account.side_effect \
            = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            result = self.swift.check_container()
            self.assertEqual(str(cm.exception), error_message)
            self.assertFalse(result)

    def test_check_container_when_false(self):
        self.swift.connection.get_account.return_value = self.account_data
        self.swift.container = 'dummy'
        result = self.swift.check_container()
        self.assertFalse(result)

    def test_check_container_when_true(self):
        self.swift.connection.get_account.return_value = self.account_data
        result = self.swift.check_container()
        self.assertTrue(result)

    def test_check_file_exists(self):
        self.swift.check_container = MagicMock()
        self.swift.check_container.return_value = True
        self.swift.connection.get_container = MagicMock()
        self.swift.connection.get_container.return_value = self.container_data
        result = self.swift.check_file_exists('fileX')
        self.assertFalse(result)
        result = self.swift.check_file_exists('file1')
        self.assertTrue(result)

    def test_check_file_exists_no_container(self):
        self.swift.check_container = MagicMock()
        self.swift.check_container.return_value = False
        result = self.swift.check_file_exists('filename')
        self.assertFalse(result)

    @unittest.skip("on debug/troubleshooting")
    def test_ensure_container_exists(self):
        success = {'status': 200}

        def mock_put_success(container_name, response_dict):
            logger.debug(
                'Called with {0} {1}'.format(container_name, response_dict))
            response_dict['status'] = success['status']

        with patch.object(
                self.swift.connection, 'get_account',
                return_value=self.account_data):
            with patch.object(
                    self.swift.connection, 'put_container',
                    side_effect=mock_put_success) as mocked_put:
                self.swift.ensure_container_exists()
                mocked_put.assert_called()

    def test_ensure_container_exists_exception(self):
        error_message = 'PUT CONTAINER ERROR'

        with patch.object(
                self.swift.connection, 'get_account',
                return_value=self.account_data):
            with patch.object(
                    self.swift.connection, 'put_container',
                    side_effect=Exception(error_message)) as mocked_put:
                self.swift.check_container = MagicMock()
                self.swift.check_container.return_value = False
                with self.assertRaises(Exception) as cm:
                    self.swift.ensure_container_exists()
                    self.assertEqual(str(cm.exception), error_message)

    def test_get_file_contents(self):
        response = ([{}], '_filecontents')
        self.swift.connection.get_object = MagicMock()
        self.swift.connection.get_object.return_value = response
        result = self.swift.get_file_contents('file_name')
        self.assertEqual(result, response[1])

    def test_get_file_contents_exeption(self):
        error_message = 'Exception on get object'
        self.swift.connection.get_object = MagicMock()
        self.swift.connection.get_object.side_effect = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            result = self.swift.get_file_contents('file_name')
            self.assertEqual(str(cm.exception), error_message)

    def test_get_files_in_container(self):
        self.swift.connection.get_container = MagicMock()
        self.swift.connection.get_container.return_value = self.container_data
        result = self.swift.get_files_in_container()
        self.assertEqual(result, self.container_data[1])

    @patch('mimetypes.guess_type')
    @patch('sys.getsizeof')
    def test_save_file_contents(self, mock_getsizeof, mock_guess_type):
        success = {'status': 200}

        def mock_put_success(
                container_name, file_name, contents,
                content_length, content_type, response_dict):
            response_dict['status'] = success['status']

        file_name = 'filename'
        contents = MagicMock()
        mock_getsizeof.return_value = 999
        mock_guess_type.return_value = ['filetype']
        with mock.patch.object(
                self.swift.connection, 'put_object',
                side_effect=mock_put_success) as mocked_put:
            self.swift.check_container = MagicMock()
            self.swift.check_container.return_value = True
            self.swift.save_file_contents(file_name, contents)
            mocked_put.assert_called_with(
                self.container,
                file_name, contents,
                content_length=999, content_type='filetype',
                response_dict=success)

    @patch('mimetypes.guess_type')
    @patch('sys.getsizeof')
    def test_save_file_contents_Exception(
            self, mock_getsizeof, mock_guess_type):
        file_name = 'filename'
        contents = MagicMock()
        mock_getsizeof.return_value = 999
        mock_guess_type.return_value = ['filetype']
        error_message = "SWIFT PUT OBJECT ERROR"
        self.swift.connection.put_object.side_effect = Exception(error_message)
        self.swift.check_container = MagicMock()
        self.swift.check_container.return_value = False
        with self.assertRaises(Exception) as cm:
            self.swift.save_file_contents(file_name, contents)
            self.assertEqual(str(cm.exception), error_message)
