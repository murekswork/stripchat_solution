import functools
import logging


def log_exception(logger: logging.Logger):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.debug("{} action successfully completed".format(func.__name__))
                return result
            except Exception as exc:
                logger.warning("{} exception occured: {} ".format(func.__name__, exc))
                raise Exception("{} exception occured: {} ".format(func, exc))

        return wrapper

    return decorator
