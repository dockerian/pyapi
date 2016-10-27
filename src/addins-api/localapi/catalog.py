import requests
import traceback

from api.keystone import get_auth_token
from api.swift import connection, write_package
from swiftclient.exceptions import ClientException
from utils import settings

from logger import getLogger
logger = getLogger(__name__)


def build_global_catalog_url():
    """
    Build a URL to hit the global catalog service and do stuff with the
    catalog:
    - get an index of catalog items
    - upload an item to the catalog
    - etc.
    """
    path = "/v1/catalog"
    base_url = "{0}".format(settings('global_catalog_url'))
    return "{0}{1}".format(base_url, path)


def build_global_catalog_item_url():
    """
    Build a URL to hit the global catalog service and do stuff with
    catalog items.
    """
    path = "/v1/catalog_item"
    base_url = "{0}".format(settings('global_catalog_url'))
    return "{0}{1}".format(base_url, path)


def get_available_package(package_name):
    """
    Hit the global catalog service and retrieve a names catalog item
    """
    try:
        # This will give us something like:
        # http://0.0.0.0:8001/v1/catalog
        base_url = build_global_catalog_item_url()
        # logger.info("BASE URL: {0}".format(base_url))

        # Add the package_name parameter
        params = {'package_name': package_name}
        # logger.info("PARAMS: {0}".format(params))

        # Make an HTTP call to the global catalog service and get the package
        result = requests.get(base_url, params=params)
        # logger.info("RESULT: {0}".format(vars(result)))

        # logger.info("RESULT: {0}".format(vars(result)))
        # logger.info("Status Code: {0}".format(result.status_code))
        # if result.status_code < 300:
        if result['status_code'] < 300:
            return result['_content']
        else:
            return {}

    except Exception as e:
        logger.error(
            "Exception trying to get available package")
        logger.exception("Details: {0}".format(e))


def get_available_package_manifests():
    """
    Hit the global catalog api service and pull back a list of available
    packages.

    Returns a dict that contains:
    - 'status': HTTP status code
    - 'packages': .tar.gz of the package from Swift
    """
    try:
        # Requests Response:
        # { 'cookies': <<class 'requests.cookies.RequestsCookieJar'>[]>,
        #   '_content': '{
        #       "status": 200,
        #       "packages": [{
        #           "status": "available",
        #           "name": "Node Env",
        #           "author": "foo.bar@corp.com",
        #           "package": "node-env.tar.gz",
        #           "version": "0.0",
        #           "tags": ["node-env", "nodejs", "foo-bar", "ALS", "helion"],
        #           "icon": "nodejs.png"}]
        #   }',
        #   'headers': {
        #       'content-length': '240', 'keep-alive': 'timeout=5, max=100',
        #       'server': 'Apache/2.4.7 (Ubuntu)', 'connection': 'Keep-Alive',
        #       'date': 'Thu, 02 Jul 2015 00:31:47 GMT',
        #       'content-type': 'application/json; charset=UTF-8'},
        #   'url': u'http://10.49.57.8/v1/catalog',
        #   'status_code': 200,
        #   '_content_consumed': True,
        #   'encoding': 'UTF-8',
        #   'request': <PreparedRequest [GET]>,
        #   'connection':
        #       <requests.adapters.HTTPAdapter object at 0x7f404a202710>,
        #   'elapsed': datetime.timedelta(0, 0, 246204),
        #   'raw': <requests.packages.urllib3.response.HTTPResponse
        #       object at 0x7f404a20ff50>,
        #   'reason': 'OK',
        #   'history': []
        # }
        response = requests.get(build_global_catalog_url())

        # print("REQUESTS RESPONSE: {0}".format(str(response)))
        # print("TYPE: {0}".format(type(response)))
        # print("TO DICT: {0}".format(response.__dict__))

        if response.status_code == 404:
            return {'status': 404, 'packages': []}
        elif response.status_code == 200:
            # print "(catalog.py) --- RESPONSE: {0}".format(str(response))
            content = response.json()
            # print "(catalog.py) --- RESPONSE CONTENT: {0}".format(content)
            return {'status': response.status_code,
                    'packages': content['packages']}
        else:
            return {'status': response.status_code,
                    'packages': []}

    except Exception as e:
        logger.error(
            "Exception raised getting package list from catalog-api")
        logger.exception("Details: {0}".format(e))
        logger.exception(traceback.format_exc())
        return {'status': 500, 'packages': []}


