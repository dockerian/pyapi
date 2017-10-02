import json
import shutil
import tempfile
import traceback

from multiprocessing import Process
from subprocess import call, check_output, CalledProcessError

from api import swift
from utils import settings, delete_directory_tree

from deploy.deploy import Deployment
from deploy.deploy_status import DeploymentStatus
from deploy.helion_cli import HelionCliComposer
from deploy.package import Package

from catalog import get_available_package

from logger import getLogger
logger = getLogger(__name__)


def check_package_exists(package_name):
    container = settings('swift_container')
    file_name = '{0}.tar.gz'.format(package_name)
    return swift.check_file_exists(container, file_name)


def deploy_package(package_name, endpoint_url, username, password):
    """
    Deploy a package into destination (e.g. ALS/Cloud Foundry)
    Params:
        package_name - the name of the package to deploy
        endpoint_url - the destination (e.g. ALS/Cloud Foundry) endpoint URL
                       ie: 'https://api.15.126.129.33.xip.io'
        username - the user name (admin email) for destination login
        password - the password for destination login
    """
    if (not check_package_exists(package_name)):
        return {'status': 404}

    cwd = ''
    try:
        # ToDo [zhuyux]: using factory to get package
        cwd = tempfile.mkdtemp()
        pkg_filename = '{0}.tar.gz'.format(package_name)
        package_path = '{0}/{1}'.format(cwd, pkg_filename)
        package = Package(package_name, package_path, endpoint_url)

        # instantiate a cli composer
        composer = HelionCliComposer(endpoint_url, username, password)

        deploy_status = DeploymentStatus(package)
        deployment = Deployment(package, composer, deploy_status, True)
        deployment_id = deployment.deployment_id

        deployment.set_status('INIT')

        # Start a new process to execute the deployment
        process = Process(
            name='deployment_{0}'.format(deployment_id),
            target=deployment.deploy)
        process.start()

        logger.info('Deployment {0} started for {1}.'.format(
            deployment_id, package_name))

        return {
            'status': 202,
            'deployment_id': deployment_id,
            'package': package_name}

    except Exception as e:
        stack_info = traceback.format_exc()
        error_message = "Exception on deploy {0}. Details:\n{1}".format(
            package_name, stack_info)
        logger.exception(error_message)
        delete_directory_tree(cwd)
        return {'status': 500, 'errors': error_message}


def get_status(id):
    """
    Get the deployment status by id
    """
    try:
        logger.info("======= deployment::get_status =======")

        deploy_status = DeploymentStatus()
        result = deploy_status.get_status(id)

        logger.debug('Deployment result: {0}'.format(result))
        if result == {} or not result['deploy_status']:
            return {'status': 404}
        else:
            return {'status': 200, 'data': result}
    except Exception as e:
        stack_info = traceback.format_exc()
        error = "Exception on getting deployment status"
        error_message = "{0} for {1}. Details:\n{2}".format(
            error, id, stack_info)
        logger.exception(error_message)
        return {'status': 500, 'errors': error_message}
