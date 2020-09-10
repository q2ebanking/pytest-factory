"""
pytest integration hooks

the  following functions are predefined hooks in pytest that we need to
either cancel out or modify

referenced in conftest.py defined in user's project

"""
import importlib

from _pytest.config import Config
from pytest import Item

from tornado_drill.framework.settings import SETTINGS
from tornado_drill.framework.stores import *  # this is to activate the fixture defined here.
from tornado_drill.framework.requests import *
from tornado_drill.mock_request import *  # this is to activate the fixture defined here.

def pytest_configure(config: Config) -> None:
    try:
        local_settings = importlib.import_module('tests.settings').SETTINGS
        SETTINGS.load(local_settings)
    except Exception as _:
        print('TORNADO-DRILL WARNING: could not find settings.py in the expected location: <cwd>/tests/settings.py')
        print('TORNADO-DRILL WARNING: will proceed but will fail if @mock_request decorators do not define RequestHandler classes')
        pass
    STORES.load(default_store=SETTINGS.default_store)

def pytest_runtest_teardown(item: Item) -> None:
    # either before or after teardown check to see if any fixtures were not called and throw warnings?
    item.teardown()