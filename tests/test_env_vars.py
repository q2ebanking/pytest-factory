import os
import pytest

from pytest_factory.framework.mall import MALL


@pytest.fixture()
def env_vars(request):
    os.unsetenv('TEST')
    yield request
    os.unsetenv('TEST')


class TestEnvVars:
    def test_env_vars(self, store):
        """
        see tests/config.ini env_vars
        """
        assert MALL.env_vars == {'TEST': '42'}
        val = os.getenv('TEST')
        assert val == "42"
