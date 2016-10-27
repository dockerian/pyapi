import mock
import unittest
import logging

from pyramid.testing import DummyRequest, DummyResource, setUp, tearDown
from pyramid.response import Response

from .. views.catalog_views import CatalogViews

from .. logger import *
logger = getLogger(__name__)


class CatalogViewsTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

    @mock.patch('localapi.views.catalog_views.get_package_list')
    def test_index(self, mock_package_list):
        fake_response = {'status': 200,
                         'packages': [{'name': 'test'}]}
        mock_package_list.return_value = fake_response
        request = DummyRequest()
        request.context = DummyResource()

        response = CatalogViews(request).index()
        self.assertEqual(type(response), dict)
        self.assertEqual(type(response['packages']), list)
        self.assertEqual(response['status'], 200)
        self.assertEqual(response, fake_response)

    @mock.patch('localapi.views.catalog_views.get_package_list')
    def test_index_returns_404(self, mock_package_list):
        fake_response = {'status': 404, 'packages': [{}]}
        mock_package_list.return_value = fake_response
        request = DummyRequest()
        request.context = DummyResource()

        response = CatalogViews(request).index()
        self.assertEqual(type(response), dict)
        self.assertEqual(type(response['packages']), list)
        self.assertEqual(response['status'], 404)

    @mock.patch('localapi.views.catalog_views.get_package_list')
    def test_index_exception(self, mock_getlist):
        error_message = 'GET PACKAGE LIST EXCEPTION'
        mock_getlist.side_effect = Exception(error_message)
        request = DummyRequest()
        request.context = DummyResource()

        response = CatalogViews(request).index()
        self.assertEqual(response['status'], 500)
        self.assertTrue(error_message in response['errors'])
