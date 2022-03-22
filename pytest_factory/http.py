from __future__ import annotations
import json
from typing import Optional, Callable, List, Union
from urllib.parse import urlparse, parse_qs
from enum import Enum

from tornado.httputil import HTTPServerRequest, HTTPHeaders

from pytest_factory.framework.factory import make_factory
from pytest_factory.framework.mall import MALL
from pytest_factory.outbound_response_double import BaseMockRequest
from requests import Response

MOCK_HTTP_RESPONSE = Optional[
    Union[
        Exception,
        str,
        Response,
        Callable,
        List[
            Union[
                Callable,
                Exception,
                str,
                Response]]]]


def _urlparse_to_dict(uri: str) -> dict:
    # TODO maybe support wildcarding names/values of query params as opposed to the whole query param string
    url_parts = urlparse(uri)
    url_component_dict = {key: getattr(url_parts, key) for key in ("scheme", "netloc", "params", "fragment")}
    url_component_dict["query"] = url_parts.query if url_parts.query == "*" else parse_qs(url_parts.query)
    for index, path_part in enumerate(url_parts.path.split('/')):
        url_component_dict[f"path_{index}"] = path_part
    return url_component_dict


# based on what the requests module supports
class HTTP_METHODS(Enum):
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    POST = 'post'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


class MockHttpRequest(HTTPServerRequest, BaseMockRequest):
    """
    if creating your own request type for a factory, and it is for a transfer protocol,
    you must set FACTORY_NAME on the class
    """

    FACTORY_NAME = 'mock_http_server'

    def __init__(self, method: str = HTTP_METHODS.GET.value, path: Optional[str] = None, **kwargs):
        """
        TODO
        :param method:
        :param path:
        :param kwargs:
        """
        if kwargs.get('headers'):
            kwargs['headers'] = HTTPHeaders(kwargs.get('headers'))

        if kwargs.get('json'):
            json_dict = kwargs.pop('json')
            kwargs['body'] = json.dumps(json_dict).encode()

        super().__init__(method=method, uri=path, **kwargs)

        # TODO make this more fake later but this trick will work if a user doesn't look too closely in the debugger
        self.connection = lambda: None
        setattr(self.connection, 'set_close_callback', lambda _: None)

    def compare(self, other: MockHttpRequest) -> bool:
        if isinstance(other, str):
            substr_index = self.full_url().find(other)
            return substr_index > -1
        this_dict = _urlparse_to_dict(self.uri)
        that_dict = _urlparse_to_dict(other.uri)

        for key, this_val in this_dict.items():
            if this_val == "*" or (not this_val and key in MALL.http_req_wildcard_fields):
                continue
            elif this_val != that_dict[key]:
                return False

        return True

    @property
    def content(self) -> str:
        return self.body.decode()

    def __hash__(self) -> int:
        # TODO this is necessary because https://stackoverflow.com/questions/1608842/types-that-define-eq-are-unhashable
        #  not ideal but necessary
        return id(self)


def mock_http_server(response: MOCK_HTTP_RESPONSE = None,
                     req_obj: Optional[MockHttpRequest] = None,
                     method: Optional[str] = HTTP_METHODS.GET.value,
                     path: Optional[str] = None, **kwargs) -> Callable:
    """
    TODO load from swagger, WSDL, etc.
    TODO document method fully

    :param response: defaults to empty string; can be single response or list of responses (for changing
    responses to consecutive calls to same endpoint) where response is of type:
    - str: will get returned as requests.Response where the response string is
        the body
    - Exception: will get raised as if the requests method failed and not attempt to generate a response
    - Response: returned directly
    - Callable: must be a function that takes the req_obj as argument and
        returns one of the above types
        - for when user wants mock server to have some correlation between
            request and response (like id of requested asset)
        - for raising Exceptions conditioned on content of the request
        - for more sophisticated behavior, consider creating a plugin instead
    :param req_obj: MockHttpRequest if kwargs not provided
    :param method: if req_obj not provided, HTTP method for creating MockHttpRequest
    :param path: if req_obj not provided, url path for creating MockHttpRequest
    :param kwargs: see help(MockHttpRequest.__init__) if not passing req_obj
    :return: the test class or function being decorated
    """
    expected_request = req_obj or MockHttpRequest(method=method, path=path, **kwargs)
    assert expected_request, 'failed to load MockHttpRequest object!'  # todo make test for this
    return make_factory(req_obj=expected_request, response=response)


class BasePlugin:
    # TODO seems unnecessary to make this a class - rework to replace with module
    PLUGIN_URL = None

    def __init__(self):
        assert self.PLUGIN_URL is not None

    @staticmethod
    def map_request_to_factory(req_obj: MockHttpRequest) -> str:
        raise NotImplementedError

    @staticmethod
    def parse_test_double_key(req_obj: MockHttpRequest) -> str:
        raise NotImplementedError
