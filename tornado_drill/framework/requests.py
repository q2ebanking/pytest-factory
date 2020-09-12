"""
monkeypatches requests module to intercept http calls and lookup mock response
in fixtures store
"""
from requests import Response
import json
from typing import Callable

from tornado.httputil import HTTPHeaders

from tornado_drill.framework.stores import STORES
from tornado_drill.mock_request_types import MockHttpRequest


def get_generic_caller(requests_method_name: str, test_func_name: str) -> Callable:
    def generic_caller(*args, **kwargs) -> Response:
        """
        this method will replace the http method in the requests module
        e.g. requests.get

        TODO this needs to be even more generic - what if the user wants to use a library other than requests to make
         calls? they'd have copy/paste most of this method

        it is important when creating monkeypatches to simulate the error
        behavior of the actual code as much as possible, including raising the
        correct Exception types
        """
        path = kwargs.get('url') or (args[0] if args else None)
        if not path:
            raise TypeError(
                f"{requests_method_name}() missing 1 required positional argument: 'url'")

        mock_http_request_kwargs = {
            'method': requests_method_name,
            'path': path
        }

        if kwargs.get('headers'):
            mock_http_request_kwargs['headers'] = HTTPHeaders(kwargs.get('headers'))

        if kwargs.get('body'):
            # TODO check if str and convert to bytes?
            mock_http_request_kwargs['body'] = kwargs.get('body')

        req_obj = MockHttpRequest(**mock_http_request_kwargs)
        mock_response = STORES.get_next_response(test_name=test_func_name,
                                                 fixture_name='mock_http_server',  # TODO make this smarter -
                                                 # allow plugin developer to provide a function that takes req_obj
                                                 # and determines if a custom fixture routing is needed!!
                                                 req_obj=req_obj)
        if isinstance(mock_response, Callable):
            mock_response = mock_response(req_obj)

        response = Response()
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
