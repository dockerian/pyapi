import re
import StringIO
import tarfile

import logging
import pyramid

from common.logger import *
logger = getLogger(__name__)


def extract_manifest_from_package(file_contents):
    """
    Extract the manifest from the vendor package
    """
    # # Zipfile
    # manifest = None
    # with zipfile.ZipFile(StringIO.StringIO(file_contents)) as zipDocument:
    #     for name in zipDocument.namelist():
    #         if pattern.search(name):
    #             manifest = zipDocument.read(name)

    # regex pattern to match the manifest filename
    # - it should end with 'manifest.json'
    manifest_regex = '^.+[/]manifest.json$'
    pattern = re.compile(manifest_regex, re.IGNORECASE)

    # tarfile - https://docs.python.org/2/library/tarfile.html
    manifest = None
    with tarfile.TarFile.open(
            mode='r:gz',
            fileobj=StringIO.StringIO(file_contents)) as tar_package:
        for tarinfo in tar_package.getmembers():
            if pattern.search(tarinfo.name):
                manifest = tar_package.extractfile(tarinfo.name).read()
                # ToDo: CJ/JZ For now, we break out on the first found version
                # of this file. We should solidify this logic as requirements
                # firm up around filenames and packaging.
                break
    return manifest
