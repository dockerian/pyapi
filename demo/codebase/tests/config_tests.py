'''
# ConfigTests

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com

'''
import os
import unittest
from logging import getLogger

from mock import Mock, patch, mock_open
from pyramid import testing

from codebase.config import get_setting
from codebase.config import get_uint
from codebase.config import settings

logger = getLogger(__name__)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()


    @patch('codebase.config.get_setting')
    def test_get_uint(self, mock_get_setting):
        """
        test codebase.config.get_uint
        """
        mock_get_setting.return_value = ''
        result = get_uint({}, 0)
        self.assertEqual(result, 0)
        result = get_uint('', -1)
        self.assertEqual(result, -1)
        result = get_uint(None, 100)
        self.assertEqual(result, 100)
        result = get_uint('SOME_KEY', 0)
        self.assertEqual(result, 0)
        mock_get_setting.return_value = 'NaN'
        result = get_uint('SOME_KEY', 1)
        self.assertEqual(result, 1)
        mock_get_setting.return_value = '31415926'
        result = get_uint('SOME_KEY', 123456)
        self.assertEqual(result, 123456)
        mock_get_setting.return_value = '-31415926'
        result = get_uint('SOME_KEY', 123456)
        self.assertEqual(result, 123456)

    def test_get_setting(self):
        """
        test codebase.config.get_setting
        """
        data = """
        db:
            user: bar
            pass: barcode
        sys:
            users:
                - foo
                - bar
                - test
                - zoo
        """
        tests_path = os.path.dirname(os.path.realpath(__file__))
        upper_path = os.path.dirname(tests_path)
        config_dir = os.path.join(upper_path, "config.yaml")
        os.environ["DB_PORT"] = "13306"
        # reset Config singleton in order to mock with test data
        from codebase.config import Config
        Config.reset()
        with patch("__builtin__.open", mock_open(read_data=data)) as mock_file:
            allset = get_setting()
            v_none = get_setting('this.does.not.exist')
            v_port = get_setting('db.port')
            v_test = get_setting('sys.users.2')
            v_user = get_setting('db.user')
            mock_file.assert_called_with(config_dir, "r")
            self.assertEqual(allset['sys.users.0'], 'foo')
            self.assertEqual(v_port, '13306')
            self.assertEqual(v_test, 'test')
            self.assertEqual(v_user, 'bar')
            self.assertEqual(v_none, '')
        # re-initialize Config singleton
        Config.reset()
        Config()

    @patch('pyramid.threadlocal.get_current_registry')
    def test_settings(self, mock_current_registry):
        fake_username = "username123"
        mock_response = Mock()
        mock_response.settings = {'cloud_username': fake_username}
        mock_current_registry.return_value = mock_response

        result = settings('cloud_username')
        self.assertEqual(result, fake_username)
