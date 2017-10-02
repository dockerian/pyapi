from keystoneclient.v2_0 import client as keystone_client

from .. utils import settings

from .. logger import getLogger
logger = getLogger(__name__)


def get_auth_token():
    """
    Get an auth token from Keystone.
    """
    try:
        keystone = keystone_client.Client(
            username=settings('cloud_username'),
            password=settings('cloud_password'),
            tenant_name=settings('cloud_project_name'),
            auth_url=settings('cloud_auth_url'),
            insecure=True)
        return keystone.auth_ref['token']['id']
    except Exception as e:
        logger.error(
            "!!! Base Exception raised on authentication against Keystone")
        logger.exception("!!! Details: {0}".format(e))
