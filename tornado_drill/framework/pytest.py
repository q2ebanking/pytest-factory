"""
pytest integration hooks

the  following functions are predefined hooks in pytest that we need to
either cancel out or modify

referenced in conftest.py defined in user's project

"""
import importlib
from warnings import warn

from _pytest.config import Config
from pytest import Item, Session

from tornado_drill.framework.settings import SETTINGS
from tornado_drill.framework.stores import *  # this is to activate the fixture defined here.
from tornado_drill.framework.requests import *
from tornado_drill.mock_request import *  # this is to activate the fixture defined here.


def pytest_configure(config: Config) -> None:
    try:
        local_settings = importlib.import_module('tests.settings').SETTINGS
        SETTINGS.load(local_settings)
    except Exception as _:
        warn('TORNADO-DRILL WARNING: could not find settings.py in the expected location: <cwd>/tests/settings.py')
        warn(
            'TORNADO-DRILL WARNING: will proceed but will fail if @mock_request decorators do not define RequestHandler classes')
        pass
    STORES.load(default_store=SETTINGS.default_store)


# def pytest_collection_finish(session: Session) -> None:
#     pass


def pytest_runtest_teardown(item: Item) -> None:
    # either before or after teardown check to see if any fixtures were not called and throw warnings?
    store = STORES.get_store(test_name=item.name)

    def find_uncalled(responses):
        return [resp[1] for resp in responses if not resp[0]]
    #
    # uncalled_fixtures = {fixture: find_uncalled(responses) for fixture, responses in vars(store).items()}
    # if any(uncalled_fixtures):
    #     warn(
    #         f'TORNADO-DRILL WARNING: {item.name} failed to call the following fixtures during execution: {uncalled_fixtures}!')
    #     # TODO maybe provide user with a flag somewhere (perhaps on @mock_request?) that will turn these into assert fails?
    #     warn('TORNADO-DRILL WARNING: if this is not expected, consider this a test failure!')
    item.teardown()
