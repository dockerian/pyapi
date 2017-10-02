import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open

from common.config import settings
from logging import getLogger
logger = getLogger(__name__)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @patch('pyramid.threadlocal.get_current_registry')
    def test_settings(self, mock_current_registry):
        fake_username = "username123"
        mock_response = Mock()
        mock_response.settings = {'cloud_username': fake_username}
        mock_current_registry.return_value = mock_response

        result = settings('cloud_username')
        self.assertEqual(result, fake_username)
