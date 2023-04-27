import logging
import os
import sys
import traceback
from colorlog import ColoredFormatter


FORMATTER_STREAM = ColoredFormatter(
    "%(asctime)s %(log_color)s%(levelname)-.1s[%(name)s] %(message)s%(reset)s"
)
FORMATTER_FILE = logging.Formatter("%(asctime)s %(levelname)-.1s. %(message)s")

VERBOSITY_V = 10
VERBOSITY_VV = 100
VERBOSITY_VVV = 1000


def touch(filepath: str):
    """
    Behaves similarly as `touch` command in Linux system.
    Creates an empty file.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        open(filepath, "a").close()
        return True
    except BaseException:
        pass
    return False


def get_func_name(offset: int = 0):
    """
    Returns the name of the caller function name.
    Offset counts the recursion - for example, offset=1 means the caller of the caller.
    """
    return sys._getframe(1 + offset).f_code.co_name


class DummyLogger:
    """
    DummyLogger does not do anything.
    """

    def __init__(self):
        pass

    def get_verbosity_value(self) -> int:
        return 0

    def set_verbosity(self, verbosity: int):
        pass

    def set_log_output_filepath(self, filepath: str, level=logging.DEBUG):
        pass

    def debugging_on(self):
        pass

    def debugging_off(self):
        pass

    def info(self, msg: str = ""):
        pass

    def error(self, msg: str = ""):
        pass

    def warn(self, msg: str = ""):
        pass

    def debug(self, msg: str = "", verbosity: int = VERBOSITY_V):
        pass

    def critical(self, msg: str = ""):
        pass


class Logger(DummyLogger):
    """
    Logger with specific format
    """

    def __init__(
        self,
        name: str = "default",
        filepath: str = "",
        verbosity: int = VERBOSITY_V,
        stream_lvl=logging.INFO,
        file_lvl=logging.DEBUG,
    ):
        self.verbosity = verbosity
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        self.__streamHandler = logging.StreamHandler()
        self.__streamHandler.setLevel(stream_lvl)
        self.__streamHandler.setFormatter(FORMATTER_STREAM)
        self.logger.addHandler(self.__streamHandler)

        self.__fileHandler = None
        if filepath and touch(filepath):
            file_handler = logging.FileHandler(filepath)
            file_handler.setLevel(file_lvl)
            file_handler.setFormatter(FORMATTER_FILE)
            self.__fileHandler = file_handler
            self.logger.addHandler(self.__fileHandler)

        self.logger.debug("log for {} started".format(name))
        self.logger.info("log output filepath: {}".format(filepath))

    def get_verbosity_value(self) -> int:
        return self.verbosity

    def set_verbosity(self, verbosity: int):
        self.verbosity = verbosity

    def set_log_output_filepath(self, filepath: str, level=logging.DEBUG):
        # remove prior one if any, only one handler would be allowed at a time
        if self.__fileHandler is not None:
            self.logger.removeHandler(self.__fileHandler)
            self.__fileHandler.close()
        if filepath and touch(filepath):
            file_handler = logging.FileHandler(filepath)
            file_handler.setLevel(level)
            file_handler.setFormatter(FORMATTER_FILE)
            self.__fileHandler = file_handler
            self.logger.addHandler(self.__fileHandler)

    def debugging_on(self):
        self.__streamHandler.setLevel(logging.DEBUG)
        self.logger.info(
            "debug msg printing is on, verbosity: {}".format(self.verbosity)
        )

    def debugging_off(self):
        self.__streamHandler.setLevel(logging.INFO)
        self.logger.info("debug msg printing is off")

    def info(self, msg="", verbosity: int = VERBOSITY_V):
        """
        Showing info message.
        @param msg: the message
        @param verbosity: the higher the number is, the less important it is.
        """
        if verbosity > self.verbosity:
            return
        self.logger.info("[{}] {}".format(get_func_name(offset=1), msg))

    def warn(self, msg="", verbosity: int = VERBOSITY_V):
        """
        Showing warning message.
        @param msg: the message
        @param verbosity: the higher the number is, the less important it is.
        """
        if verbosity > self.verbosity:
            return
        self.logger.warning("[{}] {}".format(get_func_name(offset=1), msg))

    def debug(self, msg: str = "", verbosity: int = VERBOSITY_V):
        """
        Showing debug message.
        @param msg: the message
        @param verbosity: the higher the number is, the less important it is.
        """
        if verbosity > self.verbosity:
            return
        self.logger.debug("[{}] {}".format(get_func_name(offset=1), msg))

    def error(self, msg=""):
        """
        Showing error message.
        @param msg: the message
        """
        self.logger.error("[{}] {}".format(get_func_name(offset=1), msg))
        self.logger.error(traceback.format_exc())

    def critical(self, msg=""):
        """
        Showing critical message.
        @param msg: the message
        """
        self.logger.critical("[{}] {}".format(get_func_name(offset=1), msg))
