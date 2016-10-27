import mock
import unittest
import logging

from webtest import TestApp
from pyramid.testing import setUp, tearDown, DummyRequest, DummyResource

from globalapi import main

from .. views import home_views


class HomeViewsTests(unittest.TestCase):
    def setUp(self):
        settings = {}
        app = main(settings)
        self.testapp = TestApp(app)
        self.config = setUp()

    def tearDown(self):
        tearDown()

    def test_home_views(self):
        response = self.testapp.get('/', status=200)
        self.assertEqual(response.json_body['project'], 'globalapi')

    def test_get(self):
        fake_response = {'project': 'globalapi'}
        request = DummyRequest()
        request.context = DummyResource()

        response = home_views.HomeViews(request).get()
        self.assertEqual(response.json_body, fake_response)
