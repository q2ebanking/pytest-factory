import os
import pytest
from pytest_factory.framework.stores import STORES

from tests.app import MainHandler

# must include this line
pytest_plugins = ["pytest_factory.framework.pytest", "tests.mock_plugin"]

# this property should only be defined once in the conftest.py hierarchy
#  if you need to support multiple handler classes please, you can pass them directly to
#  the mock_request decorator(s) at the class or method level to create hierarchies
STORES.default_handler_class = MainHandler

# this property allows you to monkeypatch methods and properties on the handler object
# immediately upon creation and prior to testing
# the keys are the name of the property to monkey patch and the value is the new property
STORES.handler_monkeypatches.update({})


# logger = logger.get_logger(__name__)

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
    print(f"Pre-patch: {os.getenv('ENV')}")
    envs = [monkeypatch.setenv(k, v) for k, v in test_values.items()]
    # Demo only print: here we have updated for the test
    print(f"Post yield: {os.getenv('ENV')}")
    yield envs
    for k, v in current_values.items():
        if v:
            os.environ[k] = v
    # Below for demo only
    print(f"Clean up: {os.getenv('ENV')}")
