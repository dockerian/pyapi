import mock
import unittest
import logging

from pyramid import testing
from pyramid.testing import DummyRequest, DummyResource, setUp, tearDown
from pyramid.response import Response
from pyramid.httpexceptions import HTTPOk
from pyramid.httpexceptions import HTTPInternalServerError

from .. views.catalog_item_views import CatalogItemViews

from .. logger import *
logger = getLogger(__name__)


class CatalogItemViewsTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

    @mock.patch('localapi.views.catalog_item_views.install_package')
    def test_install(self, mock_install_package):
        fake_response = HTTPOk
        mock_install_package.return_value = fake_response

        request = DummyRequest()
        request.context = DummyResource()
        request.params['package_name'] = 'dummy'

        response = CatalogItemViews(request).install()
        self.assertEqual(response, fake_response)

    def test_install_without_package_name(self):
        request = DummyRequest()
        request.context = DummyResource()
        request.params['package_name'] = None

        response = CatalogItemViews(request).install()
        self.assertEqual(response.status_int, 500)

    @mock.patch('localapi.views.catalog_item_views.install_package')
    def test_install_exception(self, mock_install_package):
        request = testing.DummyRequest()
        request.params = {'package_name': 'test'}

        error_message = "INSTALL PACKAGE EXCEPTION"
        mock_install_package.side_effect = Exception(error_message)

        with self.assertRaises(Exception):
            CatalogItemViews(request).install()
        # self.assertTrue(error_message in response['body'])
