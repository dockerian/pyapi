import json
import os

from datetime import datetime
from time import gmtime, strftime

from .. api.swift import get_deployment_list
from .. api.swift import get_file_contents, save_file_contents
from .. logger import getLogger
from .. utils import settings


logger = getLogger(__name__)


class DeploymentStatus:
    def __init__(self, package=None, swift=None):
        """
        Initialize an instance of DeploymentStatus
        """
        self.package = package
        self.destination = '' if package is None else package.destination
        self.package_name = 'N/A' if package is None else package.name
        self.swift = swift

    def get_all(self):
        return get_deployment_list()

    def get_deployment_filename(self, id):
        filename = 'deployment_{0}.json'.format(id)
        return filename

    def get_status(self, id):
        """
        get status record (as json object) by deployment id
        """
        result = {
            'deploy_id': id,
            'deploy_status': '',
            'datetime': '',
            'destination': self.destination,
            'history': [],
            'package': self.package_name}
        try:
            filename = self.get_deployment_filename(id)
            container_name = settings('swift_container')
            contents = get_file_contents(container_name, filename)

            if (contents):
                # logger.debug('Deployment status: {0}'.format(contents))
                result = json.loads(contents)
        except Exception as e:
            logger.exception("Failed to get status for {0}.\n".format(id))
        # logger.debug('Deployment result: {0}'.format(result))
        return result

    def set_status(self, id, status):
        """
        set status record (json file) by deployment id and status (string)
        """
        logger.info('======= Setting status: "{0}" =======\n'.format(status))

        result = self.get_status(id)

        date_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        history = result['history']
        record = '{0} ~ {1}'.format(date_time, status)
        if (type(history) is list):
            history.append(record)
        else:  # creating a history list
            history = [record]

        result['deploy_id'] = id
        result['deploy_status'] = status
        result['datetime'] = date_time
        result['destination'] = self.destination
        result['package'] = self.package_name
        result['history'] = history

        filename = self.get_deployment_filename(id)
        container_name = settings('swift_container')
        contents = json.dumps(result, sort_keys=True)
        save_file_contents(container_name, filename, contents)

        return result
