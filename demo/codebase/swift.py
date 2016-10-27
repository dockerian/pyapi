import logging
import mimetypes
import sys

from config import settings
from keystone import get_auth_token
from swiftclient import client as swift_client
from swiftclient.exceptions import ClientException

logger = logging.getLogger(__name__)


class Swift():
    def __init__(self, auth_token, swift_url, container_name):
        """
        Initialize a Swift instance
        """
        self.auth_token = auth_token
        self.swift_url = swift_url
        self.container = container_name
        self.connection = self.get_connection()

    def get_connection(self):
        """
        Get a connection to Swift
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
            logger.exception(err_message)
            raise

    def check_container(self):
        """
        Determine if default container exists in Swift
        """
        try:
            logger.debug('Checking container {0}'.format(self.container))
            headers, container_list = self.connection.get_account()
            for container in container_list:
                if container['name'] == self.container:
                    return True
            return False
        except Exception as e:
            err_message = "Exception raised on checking container exists."
            logger.exception(err_message)
            raise

    def check_file_exists(self, file_name):
        if (not self.check_container()):
            return False
        files = self.get_files_in_container()
        for file in files:
            if (file['name'] == file_name):
                return True
        return False

    def check_package_exists(self, package_name):
        file_name = '{0}.tar.gz'.format(package_name)
        return self.check_file_exists(file_name)

    def ensure_container_exists(self):
        """
        Ensure default container exists in Swift.
        """
        # Determine if necessary container missing; if so, create it
        container_exists = self.check_container()
        if (not container_exists):
            try:
                response = {}
                self.connection.put_container(
                    self.container, response_dict=response)
                logger.debug(
                    "--- Container {0} created".format(self.container))
                logger.debug("--- Response {0}".format(response))
            except Exception as e:
                err = "Exception on creating container {0}.".format(
                    self.container)
                logger.exception(err)
                raise

    def get_deployment_list(self):
        deployment_list = []
        result = self.connection.get_files_in_container()
        regex = re.compile('^deployment_(.+).json$')
        for file in result:
            filename = file['name']
            re_match = regex.search(filename)
            add_flag = \
                file['content_type'] == 'application/json' and \
                re_match is not None
            if (add_flag):
                try:
                    file_contents = self.get_file_contents(filename)
                    item = json.loads(file_contents)
                    deployment_list.append(item)
                except Exception:
                    continue
        return deployment_list

    def get_file_contents(self, file_name):
        """
        Function wrapper to perform 'get_object' call on Swift
        """
        try:
            response_dict = {}
            # Response from Swift:
            #     a tuple of (response headers, the object contents)
            #     The response headers will be a dict and all header names
            #     will be lowercase.
            response = self.connection.get_object(
                self.container,
                file_name,
                response_dict=response_dict)
            file_contents = response[1]
            return file_contents
        except Exception as e:
            err = "Exception on getting {0} from Swift.".format(file_name)
            logger.exception(err)
            raise

    def get_files_in_container(self):
        result = self.connection.get_container(
            self.container, full_listing=True)
        return result[1]

    def save_file_contents(self, file_name, file_contents):
        """
        Function wrapper to perform 'put_object' call Swift
        """
        try:
            # Ensure the container we need exists
            self.ensure_container_exists()
            # Push the file contents to Swift
            response = {}
            self.connection.put_object(
                self.container,
                file_name,
                file_contents,
                content_length=sys.getsizeof(file_contents),
                content_type=mimetypes.guess_type(file_name, strict=True)[0],
                response_dict=response)
            return response
        except Exception as e:
            err = "Exception on trying to save file contents to Swift.\n"
            logger.exception(err)
            raise
