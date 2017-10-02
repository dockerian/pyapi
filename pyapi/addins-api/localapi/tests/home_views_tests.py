import mock
import unittest
import logging

from webtest import TestApp
from pyramid.testing import setUp, tearDown, DummyRequest, DummyResource

from localapi import main

from .. views.home_views import HomeViews
# from .. logger import *
# logger = getLogger(__name__)


class HomeViewsTests(unittest.TestCase):
    def setUp(self):
        settings = {}
        app = main(settings)
        self.testapp = TestApp(app)
        self.config = setUp()

    def tearDown(self):
        tearDown()

    def test_main(self):
        response = self.testapp.get('/', status=200)
        self.assertIn(b'localapi', response.body)
        pass

    def test_get(self):
        fake_response = {'project': 'localapi'}
        request = DummyRequest()
        request.context = DummyResource()

        response = HomeViews(request).get()
        self.assertEqual(response, fake_response)
