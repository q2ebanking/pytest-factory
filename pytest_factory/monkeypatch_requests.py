"""
monkeypatches requests module to intercept http calls and lookup mock response
in store
"""
from requests import Response
import json
from typing import Union

from tornado.httputil import HTTPHeaders

from pytest_factory.http import MockHttpRequest
from pytest_factory.framework.exceptions import PytestFactoryException


def _request_callable(method_name: str, *args, **kwargs) -> MockHttpRequest:
    """
    this method will redefine the method with method_name in the module being
    monkeypatched while including in the new method the name of test function
    so it can look up mock responses

    :param method_name: the name of the method in the module being
        monkeypatched for this test
    :param test_func_name: name of the test function that will be in scope for
        this monkeypatch
    :param request_callable: class of the request object or function that will
        return one
    :param response_callable: class of the response object or function that
        will return one
    :return: the method that will replace the old one in the module being
        monkeypatched
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
        mock_http_request_kwargs['headers'] = HTTPHeaders(
            kwargs.get('headers'))

    if kwargs.get('body'):
        # TODO check if str and convert to bytes?
        mock_http_request_kwargs['body'] = kwargs.get('body')

    elif kwargs.get('json'):
        mock_http_request_kwargs['body'] = json.dumps(kwargs.get('json')).encode()

    req_obj = MockHttpRequest(**mock_http_request_kwargs)
    return req_obj


MOCK_RESP_TYPE = Union[None, Response, str, dict, Exception]


def _response_callable(mock_response: MOCK_RESP_TYPE,
                       *_, **kwargs) -> Response:
    response = Response()
    if not mock_response:
        response.status_code = 404
    elif isinstance(mock_response, str):  # string body 200
        response._content = mock_response
    elif isinstance(mock_response, dict):  # json body 200
        response._content = json.dumps(mock_response)
    elif isinstance(mock_response, Response):
        response = mock_response
    else:
        raise PytestFactoryException

    # TODO need to replicate redirect behavior unless allow_redirects==False.
    #  how though? could return an array instead and then it's up to
    # if response.status_code == 302 and kwargs.get('allow_redirects') is not False:
    # wut do
    return response
