"""
when creating plugins, a plugin-level settings.py is where most of the custom
code should be integrated.

at the user project test level there can be another settings.py for project-
global configurations. this means there can be two levels of settings defined
by settings.py files. these are loaded and flattened when this file is read,
with the project-level overriding. the fixtures defined at that point are then
further extended and overridden by class and function-level fixture decorators.
"""
from typing import Optional, Callable, Any, Dict, List


class SettingsType:
    pass


class StoreType:
    pass


PLUGINS_TYPE = Optional[List[SettingsType]]
OVERRIDES_TYPE = Optional[Dict[str, Any]]

# There can only be one in the end
SETTINGS: SettingsType = None


class Settings(SettingsType):
    def __init__(self, default_request_handler_class: Optional[Callable],
                 plugins: PLUGINS_TYPE = None,
                 global_store: Optional[StoreType] = None,
                 handler_overrides: OVERRIDES_TYPE = None):
        self.default_request_handler_class = default_request_handler_class
        self.plugins = plugins or []
        self.global_store = global_store or {}
        self.handler_overrides = handler_overrides or {}
        """

        :param default_request_handler_class:
        :param plugins:
        :param global_store:
        :param handler_overrides:
        :returns:
        """
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
