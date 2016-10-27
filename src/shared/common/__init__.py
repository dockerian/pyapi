"""
# shared.common module
"""

import os, sys


def import_dir():
    up_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    add_sys_path(up_dir)


def add_sys_path(new_path):
    okay = False

    new_path = os.path.abspath(new_path)

    # ignore case on Windows platform
    if sys.platform == 'win32':
        new_path = new_path.lower()

    if os.path.exists(new_path):
        okay = True
        todo = True

        # check each path in sys.path
        for path in sys.path:
            path = os.path.abspath(path)
            if sys.platform == 'win32':
                path = path.lower()
            if new_path in (path, path + os.sep):
                todo = False

        # new_path not in sys.path yet
        if todo:
            sys.path.append(new_path)

    return okay
