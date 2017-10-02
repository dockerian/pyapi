import unittest
from logging import getLogger

import mock
from pyramid import testing

from codebase.keystone import *

LOGGER = getLogger(__name__)


class KeystoneTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('codebase.config.settings')
    @mock.patch('keystoneclient.v2_0.client.Client')
    @mock.patch('pyramid.threadlocal.get_current_registry')
    def test_get_auth_token(self, mock_pyramid, mock_client, mock_settings):
        fake_token = "HP_abc123abc123"
        mock_response = mock.Mock()
        mock_response.auth_ref = {'token': {'id': fake_token}}
        mock_client.return_value = mock_response

        result = get_auth_token()
        self.assertEqual(result, fake_token)

    @mock.patch('keystoneclient.v2_0.client.Client')
    def test_get_auth_token_exception(self, mock_client):
        error_message = 'FOUND ERROR'
        mock_client.side_effect = Exception(error_message)

        with self.assertRaises(Exception) as context:
            get_auth_token()
        self.assertTrue(error_message in context.exception)
