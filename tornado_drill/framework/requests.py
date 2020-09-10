"""
monkeypatches requests module to intercept http calls and lookup mock response
in fixtures store
"""
import requests
import pytest
import inspect
from typing import Callable

from tornado_drill.framework.stores import STORES
from tornado_drill.mock_request_types import MockHttpRequest, HTTP_METHODS


@pytest.fixture(scope='function', autouse=True)
def monkey_patch_requests(monkeypatch, request) -> None:
    request.instance

    test_name = request.module.__name__ + '.' + request.node.name

    def get_generic_caller(method_name: str) -> Callable:
        def generic_caller(*args, **kwargs) -> requests.Response:
            """
            this method will replace the http method in the requests module
            e.g. requests.get

            it is important when creating monkeypatches to simulate the error
            behavior of the actual code as much as possible, including raising the
            correct Exception types
            """
            path = kwargs.get('url') or (args[0] if args else None)
            if not path:
                raise TypeError(
                    f"{method_name}() missing 1 required positional argument: 'url'")

            # TODO need to translate other requests params into params for MockHttpRequest
            req_obj = MockHttpRequest(method=method_name, path=path)

            store = STORES.get_store(test_name=test_name)
            fixture = store.mock_http_server
            mock_response = fixture.get(req_obj) or fixture.get('*')
            if not mock_response:
                response = requests.Response()  # TODO set to 404
            elif isinstance(mock_response, str):  # string body 200
                response = requests.Response()
            elif isinstance(mock_response, dict):  # json body 200
                response = requests.Response()
            elif isinstance(mock_response, MockHttpRequest):  # custom response
                response = requests.Response()
            elif isinstance(mock_response, Exception):
                raise mock_response
            else:
                assert False, 'should not happen'
            return response  # TODO if simulating timeout we would respond with None

        return generic_caller

    for method in HTTP_METHODS:
        monkeypatch.setattr(requests, method.value, get_generic_caller(method.value))
