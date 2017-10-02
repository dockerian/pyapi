import os
import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open
from ..deploy.batch import Batch, BatchProcess
from ..deploy.helion_cli import HelionCliComposer
from ..logger import getLogger
logger = getLogger(__name__)


def set_status(status):
    logger.info('======= Setting status: "{0}" =======\n'.format(status))


class BatchTests(unittest.TestCase):
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
        self.batch_cwd = '~/test/batch/cwd'
        self.batch = Batch(self.batch_cwd)
        self.batchProcess = BatchProcess(self.batch, set_status)
        self.command = ['ls', '-al']

    def tearDown(self):
        testing.tearDown()

    def test_batch_constructor(self):
        cwd_path = os.path.abspath(os.path.expanduser(self.batch_cwd))
        self.assertEqual(self.batch.batch_cmds, [])
        self.assertEqual(self.batch.cwd, cwd_path)

    def test_batch_processor_constructor(self):
        self.assertEqual(self.batchProcess.batch_cmds, [])
        self.assertEqual(self.batchProcess.set_status, set_status)
        self.assertEqual(self.batchProcess.started, False)
        self.assertFalse(self.batchProcess.success)

    def test_batch_add_commend(self):
        status = 'Foo'
        self.batch.add(status, self.command)
        batch_cmds = self.batch.batch_cmds
        self.assertEqual(batch_cmds[0]['acceptError'], False)
        self.assertEqual(batch_cmds[0]['command'], self.command)
        self.assertEqual(batch_cmds[0]['cwd'], self.batch.cwd)
        self.assertEqual(batch_cmds[0]['status'], status)

    def test_batch_add_commend(self):
        status = 'Bar'
        self.batch.add(status, self.command, True)
        batch_cmds = self.batch.batch_cmds
        self.assertEqual(batch_cmds[0]['acceptError'], True)
        self.assertEqual(batch_cmds[0]['status'], status)

    def test_batch_add_commend(self):
        status = 'X'
        self.batch.add(status, self.command, True)
        self.assertEqual(self.batch.batch_cmds[0]['status'], status)
        self.batch.clear()
        self.assertEqual(self.batch.batch_cmds, [])

    @patch('subprocess.Popen')
    def test_execute(self, mock_popen):
        mock_proc = MagicMock(returncode=0)
        mock_popen.return_value = mock_proc

        status = 'Existed'
        self.batch.add(status, self.command)
        result = self.batchProcess.execute()
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_execute_acceptError(self, mock_popen):
        mock_proc = MagicMock(returncode=1)
        mock_popen.return_value = mock_proc

        status = 'Existed'
        self.batch.add(status, self.command, True)
        result = self.batchProcess.execute()
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_execute_fail(self, mock_popen):
        mock_proc = MagicMock(returncode=1)
        mock_popen.return_value = mock_proc

        status = 'Existed'
        self.batch.add(status, self.command)
        result = self.batchProcess.execute()
        self.assertFalse(result)
        pass
