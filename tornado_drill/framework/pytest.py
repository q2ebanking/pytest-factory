"""
pytest integration hooks

the  following functions are predefined hooks in pytest that we need to
either cancel out or modify

referenced in conftest.py defined in user's project

"""
import importlib

from _pytest.config import Config
from pytest import Item

from tornado_drill.framework.settings import SETTINGS, LOGGER
from tornado_drill.framework.stores import *  # this is to activate the fixture defined here.
from tornado_drill.framework.requests import *
from tornado_drill.mock_request import *  # this is to activate the fixture defined here.


def pytest_configure(config: Config) -> None:
    try:
        local_settings = importlib.import_module('tests.settings').SETTINGS
        SETTINGS.load(local_settings)
    except Exception as _:
        LOGGER.warning(
            'could not find settings.py in the expected location: <cwd>/tests/settings.py'
            'will proceed but will fail if @mock_request decorators do not define RequestHandler classes')
        pass
    STORES.load(default_store=SETTINGS.default_store)


def pytest_runtest_teardown(item: Item) -> None:
    uncalled_fixtures = STORES.get_uncalled_fixtures(item.name)
    if any(uncalled_fixtures):
        # TODO maybe provide user with a flag somewhere (perhaps on @mock_request?) that will turn these into assert fails?
        LOGGER.warning(
            f'{item.name} failed to call the following fixtures during execution: {uncalled_fixtures}!',
            f'if this is not expected, consider this a test failure!')
    STORES.reset(item.name)

    item.teardown()
