import functools
import logging


def log_exception(logger: logging.Logger):
    """Decorator to log all actions and exceptions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.warning("{} action successfully completed".format(func.__name__))
                return result
            except Exception as exc:
                raise Exception("{} exception occured: {} ".format(func.__name__, exc))

        return wrapper

    return decorator
