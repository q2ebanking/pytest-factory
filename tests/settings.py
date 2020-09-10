'''
settings for entire project including which plugins are needed
'''

from tests.mock_plugin.settings import SETTINGS as plugin_settings
from tornado_drill.framework.settings import Settings
from tests.app import MainHandler


SETTINGS = Settings(
    default_request_handler_class=MainHandler,
    plugin_settings=[plugin_settings]
)
