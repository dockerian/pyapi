'''
# config

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com

'''
import os
import yaml
import logging
import pyramid

from base64 import b64decode

logger = logging.getLogger(__name__)

CONFIG_DEFAULT = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'config.yaml')


class _Singleton(type):
    """
    A metaclass that creates a Singleton base class when called.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """overriding __call__"""
        if cls not in cls._instances:
            cls._instances[cls] = super(
                _Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def reset(cls):
        """tear down class instances"""
        cls._instances = {}


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    """
    Singleton class
    """
    pass


class Config(Singleton):
    """
    Config class derived from Singleton
    """
    def __init__(self, config_file=CONFIG_DEFAULT):
        self.config_file = config_file
        with open(self.config_file, "r") as f:
            logger.info("reading %s", config_file)
            data = yaml.safe_load(f)
            logger.info('config: %s', str(data))
            self.settings = flatten_object(data)
            logger.info('settings: %s', str(self.settings))


def checks_config(config_func):
    """
    Get decorator to use config_func as initiator for 'config' arg

    Keyword arguments:
    config_func -- a function to get proper configuration
    """
    def checks_config_decorator(original_func):
        """
        Call decorated original_func with checking its 'config' arg

        Keyword arguments:
        func -- original function to be decorated
        """
        def _arg_index_of(func, name):
            """
            Get the index of a named arg on a func call
            """
            import inspect
            argspec = inspect.getargspec(func)
            for i in range(len(argspec[0])):
                if (argspec[0][i] == name):
                    logger.debug("argspec[0][{0}]=={1}".format(i, name))
                    return i
            return -1

        def _checks_config_wrapper(*args, **kwargs):
            """
            Check 'config' arg before calling original_func
            Call specified config_func if 'config' arg value is None.
            """
            arg_idx = _arg_index_of(original_func, 'config')
            has_arg = 0 <= arg_idx and arg_idx < len(args)
            arg_cfg = args[arg_idx] if (has_arg) else None
            kwa_cfg = kwargs.get('config')
            if (kwa_cfg is None and arg_cfg is None):
                logger.debug('Getting config by {0}'.format(config_func))
                kwargs['config'] = config_func()
            return original_func(*args, **kwargs)

        # calls the original function with checking proper configuration
        return _checks_config_wrapper
    # returns a decorated function
    return checks_config_decorator


def flatten_object(obj, result=None):
    """
    Convert an object to a flatten dictionary

    example: { "db": { "user": "bar" }} becomes {"db.user": "bar" }
    """
    if not result:
        result = {}

    def _flatten(key_obj, name=''):
        if isinstance(key_obj, dict):
            for item in key_obj:
                arg = str(name) + str(item) + '.'
                _flatten(key_obj[item], arg)
        elif isinstance(key_obj, list):
            index = 0
            for item in key_obj:
                arg = str(name) + str(index) + '.'
                _flatten(item, arg)
                index += 1
        else:
            result[name[:-1]] = key_obj

    _flatten(obj)
    return result


def get_setting(setting_key=None, default_value=''):
    """
    Get the instance by a key in application settings (config.yaml file)

    example: print setttings('mysql.database')
    """
    config = Config().settings

    if not setting_key:
        return config

    env_var = str.replace(setting_key, ".", "_").upper()
    key_val = os.environ.get(env_var, '')

    if not key_val:
        key_val = config.get(setting_key, default_value)

    return '' if key_val is None else key_val


def get_uint(key_name, default_value=0):
    """
    Get unsigned integer value for a key; otherwise, return default value.
    """
    if not key_name:
        return default_value
    try:
        key_val = str(settings(key_name))
        key_int = int(key_val) if key_val.isdigit() else 0
        return key_int if key_int > 0 else default_value
    except Exception:
        return default_value


def settings(item):
    """
    Get a reference to the settings in the .ini file
    """
    registry = pyramid.threadlocal.get_current_registry()
    return registry.settings.get(item, None)
