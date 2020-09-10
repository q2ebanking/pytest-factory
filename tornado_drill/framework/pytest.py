"""
pytest integration hooks

the  following functions are predefined hooks in pytest that we need to
either cancel out or modify

referenced in conftest.py defined in user's project

if defining a plugin

"""
import importlib

from _pytest.config import Config

from tornado_drill.framework.settings import SETTINGS
from tornado_drill.framework.stores import Stores


def pytest_configure(config: Config) -> None:
    # TODO find local settings file, which will point to plugin settings files,
    # if no local settings use framework settings
    # if plugin settings point to plugin settings recurse
    #
    # we are assuming no shared branches in the plugin tree
    #
    # we need to collapse these into one with more particular beating more general
    #
    try:
        local_settings = importlib.import_module('settings').SETTINGS
        SETTINGS.load(local_settings)
    except Exception as _:
        # no local settings
        pass

    Stores(default_store=SETTINGS.default_store)
