"""
# swift_module
"""

﻿import logging
import mimetypes
import sys

from swiftclient import client as swift_client

from config import checks_config, settings
from keystone import get_auth_token

LOGGER = logging.getLogger(__name__)


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
        try:
            return swift_client.Connection(
                preauthurl=self.swift_url,
                preauthtoken=self.auth_token,
                retries=5,
                auth_version='1',
                insecure=True)
        except Exception as e:
            err_message = "Exception raised initiating a swift connection."
            LOGGER.exception(err_message)
            raise


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
    This is a fixed/non-mockable func pointer for @check_config decorator
    """
    # LOGGER.debug('get_swift_config={0}'.format(get_swift_config))
    return get_swift_config()


# ================================================
# Swift module interfaces
# ================================================


@checks_config(config_func=_get_config)
def check_container(config=None):
    """
    Check if default container exists in Swift

    Keyword arguments:
    config -- an instance of SwiftConfig (optional, default None)
    """
    try:
        LOGGER.debug('Checking container {0}'.format(config.container))
        headers, container_list = config.connection.get_account()
        for container in container_list:
            LOGGER.debug("--- container: {0}".format(container['name']))
            if (container['name'] == config.container):
                LOGGER.debug('--- found {0}'.format(config.container))
                return True
        LOGGER.debug('--- missing container {0}'.format(config.container))
        return False
    except Exception as e:
        err_message = "Exception raised on checking container exists."
        LOGGER.exception(err_message)
        raise


@checks_config(config_func=_get_config)
def check_file_exists(file_name, config=None):
    """
    Check if specified file exists in Swift store

    Keyword arguments:
    file_name -- the name of the file to be checked in Swift store
    config -- an instance of SwiftConfig (optional, default None)
    """
    if (check_container(config=config)):
        files = get_files_in_container(config=config)
        for file in files:
            if (file['name'] == file_name):
                return True
    return False


@checks_config(config_func=_get_config)
def ensure_container_exists(config=None):
    """
    Ensure default container exists in Swift.

    Keyword arguments:
    config -- an instance of SwiftConfig (optional, default None)
    """
    container_exists = check_container(config=config)
    if (not container_exists):
        try:
            response = {}
            config.connection.put_container(
                config.container, response_dict=response)
            LOGGER.debug(
                "--- Container {0} created".format(config.container))
            LOGGER.debug("--- Response {0}".format(response))
        except Exception as e:
            err = "Exception on creating container {0}.".format(
                config.container)
            LOGGER.exception(err)
            raise


@checks_config(config_func=_get_config)
def get_file_contents(file_name, config=None):
    """
    Function wrapper to perform 'get_object' call on Swift

    Keyword arguments:
    file_name -- the name of the file in Swift store
    config -- an instance of SwiftConfig (optional, default None)
    """
    try:
        response_dict = {}
        # Response from Swift:
        #   a tuple of (response headers, the object contents)
        #   The response headers will be a dict and all header names
        #   will be in lower case.
        response = config.connection.get_object(
            config.container,
            file_name,
            response_dict=response_dict)
        file_contents = response[1]
        return file_contents
    except Exception as e:
        err = "Exception on getting {0} from Swift.".format(file_name)
        LOGGER.exception(err)
        raise


@checks_config(config_func=_get_config)
def get_files_in_container(config=None):
    """
    Get info of all files in default Swift container

    Keyword arguments:
    config -- an instance of SwiftConfig (optional, default None)
    """
    result = config.connection.get_container(
        config.container, full_listing=True)
    return result[1]


@checks_config(config_func=_get_config)
def save_file(file_name, file_contents, config=None):
    """
    Function wrapper to perform 'put_object' call Swift

    Keyword arguments:
    file_name -- the name of the file to be saved
    file_contents -- the contents of the file to be saved in Swift store
    config -- an instance of SwiftConfig (optional, default None)
    """
    try:
        # Ensure the default container exists
        ensure_container_exists(config=config)
        # Push the file contents to Swift
        response = {}
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
        config.connection.put_object(
            config.container,
            file_name,
            file_contents,
            content_length=sys.getsizeof(file_contents),
            content_type=mimetypes.guess_type(file_name, strict=True)[0],
            response_dict=response)
        return response
    except Exception as e:
        err = "Exception on saving file contents to Swift.\n"
        LOGGER.exception(err)
        raise
