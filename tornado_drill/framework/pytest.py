"""
pytest integration hooks

the following functions are predefined pytest hooks or pytest fixture definitions to integrate with tornado drill

please keep most fixture-specific logic out of this file

referenced in conftest.py defined in user's project

"""
import importlib

from _pytest.config import Config
import pytest

import requests

from tornado_drill.mock_request_types import HTTP_METHODS
from tornado_drill.framework.settings import SETTINGS, LOGGER
from tornado_drill.framework.requests import get_generic_caller
from tornado_drill.framework.stores import STORES


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


# TODO add pytest_collection_finish hook to detect duplicate test names and throw warning


@pytest.fixture()
def store(request):
    """
    fixture store - this is where the test-specific store gets assigned to the test function
    :return:
    """
    test_name = request.node.name
    store = STORES.get_store(test_name=test_name)
    assert store, 'TORNADO-DRILL ERROR: you broke something. probably in helpers.py or in this module'
    return store


@pytest.fixture()
def handler(request):
    """
    handler fixture

    sets up handlers for test methods that have not received it yet because they lacked explicit @mock_request
    and so pytest_func_with_handler never gets called for those methods
    otherwise this method gets overridden to be the handler when pytest_func_with_handler is invoked
    :return:
    """
    store = STORES.get_store(request.node.name)
    if store.handler is None:
        raise Exception
    return store.handler


@pytest.fixture(autouse=True)
def monkey_patch_requests(monkeypatch, request) -> None:
    test_name = request.node.name

    for method in HTTP_METHODS:
        monkeypatch.setattr(requests, method.value, get_generic_caller(requests_method_name=method.value,
                                                                       test_func_name=test_name))
