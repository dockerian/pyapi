import mock
import unittest

from pyramid import testing

from .. api.keystone import *
from .. utils import settings
from .. logger import *
logger = getLogger(__name__)


class KeystoneUtilsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('keystoneclient.v2_0.client.Client')
    @mock.patch('localapi.utils.settings')
    @mock.patch('pyramid.threadlocal.get_current_registry')
    def test_get_auth_token(self, mock_pyramid, mock_settings, mock_client):
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
        logger.debug('::: expect to raise Exception ...')

        result = get_auth_token()
        self.assertRaises(Exception, error_message)
