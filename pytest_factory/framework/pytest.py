"""
pytest integration hooks

import path to this file must be in pytest_plugins in conftest.py

"""
import pytest
from typing import Optional, Callable, Any

import requests

from pytest_factory.http import HTTP_METHODS
from pytest_factory.monkeypatch_requests import _request_callable, _response_callable
from pytest_factory.framework.mall import MALL
from pytest_factory import logger

logger = logger.get_logger(__name__)


@pytest.fixture()
def store(request):
    """
    store fixture - this is where the test-specific store gets assigned to the
    test function
    :return:
    """
    test_name = request.node.name
    store = MALL.get_store(test_name=test_name)
    # TODO check store at this point!
    store.register_plugins(plugins=MALL.plugins)
    # TODO check store at this point!
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


def get_generic_caller(method_name: str, test_func_name: str,
                       request_callable: Callable,
                       response_callable: Optional[Callable] = None) -> Callable:
    """
    this method will redefine the method with method_name in the module being
    monkeypatched while including in the new method the name of test function
    so it can look up mock responses

    :param method_name: the name of the method in the module being
        monkeypatched for this test
    :param test_func_name: name of the test function that will be in scope
        for this monkeypatch
    :param request_callable: class of the request object or function that will
        return one; must always take method_name as kwarg
    :param response_callable: class of the response object or function that
        will return one
    :return: the method that will replace the old one in the module being
        monkeypatched
    """

    def generic_caller(*args, **kwargs) -> Any:
        """
        this method replaces method_name in the module being monkeypatched
        """

        req_obj = request_callable(method_name=method_name, *args, **kwargs)
        store = MALL.get_store(test_name=test_func_name)
        mock_response = store.get_next_response(factory_name=req_obj.FACTORY_NAME, req_obj=req_obj)
        if isinstance(mock_response, Callable):
            mock_response = mock_response(req_obj)

        if isinstance(mock_response, Exception):
            raise mock_response

        if response_callable:
            mock_response = response_callable(mock_response=mock_response, *args, **kwargs)
        return mock_response

    return generic_caller
