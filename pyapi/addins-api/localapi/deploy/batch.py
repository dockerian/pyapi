import json
import os
import subprocess
import threading

from .. logger import getLogger
logger = getLogger(__name__)


class Batch:
    def __init__(self, cwd):
        """
        Initialize an instance of Batch
        Params:
            cwd: current working directory (where the batch to be executed)
        """
        self.batch_cmds = []
        self.cwd = os.path.abspath(os.path.expanduser(cwd))

    def add(self, status, command, accept_error=False):
        """
        Add a command to batch, with expected status on success, and
        optionally allowing non-zero exit code by accept_error=True
        """
        self.batch_cmds.append({
            'accept_error': accept_error,
            'command': command,
            'cwd': self.cwd,
            'exit_code': 0,
            'status': status,
            'stdout': '',
        })

    def clear(self):
        self.batch_cmds = []


class BatchProcess:
    def __init__(self, batch, set_status_func):
        """
        Initialize an instance of BatchProcess
        """
        self.batch_cmds = batch.batch_cmds
        self.set_status = set_status_func
        self.started = False
        self.success = False

    def execute(self):
        """
        Start to execute a batch process
        """
        can_continue = True
        self.started = True
        self.set_status('STARTED')

        logger.info('Batch:\n{0}'.format(self.batch_cmds))
        for next_cmd in self.batch_cmds:
            logger.info('CWD=={0}'.format(next_cmd['cwd']))
            logger.info('next cmd:\n{0}'.format(
                json.dumps(next_cmd, indent=2, sort_keys=True)))
            accept_error = next_cmd['accept_error']
            cmd = next_cmd['command']
            # ToDo [zhuyux]: add timeout mechnisam
            proc = subprocess.Popen(
                cmd,
                cwd='{0}'.format(next_cmd['cwd']),
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE)
            next_cmd['stdout'] = proc.communicate()[0]
            stdout = next_cmd['stdout'].decode('string_escape')
            logger.info('stdout:\n{0}'.format(stdout))
            exit_code = proc.returncode

            if (accept_error or exit_code == 0):
                self.set_status(next_cmd['status'])
            else:
                logger.error('Exit code {0} from {1}'.format(exit_code, cmd))
                next_cmd['exit_code'] = exit_code
                can_continue = False
                break

        self.set_status('SUCCESS' if can_continue else 'FAILED')
        self.success = can_continue
        return can_continue
