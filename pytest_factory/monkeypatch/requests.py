"""
monkeypatches requests module to intercept http calls and lookup mock response
in store
"""
import requests
from requests.structures import CaseInsensitiveDict
import json
from typing import Union

from pytest_factory.framework.http_types import HTTP_METHODS
from pytest_factory.http import MockHttpRequest, MockHttpResponse
from pytest_factory.framework.exceptions import TypeTestDoubleException
from pytest_factory.monkeypatch.utils import update_monkey_patch_configs, get_generic_caller


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
        'url': path
    }

    if kwargs.get('headers'):
        mock_http_request_kwargs['headers'] = CaseInsensitiveDict(
            kwargs.get('headers'))
    else:
        mock_http_request_kwargs['headers'] = CaseInsensitiveDict()

    if kwargs.get('body'):
        body = kwargs.get('body')
        body_bytes = body if isinstance(body, bytes) else body.encode()
        mock_http_request_kwargs['body'] = body_bytes
    elif kwargs.get('data'):
        mock_http_request_kwargs['body'] = kwargs.get('data')

    elif kwargs.get('json'):
        mock_http_request_kwargs['body'] = json.dumps(kwargs.get('json')).encode()
        if mock_http_request_kwargs.get('headers'):
            mock_http_request_kwargs['headers']['Content-Type'] = 'application/json'
        else:
            mock_http_request_kwargs['headers'] = CaseInsensitiveDict({'Content-Type': 'application/json'})
    allow_redirects = kwargs.get('allow_redirects')
    allow_redirects = True if allow_redirects is None else allow_redirects
    mock_http_request_kwargs['allow_redirects'] = allow_redirects
    req_obj = MockHttpRequest(**mock_http_request_kwargs)
    return req_obj


MOCK_RESP_TYPE = Union[None, requests.Response, bytes, str, dict, Exception]


def _response_callable(*_, mock_response: MOCK_RESP_TYPE,
                       **__) -> requests.Response:
    """
    takes the user-defined test double for the DOC response and casts it as a Response object
    """

    if isinstance(mock_response, requests.Response):
        response = mock_response
    else:
        response = requests.Response()
        if mock_response is None:
            response.status_code = 404
        elif isinstance(mock_response, MockHttpResponse):
            response._content = mock_response.body
            response.status_code = mock_response.status
        elif isinstance(mock_response, bytes):  # bytes body 200
            response._content = mock_response
        elif isinstance(mock_response, str):
            response._content = mock_response.encode()
        elif isinstance(mock_response, dict):  # json body 200
            response._content = json.dumps(mock_response).encode()
        else:
            raise TypeTestDoubleException(request_module_name='requests', response=mock_response)
    response.reason = response.url = ''
    response.encoding = 'utf-8'
    response.status_code = response.status_code or 200
    return response


new_methods = {}
for method in HTTP_METHODS:
    new_method = get_generic_caller(method_name=method.value,
                                    request_callable=_request_callable,
                                    response_callable=_response_callable)

    new_methods[method.value] = new_method

update_monkey_patch_configs(callable_obj=requests, patch_members=new_methods)
