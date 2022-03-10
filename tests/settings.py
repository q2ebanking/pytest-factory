"""
settings for entire project including which plugins are needed
"""

from tests.mock_plugin.settings import SETTINGS as adapter_settings
from pytest_factory.framework.logger import Settings
from pytest_factory.framework.stores import Store
from pytest_factory.outbound_mock_request import MockHttpRequest
from tests.app import MainHandler

init_store = Store(mock_http_server={
    MockHttpRequest(): 'default'
})

SETTINGS = Settings(
    default_request_handler_class=MainHandler,
    plugin_settings=[adapter_settings],
    init_store=init_store,
    handler_overrides={'TODO': 'TODO'}
)
pass



