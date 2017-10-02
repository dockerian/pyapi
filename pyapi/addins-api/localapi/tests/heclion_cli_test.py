import os
import unittest

from pyramid import testing
from .. deploy.helion_cli import HelionCliComposer
from .. logger import getLogger
logger = getLogger(__name__)


class HelionCliComposerTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.name_test = 'foo name'
        self.data = {
            'endpoint': 'api.0.0.0.0.xip.io',
            'username': 'user',
            'password': 'pass',
            'cwd': '~'}
        self.composer = HelionCliComposer(
            self.data['endpoint'],
            self.data['username'],
            self.data['password'],
            self.data['cwd'])

    def tearDown(self):
        testing.tearDown()

    def test_constructor(self):
        composer = HelionCliComposer(
            self.data['endpoint'],
            self.data['username'],
            self.data['password'])
        self.assertEqual(composer.endpoint, self.data['endpoint'])
        self.assertEqual(composer.username, self.data['username'])
        self.assertEqual(composer.password, self.data['password'])
        self.assertEqual(composer.cwd, None)

    def test_constructor_cwd(self):
        cwd_path = os.path.abspath(os.path.expanduser(self.data['cwd']))
        self.assertEqual(self.composer.cwd, cwd_path)

    def test_get_delete_cmd(self):
        result = self.composer.get_delete_cmd(self.name_test)
        self.assertEqual(result[-1], self.name_test)

    def test_get_list_cmd(self):
        result = self.composer.get_list_cmd()
        self.assertEqual(result[0:2], ['helion', 'list'])

    def test_get_login_cmd(self):
        result = self.composer.get_login_cmd()
        logger.debug(result)
        self.assertEqual(result[0:2], ['helion', 'login'])
        self.assertTrue(self.data['endpoint'] in result)
        self.assertTrue(self.data['username'] in result)
        self.assertTrue(self.data['password'] in result)

    def test_get_logout_cmd(self):
        result = self.composer.get_logout_cmd()
        self.assertEqual(result, ['helion', 'logout'])

    def test_get_push_cmd(self):
        path = 'test'
        result = self.composer.get_push_cmd(self.name_test, path)
        self.assertEqual(result[0:2], ['helion', 'push'])
        self.assertTrue(self.name_test in result)
        app_path = '{0}/{1}'.format(self.composer.cwd, path)
        self.assertTrue(app_path in result)

    def test_get_target_cmd(self):
        result = self.composer.get_target_cmd()
        self.assertEqual(result[0:2], ['helion', 'target'])
        self.assertEqual(result[-1], self.data['endpoint'])
