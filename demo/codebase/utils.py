"""
﻿# utils.py
"""

import StringIO
import re
import shutil
import tarfile
from logging import getLogger

from swift_class import Swift

from keystone import get_auth_token

LOGGER = getLogger(__name__)


def delete_directory_tree(dir_path):
    """
    Cleanup a directory
    """
    if (dir_path):
        try:
            LOGGER.info('Deleting {0}'.format(dir_path))
            # Clean up working directory
            shutil.rmtree(dir_path, ignore_errors=True)
            LOGGER.info('Deleted dir: {0}'.format(dir_path))
        except Exception as e:
            err_message = \
                'Failed to clean up working directory "{0}".' \
                .format(dir_path)
            LOGGER.exception(err_message)


def extract_manifest_from_package(file_contents):
    """
    Extract the manifest from the vendor package
    """
    manifest_regex = '^.+[/]manifest.json$'
    pattern = re.compile(manifest_regex, re.IGNORECASE)

    # tarfile - https://docs.python.org/2/library/tarfile.html
    manifest = None
    with tarfile.TarFile.open(
            mode='r:gz',
            fileobj=StringIO.StringIO(file_contents)) as tar_package:
        for tarinfo in tar_package.getmembers():
            if (pattern.search(tarinfo.name)):
                manifest = tar_package.extractfile(tarinfo.name).read()
                break
    return manifest


def get_store():
    """
    Get a Swift instance per application settings
    """
    auth_token = get_auth_token()
    container = settings('swift_container')
    swift_url = settings('swift_url')
    swift = Swift(auth_token, swift_url, container)
    return swift
