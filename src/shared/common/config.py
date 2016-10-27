import inspect
import logging
import pyramid

logger = logging.getLogger(__name__)


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
            kwa_cfg = kwargs.get('config')
            arg_idx = _arg_index_of(original_func, 'config')
            has_arg = 0 <= arg_idx and arg_idx < len(args)
            arg_cfg = None
            if has_arg:
                arg_cfg = args[arg_idx]
            if kwa_cfg is None and arg_cfg is None:
                logger.debug('Getting config by {0}'.format(config_func))
                kwargs['config'] = config_func()
            return original_func(*args, **kwargs)

        # calls the original function with checking proper configuration
        return _checks_config_wrapper
    # returns a decorated function
    return checks_config_decorator


def settings(setting_key):
    """
    Get the value by a key in application settings (.ini file)
    """
    registry = pyramid.threadlocal.get_current_registry()
    return registry.settings.get(setting_key, None)
