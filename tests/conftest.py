# this line causes the global SETTINGS in tornado_drill.framework.settings to
# get updated by the settings defined within this project's tests.
from tests.settings import SETTINGS

# here is an example of initializing tests with just the default plugin settings
# from tests.mock_plugin.settings import *

# do nothing to initialize tests with just the tornado-drill defaults

pytest_plugins = "tornado_drill.framework.pytest"
