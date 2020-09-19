'''
settings for entire project including which plugins are needed
'''

from tests.mock_plugin.settings import SETTINGS as plugin_settings
from pytest_factory.framework.settings import Settings
from pytest_factory.framework.stores import Store
from pytest_factory.mock_request_types import MockHttpRequest
from tests.app import MainHandler

default_store = Store(mock_http_server={MockHttpRequest(): 'default'})

SETTINGS = Settings(
    default_request_handler_class=MainHandler,
    plugin_settings=[plugin_settings],
    default_store=default_store,
    handler_overrides={'TODO': 'TODO'}
)
