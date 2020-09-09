'''
settings for entire project including which plugins are needed
'''

from tests.mock_plugin.settings import plugin_settings
from tornado_drill.framework.settings import Settings


Settings(plugin_settings=[plugin_settings])
