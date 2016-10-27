import json
import logging
import sys

from swiftclient.exceptions import ClientException

import utils
from common import swift
from common.config import settings
from common.logger import getLogger
logger = getLogger(__name__)


def apply_status(package_list, status):
    """
    Add or update status to packages in a list
    """
    dest = []
    if package_list is not None and len(package_list) > 0:
        for pkg in package_list:
            pkg['status'] = status
            dest.append(pkg)

    return dest


def filter_packages(files, **kwargs):
    """
    Get a list of package manifests by filters
    """
    keyword = ''
    manifest_list = []

    if (kwargs is not None):
        keyword = kwargs.get('filters', '')
    if (keyword):
        keyword = keyword.strip().lower()
    logger.debug('Keyword= {0}'.format(keyword))

    for file in files:
        if file['content_type'] == 'application/json':
            name = file['name']
            data = swift.get_file_contents(name)
            json_object = json.loads(data)
            logger.debug("Keyword= '{0}', Name= '{1}', Metadata= {2}".format(
                keyword, name, json_object))

            search_array = [name]
            if (keyword):
                # Expand metadata and append string item to search array
                for key, val in json_object.items():
                    if (key == "tags" and type(val) is list):
                        for item in val:
                            if (type(item) is str or type(item) is unicode):
                                search_array.append(item.lower())
                    elif (type(val) is str or type(val) is unicode):
                        search_array.append(val.lower())
                # Search keyword in array
                logger.debug('Searching in {0}'.format(search_array))
                for word in search_array:
                    if keyword in word:
                        logger.debug(
                            "Found '{0}' in '{1}'.".format(keyword, word))
                        manifest_list.append(json_object)
                        break
            else:
                logger.debug("Get manifest '{0}'.".format(name))
                manifest_list.append(json_object)

    logger.debug('Manifest list = {0}'.format(manifest_list))
    return manifest_list


def get_package(package_filename):
    """
    Get a single package from a given container in Swift

    Params:
    - package_filename (string): the package file name (e.g. pkg.tar.gz)

    Returns a dict that contains:
    - 'status': HTTP status code
    - 'headers': HTTP headers returned by Swift
    - 'file_contents': .tar.gz of the package from Swift
    """
    try:
        logger.debug(swift.get_file_contents)
        result = swift.get_file_contents(package_filename)
        return {'status': 200,
                'file_contents': result}

    except ClientException as ce:
        status = vars(ce)['http_status']
        logger.exception(ce)
        return {'status': status, 'errors': ce}
    except Exception as e:
        logger.exception(e)
        return {'status': 500, 'errors': ce}


# ToDo: fix this call such that it returns a flat result: headers are not
#       necessary and neither is the nested structure.
def get_package_list(**kwargs):
    """
    Get a list of packages
    Params:
    kwargs - params hash from the call to the public API that were passed in.
             used to pass in filter criteria.
    Result:
        Current example response from the "get_package_list" call
        {   'status': 200,
            'packages': {
                'status': 200,
                'headers': {
                    'content-length': '363',
                    'x-container-object-count': '2',
                    'accept-ranges': 'bytes',
                    'date': 'Thu, 25 Jun 2015 20:36:40 GMT',
                    'connection': 'keep-alive',
                    'x-timestamp': '1433886333.51949',
                    'x-trans-id': 'tx6ff534e1bbd9485caaa60-00558c6658',
                    'x-container-bytes-used': '20411',
                    'content-type': 'application/json; charset=utf-8'
                },
                'packages': [{
                    u'version': u'1.0',
                    u'package': u'application.pkg',
                    u'name': u'GlobalAPI Test Application',
                    u'tags': [
                        u'test', u'application', u'cloud foundry',
                        u'cloud', u'foundry'
                    ],
                    u'icon':
                    u'gerber.jpg'
                }]
            }
        }
    """
    logger.debug('======= getting package list =======')

    results = get_package_manifests(**kwargs)
    if results['status'] == 404:
        return {'status': 404}
    else:
        packages = results['packages']
        return {'status': 200, 'packages': packages}


def get_package_manifests(**kwargs):
    """
    Get a list of package manifests
    """
    try:
        # This call returns a list of objects in swift container.
        # An example of an object in the container:
        # { 'bytes': 92,
        #   'last_modified': '2015-06-13T02:53:25.788490',
        #   'hash': '421e105dda2580a39b21edeaf9b035de',
        #   'name': 'test_vendor_package.json',
        #   'content_type': 'application/json' }
        files = swift.get_files_in_container()

        filtered_manifests = filter_packages(files, **kwargs)

        if len(filtered_manifests) > 0:
            manifests = apply_status(filtered_manifests, 'available')
            return {'status': 200, 'packages': manifests}
        else:
            return {'status': 404}

    except ClientException as ce:
        status = vars(ce)['http_status']
        logger.exception(ce)
        return {'status': status, 'errors': ce}
    except Exception as e:
        logger.exception(e)
        return {'status': 500, 'errors': e}


def save_package(name, filedata):
    """
    Write the package to Swift

    The package the vendor uploads will have the following contents:
        - manifest; format: json; describes the overall package and contents
        - icon/image; format: png, jpeg, gif; image to show when displaying the
          package for selection
        - application; format: .tar.gz; the Cloud Foundry application
    """
    try:
        # Name the external manifest to match the package name
        manifest_filename = "{0}.json".format(name.split('.')[0])

        file_contents = filedata.file.read()
        manifest = utils.extract_manifest_from_package(file_contents)
        swift.ensure_container_exists()

        response = {}

        # Push the manifest file to Swift
        response = swift.save_object(manifest_filename, manifest)

        # Push the entire package into Swift
        response = swift.save_object(name, file_contents)

        return {'status': 201}

    except (ClientException, Exception):
        logger.exception("Exception saving package to Swift")
