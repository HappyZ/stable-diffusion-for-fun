import os
import unittest

from utilities.logger import Logger


class TestLogger(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.logger = Logger()
        self.log_filepath = "/tmp/test/tmplog.log"

    def test_logger_print(self):
        self.logger.set_log_output_filepath(self.log_filepath)
        self.logger.debug("A quirky message only developers care about")
        self.logger.info("Curious users might want to know this")
        self.logger.warn("Something is wrong and any user should be informed")
        self.logger.error("Serious stuff, this is red for a reason")
        self.logger.critical("OH NO everything is on fire")

        self.logger.debugging_on()

        self.logger.debug("A quirky message only developers care about")

        self.assertTrue(os.path.isfile(self.log_filepath))

    @classmethod
    def tearDownClass(self):
        if os.path.isfile(self.log_filepath):
            os.remove(self.log_filepath)


if __name__ == '__main__':
    unittest.main()
