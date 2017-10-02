import os
import unittest

from pyramid import testing
from .. deploy.package import Package
from .. logger import getLogger
logger = getLogger(__name__)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

        self.pkg_name = 'package name'
        self.filename = '{0}.tar.gz'.format(self.pkg_name)
        self.cwd_path = '/foo/bar'
        self.pkg_path = '{0}/{1}'.format(self.cwd_path, self.filename)
        self.endpoint = 'http://api.0.0.0.0.xip.io/'
        self.dest_url = 'http://{0}.0.0.0.0.xip.io'.format(self.pkg_name)
        self.manifest = '{0}.json'.format(self.pkg_name)
        self.package1 = Package(self.pkg_name, self.pkg_path, self.endpoint)
        self.package2 = Package(self.pkg_name, self.pkg_path)

    def tearDown(self):
        testing.tearDown()

    def test_constructor1(self):
        self.assertEqual(self.package1.id, self.pkg_name)
        self.assertEqual(self.package1.file_name, self.filename)
        self.assertEqual(self.package1.name, self.pkg_name)
        self.assertEqual(self.package1.path, self.pkg_path)
        self.assertEqual(self.package1.destination, self.dest_url)
        self.assertEqual(self.package1.cwd, self.cwd_path)

    def test_constructor2(self):
        self.assertEqual(self.package2.id, self.pkg_name)
        self.assertEqual(self.package2.file_name, self.filename)
        self.assertEqual(self.package2.name, self.pkg_name)
        self.assertEqual(self.package2.path, self.pkg_path)
        self.assertEqual(self.package2.destination, '')
        self.assertEqual(self.package2.cwd, self.cwd_path)

    def test_get_package_manifest_filename(self):
        result1 = self.package1.get_package_manifest_filename()
        self.assertEqual(result1, self.manifest)

        result2 = self.package2.get_package_manifest_filename()
        self.assertEqual(result2, self.manifest)
