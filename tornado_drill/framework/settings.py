"""
define as class with required and optional fields.

once loaded as dict, define as starting fixtures for entire project that can
then be overridden by redefinitions of same fixture type with same hash value
at test class and function level.

example:
{
    "default_request-handler": "tornado_drill.tests.app.RequestHandler",
    "plugins": ["mock_plugin"]
    "default_fixtures": {
        "mock_http_server": {}
    },
    "handler_overrides": {
        "logger": MOCK_LOGGER,
        "cache": MOCK_CACHE
    }
}

for "default-fixtures" the first level of keys should be the fixture name, and
the values should be the kwargs dict for that fixture decorator function.
for "handler-overrides" the first level are the attribute name on the handler,
and the values are the overrides.

when creating plugins, a plugin-level settings.py is where most of the custom
code should be integrated.

at the user project test level there can be another settings.py for project-
global configurations. this means there can be two levels of settings defined
by settings.py files. these are loaded and flattened when this file is read,
with the project-level overriding. the fixtures defined at that point are then
further extended and overridden by class and function-level fixture decorators.

generally the values of this settings file are python objects and so storing
this file in a data format such as JSON will not work
"""
from typing import Optional, Callable, ModuleType, Any, Dict, List

from tornado_drill.fixtures.base import BaseMockRequest
from tornado_drill.fixtures.http import MOCK_HTTP_RESPONSE


class SettingsType:
    pass


PLUGINS_TYPE = Optional[List[SettingsType]]
FIXTURES_TYPE = Optional[Dict[str, Dict[BaseMockRequest, MOCK_HTTP_RESPONSE]]]
OVERRIDES_TYPE = Optional[Dict[str, Any]]

SETTINGS = None


class Settings(SettingsType):
    def __init__(self, default_request_handler_class: Optional[Callable],
                 plugins: PLUGINS_TYPE = None,
                 default_fixtures: FIXTURES_TYPE = None,
                 handler_overrides: OVERRIDES_TYPE = None):
        self.default_request_handler_class = default_request_handler_class
        self.plugins = plugins or []
        self.default_fixtures = default_fixtures() or {}
        self.handler_overrides = handler_overrides or {}

        for plugin in self.plugins:
            self.inherit(plugin.settings)

        global SETTINGS
        SETTINGS = self

    def inherit(self, settings):
        """
        take Settings from higher in hierarchy and merge them with this
        Settings, with the lower Settings values clobbering the higher.

        in practice this means that settings at the project level will override
        settings at the plugin level which will override tornado-drill defaults
        """
        for k, v in vars(settings).items():
            if not hasattr(self, k):
                setattr(self, k, v)
            elif k != 'plugins':
                attribute = getattr(self, k)
                assert isinstance(
                    attribute, dict), f'Project settings.py error - attribute {k} is not a dict!'
                assert isinstance(
                    v, dict), f'Plugin {settings.__qualname__} settings.py error - attribute {k} is not a dict!'
                attribute = {**v, **attribute}
