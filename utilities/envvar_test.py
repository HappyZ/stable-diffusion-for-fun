import os
import unittest

from utilities.envvar import get_env_var
from utilities.envvar import get_env_var_with_default
from utilities.envvar import get_env_vars


class TestEnvVar(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.key = "TEST_ENV_VAR"
        self.value = "1234"
        os.environ[self.key] = self.value

    def test_existed_vars(self):
        env_vars = get_env_vars()
        self.assertTrue(self.key in env_vars)
        self.assertTrue(get_env_var(self.key) == self.value)

    def test_nonexisted_vars(self):
        nonexist_key = "TEST_ENV_VAR_RANDOM_STUFF"
        self.assertTrue(get_env_var(nonexist_key) is None)
        self.assertTrue(get_env_var_with_default(
            nonexist_key, nonexist_key) == nonexist_key)

    @classmethod
    def tearDownClass(self):
        del os.environ[self.key]


if __name__ == '__main__':
    unittest.main()
