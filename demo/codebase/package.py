"""
﻿# package.py
"""

import os
import re
from logging import getLogger

logger = getLogger(__name__)


class Package(object):
    def __init__(self, package_id, package_path, endpoint_url=None):
        """
        Initialize an instance of Package
        Params:
            package_id: package id or name
            package_path: full path of the package (including file name)
        """
        self.id = package_id
        self.file_name = os.path.basename(package_path)
        self.name = self.get_package_name(package_path)
        self.path = os.path.abspath(os.path.expanduser(package_path))
        self.destination = self.get_destination(endpoint_url, self.name)
        self.cwd = os.path.dirname(self.path)

    def get_destination(self, endpoint_url, package_name):
        """
        Get package destination url from endpoint and package name
        """
        dest = ''
        if (endpoint_url):
            regex = re.compile('^(http[s]?://)api\.(.+)$')
            re_match = regex.search(endpoint_url.strip('/'))
            if (re_match is not None):
                prot = re_match.group(1)
                addr = re_match.group(2)
                dest = '{0}{1}.{2}'.format(prot, package_name, addr)
        # returning package destination url
        return dest

    def get_package_manifest_filename(self):
        """
        Get package manifest filename (e.g. foo.json) without path
        """
        return '{0}.json'.format(self.name)

    def get_package_name(self, package_path):
        """
        Get package name (e.g. foo) from package path (e.g. '/path/foo.tar.gz')
        """
        pkg_file = os.path.basename(package_path)
        pkg_name = os.path.splitext(os.path.splitext(pkg_file)[0])[0]
        return pkg_name
