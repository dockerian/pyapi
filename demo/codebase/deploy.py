# deploy.py
import os
import shutil
import tempfile

from multiprocessing import Lock, Process, Queue
from batch import Batch, BatchProcess

from utils import delete_directory_tree
from logging import getLogger
logger = getLogger(__name__)


class Deployment(object):
    def __init__(
            self,
            package, cli_composer, deploy_status,
            use_package_path=False):
        """
        Initialize an instance of Deployment
        """
        import uuid
        if (use_package_path):
            self.batch = Batch(package.cwd)
        else:
            self.batch = Batch(tempfile.mkdtemp())
        self.cli_composer = cli_composer
        self.cwd = self.batch.cwd
        self.cwd_use_package_path = use_package_path
        self.deployed = False
        self.deployment_id = '{0}'.format(uuid.uuid1())
        self.deploy_status = deploy_status
        self.package = package
        self.store = deploy_status.store  # backend store
        self.started = False

    def cleanup(self):
        """
        Cleanup Deployment BatchPrcess working directory
        """
        try:
            logger.info('Deleting deployment cwd={0}'.format(self.cwd))
            # Clean up working directory
            delete_directory_tree(self.cwd)
            logger.info('Deleted deploy deployment cwd.')
        except Exception as e:
            err_message = \
                'Failed to clean up deployment cwd "{0}".' \
                .format(self.cwd)
            logger.exception(err_message)

    def deploy(self):
        """
        Start a Deployment process
        """
        if (self.started):
            err = 'Deployment {0} already started'.format(self.deployment_id)
            raise Exception(err)

        self.get_deployment_batch()

        try:
            self.started = True
            self.download_package()  # preparing package

            logger.info('Starting deployment ...')
            process = BatchProcess(self.batch, self.set_status)
            logger.debug('Batch process: {0}'.format(process))
            self.deployed = process.execute()
        except Exception as e:
            err_message = 'Exception on BatchProcess execution.'
            logger.exception(err_message)
            self.set_status('FAILED')
        else:
            logger.info('DONE deployment - {0}'.format(self.deployment_id))
        finally:
            self.cleanup()

    def download_package(self):
        if (self.cwd_use_package_path):
            self.set_status('DOWNLOADING')
            pkg_filename = self.package.file_name
            pkg_contents = store.get_file_contents(pkg_filename)
            logger.info('Downloading package {0} to {1}...'.format(
                pkg_filename, self.package.path))
            with open(self.package.path, 'w') as package_file:
                # write the package as a tar.gz into deployment cwd
                package_file.write(pkg_contents)
        return self.package.path

    def get_deployment_batch(self):
        """
        Get a batch of commands for the deployment
        """
        pkg_path = self.package.path
        pkg_name = self.package.name

        self.batch.clear()
        # add unpacking script to batch
        logger.info('Adding batch to unpack {0} from {1}'.format(
            pkg_name, pkg_path))
        self.get_package_batch()

        # add deployment script to batch
        self.batch.add('TARGET', self.cli_composer.get_target_cmd())
        self.batch.add('LOGIN', self.cli_composer.get_login_cmd())
        self.batch.add(
            'REMOVED', self.cli_composer.get_delete_cmd(pkg_name), True)
        self.batch.add('LIST', self.cli_composer.get_list_cmd())
        self.batch.add('DEPLOYED', self.cli_composer.get_push_cmd(
            pkg_name, '{0}'.format(pkg_name)))
        self.batch.add('NEWLIST', self.cli_composer.get_list_cmd())
        self.batch.add('DIR', ['ls', '-al'])

    def get_package_batch(self):
        """
        Get a batch of commands for preparing the package
        """
        dst_path = self.cwd
        src_path = self.package.path
        pkg_name = self.package.name

        # no need this copy command if package path is used as cwd
        if (not self.cwd_use_package_path):
            copy_cmd = [
                'cp', '-rf',
                '{0}'.format(src_path),
                '{0}'.format(dst_path)]
            self.batch.add('COPY', copy_cmd)

        view_cmd = [
            'tar', '-tvf',
            '{0}'.format(src_path)]
        # Assume any foo.tar.gz contains -
        #   - foo/foo.tar.gz (the package to deploy)
        #   - manifest.json
        unpack_cmd = [
            'tar', '-zxvf',
            '{0}'.format(src_path)]
        xtract_cmd = [
            'tar', '-zxvf',
            '{0}/{1}/{2}.tar.gz'.format(dst_path, pkg_name, pkg_name)]
        dir_cmd = [
            'ls', '-al',
            '{0}/{1}'.format(dst_path, pkg_name)]
        self.batch.add('PREVIEW', view_cmd)
        self.batch.add('UNPACK', unpack_cmd)
        self.batch.add('EXTRACT', xtract_cmd)
        self.batch.add('DIR', dir_cmd)

    def get_status(self):
        '''get status by self.deployment_id
        '''
        return self.deploy_status.get_status(self.deployment_id)
        # return status
        pass

    def set_status(self, status):
        '''set status by self.deployment_id
        '''
        self.deploy_status.set_status(self.deployment_id, status)
