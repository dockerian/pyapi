import unittest

from pyramid import testing
from mock import Mock, MagicMock, patch, mock_open

from .. utils import *
from .. logger import *
logger = getLogger(__name__)


class UtilsTests(unittest.TestCase):
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

    @patch('shutil.rmtree')
    def test_delete_directory_tree(self, mock_rmtree):
        dir_path = '/foo'
        delete_directory_tree(dir_path)
        self.assertTrue(mock_rmtree.called)

    @patch('shutil.rmtree')
    def test_delete_directory_tree_exception(self, mock_rmtree):
        error_message = "Exception on delete_directory_tree"
        mock_rmtree.side_effect = Exception(error_message)
        delete_directory_tree('/bar')
        self.assertRaises(Exception, error_message)

    @patch('shutil.rmtree')
    def test_delete_directory_tree_no_path(self, mock_rmtree):
        dir_path = ''
        delete_directory_tree(dir_path)
        self.assertFalse(mock_rmtree.called)

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
