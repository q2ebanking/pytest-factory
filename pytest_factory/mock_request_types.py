from __future__ import annotations
from urllib.parse import urlparse, parse_qs
from typing import Hashable, Optional, Union, List, Callable, Dict, Any
from enum import Enum
from requests import Response

from tornado.httputil import HTTPServerRequest, HTTPHeaders

from pytest_factory.framework.config_stub import HTTP_REQ_WILDCARD_FIELDS

# responses are optional and can be either a single response or list of
# responses where the response type is either a Callable, Exception, str or
# requests.Response object
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


# based on what the requests module supports
class HTTP_METHODS(Enum):
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    POST = 'post'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


class FailureMode:
    # TODO
    pass


class BaseMockRequest(Hashable):
    """
    dual-purpose class used to represent:
    - Actual Requests when created from parameters of @actual_request
    - Expected Requests when created from parameters of @mock_server
    (or similar fixture factory)

    these are stored in fixture store by test, fixture name and BaseMockRequest
    object as key where newest key always wins
    """

    def compare(self, other) -> bool:
        """
        comparison must elide non-significant differences to return matches
        e.g. "https://www.test.com?id=0&loc=1" should match
        "https://www.test.com?loc=1&id=0"
        """
        raise NotImplementedError

    def __hash__(self) -> int:
        return id(self)


ROUTING_TYPE = Dict[
    Union[
        Dict[str, Any],
        BaseMockRequest],
    MOCK_HTTP_RESPONSE
]


def _urlparse_to_dict(uri: str) -> dict:
    url_parts = urlparse(uri)
    url_component_dict = {key: getattr(url_parts, key) for key in ("scheme", "netloc", "params", "fragment")}
    url_component_dict["query"] = url_parts.query if url_parts.query == "*" else parse_qs(url_parts.query)
    for index, path_part in enumerate(url_parts.path.split('/')):
        url_component_dict[f"path_{index}"] = path_part
    return url_component_dict


class MockHttpRequest(HTTPServerRequest, BaseMockRequest):
    """
    if creating your own request type for a fixture, you must set FACTORY_NAME on the class
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

        super().__init__(method=method, uri=path, **kwargs)

        # TODO make this more fake later but this trick will work if a user doesn't look too closely in the debugger
        self.connection = lambda: None
        setattr(self.connection, 'set_close_callback', lambda _: None)

    def compare(self, other: MockHttpRequest) -> bool:
        """
        we are effectively simulating the third-party endpoint's router here
        """

        this_dict = _urlparse_to_dict(self.uri)
        that_dict = _urlparse_to_dict(other.uri)

        for key, this_val in this_dict.items():
            if key not in HTTP_REQ_WILDCARD_FIELDS and this_val != "*":
                if this_val != that_dict[key]:
                    return False

        return True

    def __hash__(self) -> int:
        # TODO this is necessary because https://stackoverflow.com/questions/1608842/types-that-define-eq-are-unhashable
        #  not ideal but necessary
        return id(self)
