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

fixture_for_hq_esp_error_state_3