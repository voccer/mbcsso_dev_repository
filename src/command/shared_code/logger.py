## create logger with singleton instance

import os
import logging


class Logger:
    __instance = None
    __logger = None

    def __init__(self):
        if Logger.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Logger.__instance = self
            Logger.__logger = logging.getLogger()
            Logger.__logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
            Logger.__logger.info("Logger initialized")

    @staticmethod
    def get_logger():
        if Logger.__logger is None:
            Logger()
        return Logger.__logger
