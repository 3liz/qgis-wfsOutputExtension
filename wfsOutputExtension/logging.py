__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import functools
import time
import traceback

from contextlib import contextmanager

from qgis.core import Qgis, QgsMessageLog

from wfsOutputExtension.definitions import PLUGIN


class Logger:

    @staticmethod
    def info(message: str):
        QgsMessageLog.logMessage(str(message), PLUGIN, Qgis.Info)

    @staticmethod
    def warning(message: str):
        QgsMessageLog.logMessage(str(message), PLUGIN, Qgis.Warning)

    @staticmethod
    def critical(message: str):
        QgsMessageLog.logMessage(str(message), PLUGIN, Qgis.Critical)

    @staticmethod
    def log_exception(e: BaseException):
        """ Log a Python exception. """
        Logger.critical(
            "Critical exception:\n{e}\n{traceback}".format(
                e=e,
                traceback=traceback.format_exc()
            )
        )


def exception_handler(func):
    """ Decorator to catch all exceptions. """
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            Logger.log_exception(e)
    return inner_function


@contextmanager
def trap():
    """ Define a trap context for catching all exceptions """
    try:
        yield
    except Exception as e:
        Logger.log_exception(e)


def log_function(func):
    """ Decorator to log function. """
    @functools.wraps(func)
    def log_function_core(*args, **kwargs):
        start = time.time()
        value = func(*args, **kwargs)
        end = time.time()
        Logger.info("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return value

    return log_function_core
