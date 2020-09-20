"""
pytest integration hooks

the following functions are predefined pytest hooks or pytest fixture
definitions to integrate with pytest-factory

please keep most fixture-specific logic out of this file

referenced in conftest.py defined in user's project

"""
import importlib

from _pytest.config import Config
import pytest

import requests

from pytest_factory.mock_request_types import HTTP_METHODS
from pytest_factory.framework.settings import SETTINGS, LOGGER
from pytest_factory.framework.helpers import get_generic_caller
from pytest_factory.requests import _request_callable, _response_callable
from pytest_factory.framework.stores import STORES


# from pytest_factory.parameterization import parameterize


def pytest_configure(config: Config) -> None:
    try:
        local_settings = importlib.import_module('tests.settings').SETTINGS
        SETTINGS.load(local_settings)
    except Exception as _:
        LOGGER.warning('could not find settings.py in the expected '
                       + 'location: <cwd>/tests/settings.py',
                       'will proceed but will fail if @Òmock_request '
                       + 'decorators do not define RequestHandler classes')
        pass
    STORES.load(default_store=SETTINGS.default_store)


def pytest_generate_tests(metafunc: "Metafunc") -> None:
    """
    takes metafunc and passes the contained Item to the parameterizer
    which returns a list of new test Items.
    metafunc is updated with the new test Items
    :param metafunc: contains metadata for test function and references
        to test config and definition
    """
    pass


@pytest.fixture()
def store(request):
    """
    fixture store - this is where the test-specific store gets assigned to the
    test function
    :return:
    """
    test_name = request.node.name
    store = STORES.get_store(test_name=test_name)
    assert store, 'pytest-factory ERROR: you broke something. probably in ' + \
                  'helpers.py or in this module'
    return store


@pytest.fixture(autouse=True)
def monkey_patch_requests(monkeypatch, request) -> None:
    test_name = request.node.name

    for method in HTTP_METHODS:
        new_method = get_generic_caller(method_name=method.value,
                                        test_func_name=test_name,
                                        request_callable=_request_callable,
                                        response_callable=_response_callable)
        monkeypatch.setattr(requests, method.value, new_method)
