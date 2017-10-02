"""
# keystone
"""

﻿from logging import getLogger

from keystoneclient.v2_0 import client as keystone_client

from config import settings

LOGGER = getLogger(__name__)


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
        LOGGER.error(
            "Exception authenticating against Keystone")
        LOGGER.exception("Details: {0}".format(e))
        raise
