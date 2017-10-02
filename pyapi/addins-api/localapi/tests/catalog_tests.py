import ast
import json
import mock
import unittest

# these are for mocking out the requests lib
import responses
import requests

from pyramid.testing import setUp, tearDown
from swiftclient.exceptions import ClientException

from .. catalog import *


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

    # ========================================
    # = build_global_catalog_url
    # ========================================
    @mock.patch('localapi.catalog.settings')
    def test_build_global_catalog_url(self, settings_mock):
        expected_url = "http://localhost/v1/catalog"
        settings_mock.return_value = "http://localhost"

        result = build_global_catalog_url()
        self.assertEqual(result, expected_url)

    # ========================================
    # = build_global_catalog_item_url
    # ========================================
    @mock.patch('localapi.catalog.settings')
    def test_build_global_catalog_item_url(self, settings_mock):
        expected_url = "http://localhost/v1/catalog_item"
        settings_mock.return_value = "http://localhost"

        result = build_global_catalog_item_url()
        self.assertEqual(result, expected_url)

    # ========================================
    # = get_available_package
    # ========================================
    @mock.patch('requests.get')
    @mock.patch('localapi.catalog.build_global_catalog_item_url')
    def test_get_available_package(self, mock_catalog_item_url, mock_requests):
        fake_response = {'status_code': 200, '_content': 'dummy_content'}
        mock_requests.return_value = fake_response

        result = get_available_package('dummy')
        self.assertEqual(result, 'dummy_content')

    @mock.patch('requests.get')
    @mock.patch('localapi.catalog.build_global_catalog_item_url')
    def test_get_available_package_missing(
            self, mock_catalog_item_url, mock_requests):
        fake_response = {'status_code': 500}
        mock_requests.return_value = fake_response

        result = get_available_package('dummy')
        self.assertEqual(result, {})

    @mock.patch('localapi.catalog.build_global_catalog_item_url')
    def test_get_available_package_exeception(
            self, mock_catalog_item_url):
        error_message = 'ERROR'
        mock_catalog_item_url.side_effect = Exception(error_message)

        get_available_package('dummy')
        self.assertRaises(Exception, error_message)

    # ========================================
    # = get_available_package_manifests
    # ========================================
    # @unittest.skip("skipping for now")
    @responses.activate
    @mock.patch('localapi.catalog.build_global_catalog_url')
    def test_get_available_package_manifests(self, mock_catalog_url):
        fake_global_api_url = 'http://example.com/v1/catalog'
        mock_catalog_url.return_value = fake_global_api_url
        fake_resp = {
            "status": 200,
            "packages": [{
                "status": "available",
                "name": "Node Env",
                "author": "foo.bar@corp.com",
                "package": "node-env.tar.gz",
                "version": "0.0",
                "tags": ["node-env", "nodejs", "foo-bar", "ALS", "helion"],
                "icon": "nodejs.png"}]}

        responses.add(
            responses.GET,
            fake_global_api_url,
            status=200,
            body=json.dumps(fake_resp),
            content_type='application/json')
        response = get_available_package_manifests()
        self.assertEqual(response['status'], 200)
        self.assertEqual(response['packages'], fake_resp['packages'])
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, fake_global_api_url)
        self.assertEqual(ast.literal_eval(
            responses.calls[0].response.text), fake_resp)

    @responses.activate
    @mock.patch('localapi.catalog.build_global_catalog_url')
    def test_get_available_package_manifests_returns_404(
            self, mock_catalog_url):
        fake_global_api_url = 'http://example.com/v1/catalog'
        mock_catalog_url.return_value = fake_global_api_url
        responses.add(responses.GET, fake_global_api_url,
                      status=404, content_type='application/json')

        resp = get_available_package_manifests()

        self.assertEqual(resp['status'], 404)
        # No need to call .json() on the response; response was sent as json
        self.assertEqual(resp['packages'], [])
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, fake_global_api_url)
        self.assertEqual(responses.calls[0].response.text, u'')

    @responses.activate
    @mock.patch('localapi.catalog.build_global_catalog_url')
    def test_get_available_package_manifests_returns_unknown_error(
            self, mock_catalog_url):
        fake_global_api_url = 'http://example.com/v1/catalog'
        mock_catalog_url.return_value = fake_global_api_url
        responses.add(responses.GET, fake_global_api_url,
                      status=401, content_type='application/json')

        resp = get_available_package_manifests()

        self.assertEqual(resp['status'], 401)
        # No need to call .json() on the response; response was sent as json
        self.assertEqual(resp['packages'], [])
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, fake_global_api_url)
        self.assertEqual(responses.calls[0].response.text, u'')

    # ========================================
    # = get_package_manifests
    # ========================================
    @mock.patch('localapi.catalog.apply_status_to_package_list')
    @mock.patch('localapi.catalog.filter_manifests')
    @mock.patch('localapi.catalog.connection')
    @mock.patch('localapi.catalog.get_auth_token')
    @mock.patch('localapi.catalog.settings')
    def test_get_package_manifests(
            self, mock_settings, mock_get_auth_token, mock_connection,
            mock_filter, mock_apply_status):
        filelist1 = [
            {'content_type': 'application/json', 'content': 'foo'},
            {'content_type': 'application/json', 'content': 'bar'},
            {'content_type': 'application/xml', 'content': 'baz'}
        ]
        filelist2 = [
            {'content_type': 'application/json', 'content': 'foo'},
            {'content_type': 'application/json', 'content': 'bar'}
        ]
        filelist3 = [{
            'content_type': 'application/json',
            'content': 'foo',
            'status': 'installed'
            }, {
            'content_type': 'application/json',
            'content': 'bar',
            'status': 'installed'}
        ]

        mock_headers = mock.Mock()
        mock_connection.get_container.return_value = [mock_headers, filelist1]
        mock_filter.return_value = filelist2
        mock_apply_status.return_value = filelist3

        result = get_package_manifests()

        self.assertEqual(result['status'], 200)
        self.assertEqual(result['packages'], filelist3)

    @mock.patch('localapi.catalog.settings')
    @mock.patch('localapi.catalog.get_auth_token')
    @mock.patch('localapi.catalog.connection')
    def test_get_package_manifests_404(
            self, mock_connection, mock_get_auth_token, mock_settings):
        error_message = 'CONNECTION ERROR'
        mock_connection.side_effect = ClientException(http_status=404,
                                                      msg=error_message)

        result = get_package_manifests()
        self.assertEqual(result['status'], 404)

    # ToDo: remove this once we remove the below ClientException in catalog.py
    @mock.patch('localapi.catalog.settings')
    @mock.patch('localapi.catalog.get_auth_token')
    def test_get_package_manifests_client_exception(
            self, mock_get_auth_token, mock_settings):
        error_message = 'ERROR'
        mock_get_auth_token.side_effect = ClientException(error_message)

        result = get_package_manifests()
        self.assertEqual(result['status'], 500)

    @mock.patch('localapi.catalog.settings')
    def test_get_package_manifests_exception(
            self, mock_settings):
        error_message = 'ERROR'
        mock_settings.side_effect = Exception(error_message)

        result = get_package_manifests()
        self.assertEqual(result['status'], 500)

    # ========================================
    # = apply_status_to_package_list
    # ========================================
    def test_apply_status_to_package_list(self):
        src_pkgs = [{'name': 'pkg1'}, {'name': 'pkg2'}]
        status = 'dummy'
        pkg_list = [{'name': 'pkg1', 'status': 'dummy'},
                    {'name': 'pkg2', 'status': 'dummy'}]

        result = apply_status_to_package_list(src_pkgs, status)
        self.assertEqual(result, pkg_list)

    # ========================================
    # = filter_manifests
    # ========================================
    def test_filter_manifests(self):
        all_data = [
          {'content': 'foo', 'content_type': 'application/json', 'name': 'a'},
          {'content': 'bar', 'content_type': 'application/json', 'name': 'b'},
          {
              'name': 'deployment_',
              'content': 'baz',
              'content_type': 'application/xml'
          }]
        bad_data = [{
            'name': 'deployment_',
            'content': 'baz',
            'content_type': 'application/xml'
            }]
        res_good = [
          {'content': 'foo', 'content_type': 'application/json', 'name': 'a'},
          {'content': 'bar', 'content_type': 'application/json', 'name': 'b'},
          ]

        result = filter_manifests(all_data)
        self.assertEqual(result, res_good)

    def test_filter_manifests_when_none(self):
        result = filter_manifests([])
        self.assertEqual(result, [])

    # ========================================
    # = get_package_list
    # ========================================
    @mock.patch('localapi.catalog.apply_status_to_package_list')
    @mock.patch('localapi.catalog.get_available_package_manifests')
    @mock.patch('localapi.catalog.get_package_manifests')
    def test_get_package_list(
            self, mock_get_manifests, mock_get_avail_manifests,
            mock_apply_status):
        pkg1 = [{'name1': 'pkg1', 'status': 'installed'}]
        pkg2 = [{'name2': 'pkg2', 'status': 'available'}]
        pkgs = [{'name1': 'pkg1', 'status': 'installed'},
                {'name2': 'pkg2', 'status': 'available'}]

        mock_ins_mnfts = {'status': 200, 'packages': pkg1}
        mock_avl_mnfts = {'status': 200, 'packages': pkg2}
        mock_all_mnfts = {'status': 200, 'packages': pkgs}

        mock_get_manifests.return_value = mock_ins_mnfts
        mock_get_avail_manifests.return_value = mock_avl_mnfts
        mock_apply_status.return_value = mock_all_mnfts

        result = get_package_list()
        # ToDo - beef up the comparison here
        # self.assertEqual(result['status'], mock_manifests['status'])
        # self.assertEqual(result, None)
        self.assertEqual(len(result['packages']),
                         len(mock_all_mnfts['packages']))

    @mock.patch('localapi.catalog.get_package_manifests')
    @mock.patch('localapi.catalog.get_available_package_manifests')
    def test_get_package_list_when_no_packages(self, mock_avail_get_manifests,
                                               mock_inst_get_manifests):
        result_not_avail = {'status': 404, 'packages': []}
        mock_avail_get_manifests.return_value = result_not_avail
        mock_inst_get_manifests.return_value = result_not_avail

        result = get_package_list()
        self.assertEqual(result['status'], 404)
        self.assertEqual(result['packages'], [])

    @mock.patch('localapi.catalog.get_package_manifests')
    @mock.patch('localapi.catalog.get_available_package_manifests')
    def test_get_package_list_when_no_available_pkgs(
            self, mock_avail_get_manifests, mock_inst_get_manifests):
        result_not_avail = {'status': 404, 'packages': []}
        installed_pkgs = {'status': 200,
                          'packages': [{
                                'name1': 'pkg1',
                                'status': 'installed'}]}

        mock_avail_get_manifests.return_value = result_not_avail
        mock_inst_get_manifests.return_value = installed_pkgs

        response = get_package_list()
        self.assertEqual(response['status'], 200)
        self.assertEqual(response['packages'],
                         installed_pkgs['packages'])

    @mock.patch('localapi.catalog.get_package_manifests')
    @mock.patch('localapi.catalog.get_available_package_manifests')
    def test_get_package_list_when_no_installed_pkgs(
            self, mock_avail_get_manifests, mock_inst_get_manifests):
        result_not_installed = {'status': 404, 'packages': []}
        available_pkgs = {'status': 200,
                          'packages': [{
                                'name1': 'pkg1',
                                'status': 'available'}]}

        mock_inst_get_manifests.return_value = result_not_installed
        mock_avail_get_manifests.return_value = available_pkgs

        response = get_package_list()

        self.assertEqual(response['status'], 200)
        self.assertEqual(response['packages'],
                         available_pkgs['packages'])

    # @patch('localapi.catalog.get_package_manifests')
    # def test_get_package_list_clientException(self, mock_get_manifests):
    #     error_message = 'get_package_manifests ClientException'
    #     mock_get_manifests.side_effect = ClientException(error)
    #
    #     result = get_package_list()
    #     self.assertRaises(ClientException, mock_get_manifests, error_message)

    @mock.patch('localapi.catalog.get_available_package_manifests')
    def test_get_package_list_exception(self, mock_avail_manifests):
        error_message = 'Exception'
        mock_avail_manifests.side_effect = Exception(error_message)

        result = get_package_list()
        self.assertEqual(result['status'], 500)
        self.assertEqual(result['packages'], [])

    # @patch('localapi.catalog.get_package_manifests')
    # def test_get_package_list_clientException(
    #           self, mock_getPackageManifests):
    #     error_message = 'GET MANIFEST ERROR'
    #     mock_getPackageManifests.side_effect = ClientException(error_message)
    #
    #     result = get_package_list()
    #     self.assertRaises(
    #           ClientException, mock_getPackageManifests, error_message)
    #
    # @patch('localapi.catalog.get_package_manifests')
    # def test_get_package_list_exception(self, mock_getPackageManifests):
    #     error_message = 'GET MANIFEST ERROR'
    #     mock_getPackageManifests.side_effect = Exception(error_message)
    #
    #     result = get_package_list()
    #     self.assertRaises(Exception, error_message)

    # ========================================
    # = install_package
    # ========================================
    @mock.patch('localapi.catalog.write_package')
    @mock.patch('localapi.catalog.get_available_package')
    def test_install_package(self, mock_get_avail_pkg, mocked_write):
        fake_fileobj = 'fake-fileobj'
        mock_get_avail_pkg.return_value = fake_fileobj

        install_package('dummy')
        mocked_write.assert_called_with('dummy', fake_fileobj)

    # ToDo - REMOVE - ClientException no longer handled in catalog module.
    # @mock.patch('localapi.catalog.write_package')
    # @mock.patch('localapi.catalog.get_available_package')
    # def test_install_package_raises_client_exception(
    #         self, mock_get_avail_pkg, mocked_write):
    #     error_message = 'ERROR'
    #     mock_get_avail_pkg.side_effect = ClientException(error_message)
    #
    #     install_package('dummy')
    #     self.assertRaises(
    #             ClientException, mock_get_avail_pkg, error_message)

    @mock.patch('localapi.catalog.write_package')
    @mock.patch('localapi.catalog.get_available_package')
    def test_install_package_raises_exception(
            self, mock_get_avail_pkg, mocked_write):
        error_message = 'ERROR'
        mock_get_avail_pkg.side_effect = Exception(error_message)

        install_package('dummy')
        self.assertRaises(Exception, error_message)
