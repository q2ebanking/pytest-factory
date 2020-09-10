"""
monkeypatches requests module to intercept http calls and lookup mock response
in fixtures store
"""
import sys
import requests
import pytest
from enum import Enum

from tornado_drill.framework.stores import STORES
from tornado_drill.mock_request_types import MockHttpRequest


# based on what the requests module supports
class HTTP_METHODS(Enum):
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    POST = 'post'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


@pytest.fixture(scope='function', autouse=True)
def monkey_patch_requests(monkeypatch, request) -> None:
    test_name = request.node.name

    async def generic_caller(*args, **kwargs) -> requests.Response:
        """
        this method will monkeypatch the async version of the requests http
        method e.g. requests.get

        it is important when creating monkeypatches to simulate the error
        behavior of the actual code as much as possible, including raising the
        correct Exception types
        """
        method_name = sys._getframe(0).f_code.co_name
        method = getattr(requests, method_name)
        uri = kwargs.get('url') or args[0] if args else None
        if not uri:
            raise TypeError(
                f"{method_name}() missing 1 required positional argument: 'url'")

        # TODO need to translate other requests params into params for MockHttpRequest
        req_obj = MockHttpRequest(method=method, uri=uri)

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

    for method in HTTP_METHODS:
        monkeypatch.setattr(requests, method, generic_caller)
