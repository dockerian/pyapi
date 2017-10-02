import mock
import unittest

from mock import patch
from pyramid.testing import setUp, tearDown
from swiftclient.exceptions import ClientException

from .. api.swift import *


class SwiftTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

    @mock.patch('swiftclient.client.Connection')
    @mock.patch('localapi.api.swift.settings')
    def test_connection(self, settings_mock, mock_connection):
        auth_token = "HPAUTH_9787665544434434"
        fake_connection = mock.Mock()
        mock_connection.return_value = fake_connection

        result = connection(auth_token)
        self.assertEqual(result, fake_connection)

    @mock.patch('swiftclient.client.Connection')
    @mock.patch('localapi.api.swift.settings')
    def test_connection_client_exception(self, settings_mock, mock_connection):
        auth_token = "HPAUTH_9787665544434434"
        error_message = 'SWIFT CLIENT ERROR'
        mock_connection.side_effect = ClientException(error_message)

        result = connection(auth_token)
        self.assertRaises(ClientException, mock_connection, error_message)

    @mock.patch('swiftclient.client.Connection')
    @mock.patch('localapi.api.swift.settings')
    def test_connection_exception(self, settings_mock, mock_connection):
        auth_token = "HPAUTH_9787665544434434"
        error_message = 'CONNECTION ERROR'
        mock_connection.side_effect = Exception(error_message)

        result = connection(auth_token)
        self.assertRaises(Exception, error_message)

    def test_verify_container_missing_when_false(self):
        account = ([{}], [{'name': 'name1'}])
        connection = mock.Mock()
        connection.get_account.return_value = account
        test_container_name = 'name1'

        result = verify_container_missing(connection, test_container_name)
        self.assertFalse(result)

    def test_verify_container_missing_when_true(self):
        account = ([{}], [{'name': 'name1'}])
        connection = mock.Mock()
        connection.get_account.return_value = account
        test_container_name = 'dummy'

        result = verify_container_missing(connection, test_container_name)
        self.assertTrue(result)

    def test_verify_container_missing_client_exception(self):
        name = 'foo'
        connection = mock.Mock()
        error_message = 'SWIFT CLIENT ERROR'
        connection.get_account.side_effect = ClientException(error_message)

        result = verify_container_missing(connection, name)
        self.assertRaises(
            ClientException,
            connection.get_account,
            error_message)
        self.assertFalse(result)

    def test_verify_container_missing_exception(self):
        name = 'foo'
        connection = mock.Mock()
        error_message = 'PUT CONTAINER ERROR'
        connection.get_account.side_effect = Exception(error_message)

        result = verify_container_missing(connection, name)
        self.assertRaises(Exception, error_message)
        self.assertFalse(result)

    @mock.patch('swiftclient.client.Connection')
    @mock.patch('localapi.api.swift.verify_container_missing')
    def test_ensure_addins_container_exists(
            self, mock_check_container, mock_swift_connection):
        success = {'status': 200}

        def mock_put_success(container_name, response_dict):
            response_dict['status'] = success['status']

        container_name = "dummy_container_name"
        with mock.patch.object(
                mock_swift_connection, 'put_container',
                side_effect=mock_put_success) as mocked_put:
            ensure_addins_container_exists(
                mock_swift_connection,
                container_name)
        mocked_put.assert_called_with(container_name, response_dict=success)

    @mock.patch('swiftclient.client.Connection')
    @mock.patch('localapi.api.swift.verify_container_missing')
    def test_ensure_addins_container_exists_client_exception(
            self, mock_check_container, mock_swift_connection):
        container_name = "dummy_container_name"
        error_message = 'SWIFT CLIENT ERROR'

        with mock.patch.object(
                mock_swift_connection, 'put_container',
                side_effect=ClientException(error_message)) as mocked_put:
            ensure_addins_container_exists(
                mock_swift_connection,
                container_name)
        self.assertRaises(ClientException, mocked_put, error_message)

    @mock.patch('swiftclient.client.Connection')
    @mock.patch('localapi.api.swift.verify_container_missing')
    def test_ensure_addins_container_exists_exception(
            self, mock_check_container, mock_swift_connection):
        container_name = "dummy_container_name"
        error_message = 'PUT CONTAINER ERROR'

        with mock.patch.object(
                mock_swift_connection, 'put_container',
                side_effect=Exception(error_message)) as mocked_put:
            ensure_addins_container_exists(
                mock_swift_connection,
                container_name)
        self.assertRaises(Exception, error_message)

    @patch('mimetypes.guess_type')
    @patch('swiftclient.client.Connection')
    @patch('sys.getsizeof')
    def test_put_object(
            self, mock_getsizeof, mock_swift_connection, mock_guess_type):
        success = {'status': 200}

        def mock_put_success(
                container_name, file_name, contents, content_length,
                content_type, response_dict):
            response_dict['status'] = success['status']

        file_name = 'filename'
        container_name = "dummy_container_name"
        contents = mock.MagicMock()
        mock_getsizeof.return_value = 999
        mock_guess_type.return_value = ['filetype']

        with mock.patch.object(
                mock_swift_connection, 'put_object',
                side_effect=mock_put_success) as mocked_put:
            put_object(
                mock_swift_connection, container_name, file_name, contents)

        mocked_put.assert_called_with(
            container_name, file_name, contents, content_length=999,
            content_type='filetype', response_dict=success)

    @patch('mimetypes.guess_type')
    @patch('swiftclient.client.Connection')
    @patch('sys.getsizeof')
    def test_put_object_returns_client_exception(
            self, mock_getsizeof, mock_swift_connection, mock_guess_type):
        file_name = 'filename'
        container_name = "dummy_container_name"
        contents = mock.MagicMock()
        mock_getsizeof.return_value = 999
        mock_guess_type.return_value = ['application/json']
        error_message = "ERROR"
        mock_swift_connection.put_object.side_effect = ClientException(
            error_message)

        put_object(
            mock_swift_connection, container_name, file_name, contents)
        self.assertRaises(
            ClientException,
            mock_swift_connection.put_object,
            error_message)

    @patch('mimetypes.guess_type')
    @patch('swiftclient.client.Connection')
    @patch('sys.getsizeof')
    def test_put_object_returns_exception(
            self, mock_getsizeof, mock_swift_connection, mock_guess_type):
        file_name = 'filename'
        container_name = "dummy_container_name"
        contents = mock.MagicMock()
        # mock_getsizeof.return_value = 999
        # mock_guess_type.return_value = ['filetype']
        error_message = "ERROR"
        mock_swift_connection.put_object.side_effect = Exception(error_message)

        put_object(
                mock_swift_connection, container_name, file_name, contents)
        self.assertRaises(Exception, error_message)

    @mock.patch('localapi.api.keystone.get_auth_token')
    @mock.patch('localapi.api.swift.connection')
    @mock.patch('localapi.api.swift.extract_manifest_from_package')
    @mock.patch('localapi.api.swift.ensure_addins_container_exists')
    @mock.patch('localapi.api.swift.put_object')
    @mock.patch('localapi.api.swift.settings')
    def test_write_package(
            self,
            mock_settings,
            mock_put_object,
            mock_ensure_container,
            mock_extract_manifest,
            mock_connection,
            mock_get_auth_token):

        name = "thepackage/manifest.json"
        filedata = mock.Mock()
        mock_put_object.return_value = {'status': 200}

        result = write_package(name, filedata)
        self.assertEqual(result, 200)

    @mock.patch('localapi.api.keystone.get_auth_token')
    @mock.patch('localapi.api.swift.connection')
    @mock.patch('localapi.api.swift.extract_manifest_from_package')
    @mock.patch('localapi.api.swift.put_object')
    @mock.patch('localapi.api.swift.settings')
    def test_write_package_client_exception(
            self,
            mock_settings,
            mock_put_object,
            mock_extract_manifest,
            mock_connection,
            mock_get_auth_token):

        name = "thepackage/manifest.json"
        filedata = mock.Mock()
        error_message = 'SAVE TO SWIFT ERROR'
        mock_connection.side_effect = ClientException(error_message)

        result = write_package(name, filedata)
        self.assertRaises(ClientException, mock_connection, error_message)

    @mock.patch('localapi.api.swift.settings')
    def test_write_package_exception(self, mock_settings):

        name = "thepackage/manifest.json"
        filedata = mock.Mock()
        error_message = 'SAVE TO SWIFT ERROR'
        # doesn't matter what throw the exceptyion, just pick the first
        # thing in
        mock_settings.side_effect = Exception(error_message)

        result = write_package(name, filedata)
        self.assertRaises(Exception, error_message)
