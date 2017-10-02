import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open

from .. utils import *
from common.logger import *
logger = getLogger(__name__)


class UtilsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_extract_manifest_from_package(self):
        with patch('tarfile.TarFile.open', create=True) as \
                mock_context:
            test1 = Mock()
            test1.configure_mock(name='manifest.json', content='')
            test2 = Mock()
            test2.configure_mock(name='./manifest.json', content='content')
            tarMembers = [test1, test2]
            mock_tar_package = Mock()
            mock_tar_package.getmembers.return_value = tarMembers
            mock_extractfile = Mock()
            mock_extractfile.read.return_value = test2.content
            mock_tar_package.extractfile.return_value = mock_extractfile
            mock_tar_open = MagicMock()  # return_value=mock_tar_package)
            mock_tar_open.__enter__ = MagicMock(return_value=mock_tar_package)
            mock_tar_open.__exit__ = MagicMock(return_value=False)
            mock_context.return_value = mock_tar_open
            file_contents = Mock()

            result = extract_manifest_from_package(file_contents)
            self.assertEqual(result, test2.content)
