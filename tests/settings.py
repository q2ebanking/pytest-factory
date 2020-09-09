'''
settings for entire project including which plugins are needed
'''

from mock_plugin.settings import plugin_settings
from tornado_drill.settings import Settings


Settings(plugins=[plugin_settings])