def filter_manifests(manifests, **filters):
    manifest_list = []
    for item in manifests:
        if item['name'].startswith('deployment_'):
            continue
        if item['content_type'] == 'application/json':
            manifest_list.append(item)
    return manifest_list


def apply_status_to_package_list(data, status):
    """
    """
    dest = []
    if data is not None and len(data) > 0:
        for pkg in data:
            pkg['status'] = status
            dest.append(pkg)

    return dest


def get_package_manifests():
    """
    Get a list of package manifests

    Returns a dict that contains:
    - 'status': HTTP status code
    - 'packages': .tar.gz of the package from Swift
    """
    try:

        # Get the name of the container
        container_name = settings('swift_container')

        # Prepare to use Swift
        auth_token = get_auth_token()
        swift_connection = connection(auth_token)

        # This call returns a dict (container attrs) and
        # a list (objects in container). Example result:
        # { 'bytes': 92,
        #   'last_modified': '2015-06-13T02:53:25.788490',
        #   'hash': '421e105dda2580a39b21edeaf9b035de',
        #   'name': 'test_vendor_package.json',
        #   'content_type': '`application/json`' }
        result = swift_connection.get_container(
            container_name, full_listing=True)

        logger.info(
            "Contents of Swift container: {0}".format(result[1]))

        # filter manifests based on filter criteria passed
        filtered_manifests = filter_manifests(result[1])

        # logger.info(filtered_manifests)

        # add a 'status' attribute to each manifest
        if len(filtered_manifests) > 0:
            manifests = apply_status_to_package_list(
                filtered_manifests, 'installed')
            return {'status': 200, 'packages': manifests}
        else:
            # ToDo: This section WILL get hit once we are able to return a
            # proper 404 from the Swift layer, vs an exception.
            return {'status': 404, 'packages': []}

    # ToDo (CJ) Once the ClientException error handling can be done within the
    #           swift module, kill this.
    except ClientException as ce:
        if vars(ce)['http_status'] == 404:
            return {'status': 404, 'packages': []}
        else:
            return {'status': 500, 'packages': []}
    except Exception as e:
        msg = "Exception getting package manifests"
        logger.error(msg)
        logger.exception("Details: {0}".format(e))
        return {'status': 500, 'packages': [], 'errors': msg}


def get_package_list():
    """
    Get a list of packages

    This method gets a combined list of packages from the global catalog
    service and the local data store. The default status of each package in the
    global catalog is 'available' and the default status of each package in the
    local data store is installed. The two lists of packages are combined and
    returned to the caller.
    """
    try:
        # get a list of available packages from the global catalog service
        apm = get_available_package_manifests()
        # print "AVAIL: {0}".format(apm)

        # get a list of installed packages from the local catalog
        ipm = get_package_manifests()
        # print "INSTLD: {0}".format(ipm)

        # combine the two collections
        all_manifests = apm['packages']+ipm['packages']
        # print "ALL MANIFESTS: {0}".format(all_manifests)

        if all_manifests == []:
            return {'status': 404, 'packages': []}
        else:
            return {'status': 200, 'packages': all_manifests}

    except Exception as e:
        # if vars(e)['http_status'] == 404:
        #     return {'status': 404, 'packages': []}
        # else:
        msg = "Exception attempting to get package list from Swift"
        details = "Details: {0}".format(e)
        logger.error(msg)
        logger.exception(details)
        return {'status': 500, 'packages': [], 'errors': details}


def install_package(name):
    """
    Install a package from the global catalog into the local catalog
    """
    try:
        # get the package from the global api svc
        package_as_fileobj = get_available_package(name)

        # write the package to swift locally
        write_package(name, package_as_fileobj)

    except Exception as e:
        logger.error(
            "Exception raised attempting to install package")
        logger.exception("Details: {0}".format(e))
