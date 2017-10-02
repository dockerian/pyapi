import unittest

from pyramid import testing
from common.logger import getLogger, Logger


class LoggerTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_getlogger(self):
        logger = getLogger(__name__)
        self.assertEqual(logger.propagate, True)
        self.assertEqual(logger.name, __name__)

    def test_logger(self):
        logger = Logger(__name__)
        self.assertEqual(logger.propagate, True)
        self.assertEqual(logger.name, __name__)
