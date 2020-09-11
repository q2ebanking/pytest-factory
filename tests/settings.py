'''
settings for entire project including which plugins are needed
'''

from tests.mock_plugin.settings import SETTINGS as plugin_settings
from tornado_drill.framework.settings import Settings
from tornado_drill.framework.stores import Store
from tornado_drill.mock_request_types import MockHttpRequest
from tests.app import MainHandler

default_store = Store(mock_http_server={MockHttpRequest(): 'default'})

SETTINGS = Settings(
    default_request_handler_class=MainHandler,
    plugin_settings=[plugin_settings],
    default_store=default_store,
    handler_overrides={'TODO': 'TODO'}
)
