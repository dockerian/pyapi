import json
import unittest

from mock import Mock, MagicMock, patch
from swiftclient.exceptions import ClientException
from pyramid.response import Response
from pyramid import testing

from .. package import *
from common.logger import getLogger
logger = getLogger(__name__)


class PackageTests(unittest.TestCase):
    def get_data(self, name):
        response = self.get_response(name)
        return response[1]

    def get_response(self, name):
        """
        Mock side_effect of get_object in swift connection API
        """
        for manifest in self.manifests:
            for key, val in manifest.iteritems():
                if name in val:
                    return ['response', json.dumps(manifest)]
        return ['response', '{}']

    def setUp(self):
        self.manifests = [
            {
                'icon': 'fooApp.jpg',
                'name': 'F00 Test',
                'package': 'foo-application.pkg',
                'tags': ['first', 'foo', 'MyApp', 'test'],
                'newTags': ['newFoo', 'newTag'],
                'subTags': {'tags': ['newFoo', 'subFoo'], 'x': 'sub'},
                'version': '1.0'},
            {
                'icon': 'barApp.jpg',
                'name': 'B@r Application',
                'package': 'bar-package.pkg',
                'tags': ['2nd', 'bartender', 'cocktail', 'blahblah'],
                'newTags': ['newBar', 'newTag'],
                'subTags': {'tags': ['newBar', 'subBar'], 'x': 'sub'},
                'version': '10.2.0'},
            ]
        self.test_data = [
            {'content_type': 'application/json', 'name': 'foo'},
            {'content_type': 'application/json', 'name': 'bar'}
            ]
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    # ========================================
    # = apply_status
    # ========================================
    def test_apply_status(self):
        src_pkgs = [{
            u'version': u'1.0', u'package': u'application.pkg',
            u'name': u'GlobalAPI Test Application',
            u'tags': [u'test', u'application', u'cloud foundry', u'cloud',
                      u'foundry'],
            u'icon': u'gerber.jpg'}]
        status = 'dummy'
        pkg_list = [{
            u'version': u'1.0', u'package': u'application.pkg',
            u'name': u'GlobalAPI Test Application',
            u'tags': [u'test', u'application', u'cloud foundry', u'cloud',
                      u'foundry'],
            u'icon': u'gerber.jpg',
            u'status': u'dummy'}]

        result = apply_status(src_pkgs, status)
        self.assertEqual(result, pkg_list)

    def test_apply_status_to_empty_package_list(self):
        src_pkgs = []
        status = 'dummy'
        pkg_list = []

        result = apply_status(src_pkgs, status)
        self.assertEqual(result, pkg_list)

    def test_apply_status_to_none_package_list(self):
        src_pkgs = None
        status = 'dummy'
        pkg_list = []

        result = apply_status(src_pkgs, status)
        self.assertEqual(result, pkg_list)

    # ========================================
    # = filter_packages
    # ========================================
    @patch('common.swift.get_file_contents')
    def test_filter_packages(self, mock_get_file):
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': 'foo'}

        result = filter_packages(files, **filters)
        self.assertEqual(result, [manifests[0]])

    @patch('common.swift.get_file_contents')
    def test_filter_packages_casesensitivity(self, mock_get_file):
        """
        Test filter function is case-insensitive
        """
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': 'FOO'}

        result = filter_packages(files, **filters)
        # Ignoring case (in current implementation); or this would fail
        self.assertEqual(result, [manifests[0]])

    @patch('common.swift.get_file_contents')
    def test_filter_packages_emptyfilters(self, mock_get_file):
        """
        Test filters with empty string or white spaces
        """
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': '  '}

        result = filter_packages(files, **filters)
        self.assertEqual(result, manifests)
        result = filter_packages(files, filters='')
        self.assertEqual(result, manifests)

    @patch('common.swift.get_file_contents')
    def test_filter_packages_name(self, mock_get_file):
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': 'bar'}

        result = filter_packages(files, **filters)
        self.assertEqual(result, [manifests[1]])

    @patch('common.swift.get_file_contents')
    def test_filter_packages_nofilters(self, mock_get_file):
        """
        Test filter function with no "filters" key
        """
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        query = {'name': 'bar'}

        result = filter_packages(files)
        self.assertEqual(result, manifests)
        result = filter_packages(files, **query)
        self.assertEqual(result, manifests)

    @patch('common.swift.get_file_contents')
    def test_filter_packages_nonefilters(self, mock_get_file):
        """
        Test filter function when filters is None
        """
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': None}

        result = filter_packages(files, **filters)
        self.assertEqual(result, manifests)

    @patch('common.swift.get_file_contents')
    def test_filter_packages_nomatch(self, mock_get_file):
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': 'No Match'}

        result = filter_packages(files, **filters)
        self.assertEqual(result, [])

    @patch('common.swift.get_file_contents')
    def test_filter_packages_outspeclist(self, mock_get_file):
        """
        Test filter won't apply on keyword in a list other than tags
        """
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': 'newFoo'}

        result = filter_packages(files, **filters)
        self.assertEqual(result, [])

    @patch('common.swift.get_file_contents')
    def test_filter_packages_tags(self, mock_get_file):
        """
        Test to filter packages by keyword in tags
        """
        files = self.test_data
        manifests = self.manifests
        mock_get_file.side_effect = self.get_data
        filters = {'filters': 'Blah'}

        result = filter_packages(files, **filters)
        self.assertEqual(result, [manifests[1]])

    # ========================================
    # = get_package
    # ========================================
    @patch('common.swift.get_file_contents')
    def test_get_package(self, mock_get_file):
        mock_get_file.return_value = 'contents'
        package_filename = 'foo.tar.gz'
        result = get_package(package_filename)
        self.assertEqual(result['file_contents'], 'contents')
        self.assertEqual(result['status'], 200)

    @patch('common.swift.get_file_contents')
    def test_get_package_exception_404(self, mock_get_file):
        error_message = 'GET_FILE_CONTENTS ClientException ERROR'
        mock_get_file.side_effect = ClientException(
                msg=error_message, http_status=404)
        with self.assertRaises(Exception) as cm:
            result = get_package('')
            self.assertRaises(ClientException, mock_get_files, error_message)
            self.assertEqual(str(cm.exception), error_message)
            self.assertEqual(result['status'], 404)

    @patch('common.swift.get_file_contents')
    def test_get_package_exception(self, mock_get_file):
        error_message = 'GET_FILE_CONTENTS ERROR'
        mock_get_file.side_effect = Exception(error_message)
        with self.assertRaises(Exception) as cm:
            result = get_package('')
            self.assertEqual(str(cm.exception), error_message)
            self.assertRaises(Exception, error_message)

    # ========================================
    # = get_package_manifests
    # ========================================
    @patch('globalapi.package.filter_packages')
    @patch('globalapi.package.apply_status')
    @patch('common.swift.get_files_in_container')
    def test_get_package_manifests(
            self, mock_get_files, mock_filter, mock_apply_status):
        packages = self.test_data
        mock_get_files.return_value = packages
        mock_filter.return_value = packages
        mock_apply_status.return_value = packages

        result = get_package_manifests()
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['packages'], packages)

    @patch('common.swift.get_files_in_container')
    def test_get_package_manifests_empty(self, mock_get_files):
        error_message = 'get_files_in_container ERROR'
        mock_get_files.return_value = []
        result = get_package_manifests()
        self.assertEqual(result['status'], 404)

    @patch('common.swift.get_files_in_container')
    def test_get_package_manifests_clientexception(self, mock_get_files):
        error_message = 'get_files_in_container ERROR'
        mock_get_files.side_effect = ClientException(
                msg=error_message, http_status=404)

        result = get_package_manifests()
        self.assertRaises(ClientException, mock_get_files, error_message)
        self.assertEqual(result['status'], 404)

    @patch('common.swift.get_files_in_container')
    def test_get_package_manifests_exception(self, mock_get_files):
        error_message = 'get_files_in_container ERROR'
        mock_get_files.side_effect = Exception(error_message)

        result = get_package_manifests()
        self.assertRaises(Exception, error_message)

    # ========================================
    # = get_package_list
    # ========================================
    @patch('globalapi.package.get_package_manifests')
    def test_get_package_list(self, mock_get_manifests):
        mock_manifests = {'status': 200,
                          'packages': [{
                            'status': 'available',
                            u'name': u'Dummy',
                            u'package': u'dummy.pkg',
                            u'tags': [u'dummy', u'application', u'cloud'],
                            u'version': u'1.0',
                            u'icon': u'dummy.jpg'}]}
        mock_get_manifests.return_value = mock_manifests

        result = get_package_list()
        self.assertEqual(result['status'], mock_manifests['status'])
        self.assertEqual(result['packages'],
                         mock_manifests['packages'])

    @patch('globalapi.package.get_package_manifests')
    def test_get_package_list_404(self, mock_get_manifests):
        mock_manifests = {'status': 404, 'data': Mock()}
        mock_get_manifests.return_value = mock_manifests

        result = get_package_list()
        self.assertEqual(result['status'], mock_manifests['status'])
        self.assertFalse('packages' in result.keys())

    @patch('globalapi.package.get_package_manifests')
    def test_get_package_list_exception(self, mock_get_manifests):
        error_message = 'get_package_manifests Exception'
        mock_get_manifests.side_effect = Exception(error)
        with self.assertRaises(Exception) as cm:
            result = get_package_list()
            self.assertEqual(str(cm.exception), error_message)

    @patch('globalapi.package.get_package_manifests')
    def test_get_package_list_exception(self, mock_getPackageManifests):
        error_message = 'GET MANIFEST ERROR'
        mock_getPackageManifests.side_effect = Exception(error_message)

        with self.assertRaises(Exception) as cm:
            result = get_package_list()
            self.assertEqual(str(cm.exception), error_message)

    @patch('globalapi.utils.extract_manifest_from_package')
    @patch('common.swift.ensure_container_exists')
    @patch('common.swift.save_object')
    def test_save_package(
            self,
            mock_save,
            mock_ensure_container,
            mock_extract_manifest):

        filedata = Mock()
        name = "thepackage/manifest.json"
        mock_save.return_value = {'status': 201}
        mock_extract_manifest.return_value = MagicMock()

        result = save_package(name, filedata)
        self.assertEqual(result['status'], 201)

    @patch('globalapi.utils.extract_manifest_from_package')
    @patch('common.swift.ensure_container_exists')
    @patch('common.swift.save_object')
    def test_save_package_exception(
            self,
            mock_save,
            mock_ensure_container,
            mock_extract_manifest):

        name = "thepackage/manifest.json"
        filedata = Mock()
        error_message = 'SAVE TO SWIFT ERROR'
        mock_ensure_container.side_effect = Exception(error_message)

        result = save_package(name, filedata)
        self.assertRaises(Exception, error_message)
