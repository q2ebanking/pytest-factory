import os
os.unsetenv('TEST')


class TestEnvVars:
    def test_env_vars(self, store):
        """
        see tests/config.ini env_vars
        """
        val = os.getenv('TEST')
        assert val == "42"
