import re
import StringIO
import shutil
import tarfile

import pyramid

from logger import getLogger
logger = getLogger(__name__)


def settings(item):
    """
    Get a reference to the settings in the .ini file
    """
    registry = pyramid.threadlocal.get_current_registry()
    return registry.settings.get(item, None)


def delete_directory_tree(dir_path):
    """
    Cleanup a directory
    """
    if (dir_path):
        try:
            logger.info('Deleting {0}'.format(dir_path))
            # Clean up working directory
            shutil.rmtree(dir_path, ignore_errors=True)
            logger.info('Deleted dir: {0}'.format(dir_path))
        except Exception as e:
            err_message = \
                'Failed to clean up working directory "{0}".\nDetails:\n{1}' \
                .format(dir_path, e)
            logger.exception(err_message)


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
