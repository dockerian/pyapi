import json
import re
import sys
import mimetypes
import StringIO

from swiftclient import client as swift_client
from swiftclient.exceptions import ClientException

from .. api.keystone import get_auth_token
from .. utils import settings, extract_manifest_from_package

from .. logger import getLogger
logger = getLogger(__name__)


def connection(auth_token):
    """
    Get a connection to Swift
    """
    try:
        return swift_client.Connection(
            preauthurl=settings('swift_url'),
            preauthtoken=auth_token,
            retries=5,
            auth_version='1',
            insecure=True)

    except ClientException as ce:
        logger.error(
            "ClientException raised initiating a connection")
        logger.exception("Details: {0}".format(ce))
    except Exception as e:
        logger.error(
            "Exception raised initiating a connection")
        logger.exception("Details: {0}".format(e))


def verify_container_missing(swift_connection, container_name):
    """
    Determine if a named container missing in Swift
    """
    try:
        headers, container_list = swift_connection.get_account()
        for container in container_list:
            # logger.debug("--- Name: {0}".format(container['name']))
            if container['name'] == container_name:
                logger.debug('--- exists container {0}'.format(container_name))
                return False

        logger.debug('--- missing container name {0}'.format(container_name))
        return True

    except ClientException as ce:
        logger.error(
            "ClientException raised verifying container exists")
        logger.exception("Details: {0}".format(ce))
    except Exception as e:
        logger.error(
            "Exception raised verifying container exists")
        logger.exception("Details: {0}".format(e))


def ensure_addins_container_exists(swift_connection, container_name):
    """
    Ensure the Global Catalog container exists in Swift. It will be useful for
    this to happen automagically each time we deploy to a new environment.
    """

    # Determine if necessary container missing; if so, create it
    container_missing = verify_container_missing(
        swift_connection, container_name)
    if container_missing:
        try:
            response = {}
            logger.debug('--- putting container {0}...'.format(container_name))
            swift_connection.put_container(
                container_name, response_dict=response)
            logger.debug(
                "--- Container {0} created".format(container_name))
            logger.debug("--- Response {0}".format(response))

        except ClientException as ce:
            logger.error(
                "ClientException raised creating Swift container")
            logger.exception("Details: {0}".format(ce))
        except Exception as e:
            logger.error(
                "Exception raised creating Swift container")
            logger.exception("Details: {0}".format(e))


def check_file_exists(container_name, file_name):
    # Prepare to use Swift
    auth_token = get_auth_token()
    swift_connection = connection(auth_token)

    if (verify_container_missing(swift_connection, container_name)):
        return False

    result = swift_connection.get_container(
            container_name, full_listing=True)
    for file in result[1]:
        if (file['name'] == file_name):
            return True
    return False


def get_deployment_list():
    # Prepare to use Swift
    auth_token = get_auth_token()
    swift_connection = connection(auth_token)
    # Get the name of the container
    container_name = settings('swift_container')

    # Ensure the container we need exists
    ensure_addins_container_exists(swift_connection, container_name)
    # This following call returns a tuple of:
    # - response headers (dict)
    # - objects in the container (list)
    # An example of an object in the container:
    # { 'bytes': 92,
    #   'name': 'test_vendor_package.json',
    #   'content_type': 'application/json' }
    result = swift_connection.get_container(
            container_name, full_listing=True)
    logger.debug(result)

    deployment_list = []
    regex = re.compile('^deployment_(.+).json$')
    for file in result[1]:
        filename = file['name']
        re_match = regex.search(filename)
        add_flag = \
            file['content_type'] == 'application/json' and \
            re_match is not None
        if (add_flag):
            try:
                file_contents = get_file_contents(container_name, filename)
                item = json.loads(file_contents)
                deployment_list.append(item)
            except Exception:
                continue
    return deployment_list


def get_file_contents(container_name, file_name):
    """
    Function wrapper to perform 'get_object' call against Swift container
    """
    try:
        # Get an auth token, Swift connection, container name
        auth_token = get_auth_token()
        swift_connection = connection(auth_token)
        response = swift_connection.get_object(container_name, file_name)
        contents = response[1]
        return contents
    except Exception as e:
        err = "Exception on trying to get {0} from Swift.\n".format(file_name)
        logger.exception(err)
        raise


# def get_files_in_container(container_name):
#     # Prepare to use Swift
#     auth_token = get_auth_token()
#     swift_connection = connection(auth_token)
#     result = swift_connection.get_container(
#             container_name, full_listing=True)
#     return result[1]


def put_object(swift_connection, container_name, file_name, contents):
    """
    Wrapper for performing the 'put_object' against Swift
    """
    try:
        # logger.info("=== INSIDE put_object ===")
        response = {}
        swift_connection.put_object(
            container_name,
            file_name,
            contents,
            content_length=sys.getsizeof(contents),
            content_type=mimetypes.guess_type(file_name, strict=True)[0],
            response_dict=response)
        # logger.info("Response: {0}".format(vars(response)))
        return response

    except ClientException as ce:
        logger.error(
            "ClientException raised on put_object to Swift")
        logger.exception("Details: {0}".format(ce))
    except Exception as e:
        logger.error(
            "Exception raised on put_object to Swift")
        logger.exception("Details: {0}".format(e))


def save_file_contents(container_name, filename, file_contents):
    """
    Function wrapper to perform 'put_object' call against Swift container
    """
    try:
        # Get an auth token, Swift connection, container name
        auth_token = get_auth_token()
        swift_connection = connection(auth_token)
        # Ensure the container we need exists
        ensure_addins_container_exists(swift_connection, container_name)

        # Push the file contents to Swift
        response = put_object(
            swift_connection, container_name, filename, file_contents)
        logger.debug(response)
        return response
    except Exception as e:
        logger.exception(
            "Exception on trying to save file contents to Swift.\n")


def write_package(filename, filedata):
    """
    Write the package to Swift

    The package the vendor uploads will have the following contents:
        - manifest; format: json; describes the overall package and contents
        - icon/image; format: png, jpeg, gif; image to show when displaying the
          package for selection
        - application; format: .tar.gz; the Cloud Foundry application
    """
    try:
        # Get the container name
        container_name = settings('swift_container')

        # Name the external manifest to match the package name
        manifest_filename = "{0}.json".format(filename.split('.')[0])

        # Read package file contents
        file_contents = StringIO.StringIO(filedata).read()

        # Extract the manifest from the package
        manifest = extract_manifest_from_package(file_contents)

        # Prepare to use Swift
        auth_token = get_auth_token()
        swift_connection = connection(auth_token)

        # Ensure the container we need exists
        ensure_addins_container_exists(swift_connection, container_name)

        # Push the manifest file to Swift
        response = {}
        response = put_object(
            swift_connection,
            container_name,
            manifest_filename,
            manifest)

        # Push the entire package into Swift
        response = put_object(
            swift_connection,
            container_name,
            filename,
            file_contents)

        return response['status']

    except ClientException as ce:
        logger.error(
            "ClientException raised writing package to Swift container")
        logger.exception("Details:\n")
    except Exception as e:
        logger.error("Exception raised writing package to Swift container")
        logger.exception("Details:\n")
