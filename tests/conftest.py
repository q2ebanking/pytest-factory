import os
import pytest

from pytest_factory.logger import get_logger

from tests.app import MainHandler

# must include this line
pytest_plugins = ["pytest_factory.framework.pytest"]


logger = get_logger(__name__)


@pytest.fixture(scope="function")
def update_env_vars(monkeypatch):
    """Sets test values for environment variable and then re-sets the values
    to whatever they were before the test ran.
    """

    current_values = {
        "ENV": os.getenv("ENV", "dev"),
        "SOME_EXISTING_VAR": os.getenv("SOME_EXISTING_VAR", "not set"),
    }
    test_values = {"ENV": os.getenv("ENV", "test"), "SOME_EXISTING_VAR": "somevalue"}
    # Demo only print: here we have the real values
    logger.debug(f"Pre-patch: {os.getenv('ENV')}")
    envs = [monkeypatch.setenv(k, v) for k, v in test_values.items()]
    # Demo only print: here we have updated for the test
    logger.debug(f"Post yield: {os.getenv('ENV')}")
    yield envs
    for k, v in current_values.items():
        if v:
            os.environ[k] = v
    # Below for demo only
    logger.debug(f"Clean up: {os.getenv('ENV')}")
