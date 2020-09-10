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


class Settings(SettingsType):
    def __init__(self,
                 default_request_handler_class: Optional[Callable] = None,
                 plugin_settings: PLUGINS_TYPE = None,
                 default_store: Optional[StoreType] = None,
                 handler_overrides: OVERRIDES_TYPE = None):
        """

        :param default_request_handler_class:
        :param plugins:
        :param default_store:
        :param handler_overrides:
        :returns:
        """
        self.default_request_handler_class = default_request_handler_class
        self.plugin_settings = plugin_settings or []
        self.default_store = default_store or {}
        self.handler_overrides = handler_overrides or {}
        for settings in self.plugin_settings:
            self.inherit(settings)

    def load(self, settings: SettingsType):
        """
        take Settings from lower in hierarchy and merge them into the global settings

        in practice this means that the merged project and plugin hierarchy settings
        will override tornado-drill defaults
        :param settings:
        :return:
        """
        for attribute, value in vars(settings).items():
            setattr(self, attribute, value)

    def inherit(self, settings: SettingsType):
        """
        take Settings from higher in hierarchy and merge them with this
        Settings, with the lower Settings values clobbering the higher.

        in practice this means that settings at the project level (of which there
        can ONLY be one) will override settings at the plugin level, of which
        there can be MORE than one
        """
        for k, v in vars(settings).items():
            if not hasattr(self, k):
                setattr(self, k, v)
            elif k == 'plugin_settings':
                for plugin_settings in v:
                    self.inherit(plugin_settings)
            elif isinstance(v, dict) and isinstance(getattr(self, k), dict):
                attribute = getattr(self, k)
                setattr(self, k, {**v, **attribute})


SETTINGS = Settings()
