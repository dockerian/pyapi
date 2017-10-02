import logging
import mimetypes
import sys

from config import checks_config, settings
from keystone import get_auth_token
from swiftclient import client as swift_client
from swiftclient.exceptions import ClientException

from logger import getLogger
logger = getLogger(__name__)


# ================================================
# Swift configuration class
# ================================================
class SwiftConfig(object):
    def __init__(self, auth_token, swift_url, container_name):
        """
        Initialize a Swift configuration instance
        """
        self.auth_token = auth_token
        self.swift_url = swift_url
        self.container = container_name
        self.connection = self._get_connection()

    def _get_connection(self):
        """
        Get a connection to Swift object store
        """
        return swift_client.Connection(
            preauthurl=self.swift_url,
            preauthtoken=self.auth_token,
            retries=5,
            auth_version='1',
            insecure=True)


# ================================================
# Swift configuration initialization
# ================================================
def get_swift_config():
    """
    Get a SwiftConfig instance per application settings
    """
    auth_token = get_auth_token()
    container = settings('swift_container')
    swift_url = settings('swift_url')
    swift_cfg = SwiftConfig(auth_token, swift_url, container)
    return swift_cfg


def _get_config():
    """
    This is a fixed/non-mockable func pointer for @checks_config decorator
    """
    return get_swift_config()

# ================================================
# Swift module interfaces
# ================================================

@checks_config(config_func=_get_config)
def check_container_missing(config=None):
    """
    Check if default container missing in Swift

    Keyword arguments:
    config -- an instance of SwiftConfig (optional, default None)
    """
    try:
        logger.debug('Checking container {0}'.format(config.container))
        headers, container_list = config.connection.get_account()
        for container in container_list:
            logger.debug("--- container: {0}".format(container['name']))
            if (container['name'] == config.container):
                logger.debug('--- found {0}'.format(config.container))
                return False
        logger.debug('--- missing container {0}'.format(config.container))
        return True
    except (ClientException, Exception):
        logger.exception("Exception verifying container exists.")
        raise


@checks_config(config_func=_get_config)
def ensure_container_exists(config=None):
    """
    Ensure default container exists in Swift.

    Keyword arguments:
    config -- an instance of SwiftConfig (optional, default None)
    """
    # Determine if necessary container missing; if so, create it
    container_missing = check_container_missing(config=config)
    if (container_missing):
        try:
            response = {}
            config.connection.put_container(
                config.container, response_dict=response)
            logger.debug(
                "--- Container {0} created".format(config.container))
            logger.debug("--- Response {0}".format(response))
        except (ClientException, Exception):
            msg = "Exception creating container {0}.".format(config.container)
            logger.exception(msg)
            raise


# ToDo - CJ - Change this back to 'read_object'
@checks_config(config_func=_get_config)
def get_file_contents(file_name, config=None):
    """
    Function wrapper to perform 'get_object' call on Swift

    Keyword arguments:
    file_name -- the name of the file in Swift store
    config -- an instance of SwiftConfig (optional, default None)
    """
    response_dict = {}
    try:
        # Response from Swift:
        #     a tuple of (response headers, the object contents)
        #     The response headers will be a dict and all header names
        #     will be lowercase.
        response = config.connection.get_object(
            config.container,
            file_name,
            response_dict=response_dict)
        file_contents = response[1]
        return file_contents
    except (ClientException, Exception):
        msg = "Exception getting object {0} from Swift.".format(file_name)
        logger.exception(msg)
        raise


@checks_config(config_func=_get_config)
def get_files_in_container(config=None):
    """
    Get info of all files in default Swift container

    Keyword arguments:
    config -- an instance of SwiftConfig (optional, default None)
    """
    # This call returns a tuple of:
    # - response headers (dict)
    # - objects in the container (list)
    # An example of an object in the container:
    # { 'bytes': 92,
    #   'last_modified': '2015-06-13T02:53:25.788490',
    #   'hash': '421e105dda2580a39b21edeaf9b035de',
    #   'name': 'test_vendor_package.json',
    #   'content_type': 'application/json' }
    result = config.connection.get_container(
        config.container, full_listing=True)
    return result[1]


@checks_config(config_func=_get_config)
def save_object(name, contents, config=None):
    """
    Function wrapper to perform 'put_object' call Swift

    Keyword arguments:
    name -- the name of the file to be saved
    contents -- the contents of the file to be saved in Swift store
    config -- an instance of SwiftConfig (optional, default None)
    """
    try:
        # Ensure the container we need exists
        ensure_container_exists(config=config)
        # Push the file contents to Swift
        # Example of response from put_object call -
        # {
        #     'status': 201,
        #     'headers': {
        #         'content-length': '0',
        #         'last-modified': 'Fri, 17 Jul 2015 04:43:56 GMT',
        #         'connection': 'keep-alive',
        #         'etag': 'd41d8cd98f00b204e9800998ecf8427e',
        #         'x-trans-id': 'txeddbca07d8e744deae343-0055a8880c',
        #         'date': 'Fri, 17 Jul 2015 04:43:57 GMT',
        #         'content-type': 'text/html; charset=UTF-8'},
        #     'reason': 'Created',
        #     'response_dicts': [{
        #         'status': 201,
        #         'headers': {
        #             'content-length': '0',
        #             'last-modified':
        #             'Fri, 17 Jul 2015 04:43:56 GMT',
        #             'connection': 'keep-alive',
        #             'etag': 'd41d8cd98f00b204e9800998ecf8427e',
        #             'x-trans-id': 'txeddbca07d8e744deae343-0055a8880c',
        #             'date': 'Fri, 17 Jul 2015 04:43:57 GMT',
        #             'content-type': 'text/html; charset=UTF-8'},
        #             'reason': 'Created'}]}
        # Note: somehow 'content-length' is 0
        response = {}
        config.connection.put_object(
            config.container,
            name,
            contents,
            content_length=sys.getsizeof(contents),
            content_type=mimetypes.guess_type(name, strict=True)[0],
            response_dict=response)
        logger.debug(response)
        return response
    except (ClientException, Exception):
        msg = "Exception saving object to Swift.\n"
        logger.exception(msg)
        raise
