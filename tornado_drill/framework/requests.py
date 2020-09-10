"""
monkeypatches requests module to intercept http calls and lookup mock response
in fixtures store
"""
import requests
import pytest
import json
from typing import Callable

from tornado.httputil import HTTPHeaders

from tornado_drill.framework.stores import STORES
from tornado_drill.mock_request_types import MockHttpRequest, HTTP_METHODS


@pytest.fixture(scope='function', autouse=True)
def monkey_patch_requests(monkeypatch, request) -> None:
    test_name = request.node.name

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

            mock_http_request_kwargs = {
                'method': method_name,
                'path': path
            }

            if kwargs.get('headers'):
                mock_http_request_kwargs['headers'] = HTTPHeaders(kwargs.get('headers'))

            if kwargs.get('body'):
                # TODO convert to bytes?
                mock_http_request_kwargs['body'] = kwargs.get('body')

            # TODO need to translate other requests params into params for MockHttpRequest
            req_obj = MockHttpRequest(**mock_http_request_kwargs)

            store = STORES.get_store(test_name=test_name)
            fixture = store.mock_http_server  # TODO this is not getting loaded implicitly - see helpers.py?
            mock_response = fixture.get('*')
            for k, v in fixture.items():
                if k.__hash__() == req_obj.__hash__():
                    mock_response = v
            response = requests.Response()
            if not mock_response:
                response.status_code = 404
            elif isinstance(mock_response, str):  # string body 200
                response._content = mock_response
            elif isinstance(mock_response, dict):  # json body 200
                response._content = json.dumps(mock_response)
            elif isinstance(mock_response, Exception):
                raise mock_response
            else:
                assert False, 'should not happen'
            return response

        return generic_caller

    for method in HTTP_METHODS:
        monkeypatch.setattr(requests, method.value, get_generic_caller(method.value))
