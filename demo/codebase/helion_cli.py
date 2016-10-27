# helicon_cli.py
import os


class HelionCliComposer(object):
    def __init__(self, endpoint, username, password, cwd=None):
        """
        Initialize an instance of HelionCliComposer
        """
        self.cwd = None
        if (cwd is not None):
            self.cwd = os.path.abspath(os.path.expanduser(cwd))
        self.endpoint = endpoint
        self.username = username
        self.password = password
        pass

    def get_delete_cmd(self, name):
        return [
            'helion', 'delete',
            '--target', '{0}'.format(self.endpoint),
            '-n', '{0}'.format(name)]

    def get_list_cmd(self):
        return ['helion', 'list', '--target', '{0}'.format(self.endpoint)]

    def get_login_cmd(self):
        return [
            'helion', 'login',
            '{0}'.format(self.username),
            '--credentials', 'username: {0}'.format(self.username),
            '--password', '{0}'.format(self.password),
            '--target', '{0}'.format(self.endpoint)]

    def get_logout_cmd(self):
        return ['helion', 'logout']

    def get_push_cmd(self, name, path):
        if (self.cwd is not None):
            path = '{0}/{1}'.format(self.cwd, path)
        return [
            'helion', 'push',
            '--target', '{0}'.format(self.endpoint),
            '--as', '{0}'.format(name),
            '--path', '{0}'.format(path),
            '--no-prompt']

    def get_target_cmd(self):
        return ['helion', 'target', self.endpoint]
