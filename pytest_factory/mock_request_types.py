from urllib.parse import urlparse
from typing import Hashable, Optional, Union, List, Callable, Dict, Any
from enum import Enum
from requests import Response

from tornado.httputil import HTTPServerRequest, HTTPHeaders

# responses are optional and can be either a single response or list of
# responses where the response type is either a Callable, Exception, str or
# requests.Response object
MOCK_HTTP_RESPONSE = Optional[
    Union[
        Exception,
        str,
        Response,
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
    object as key where newest hash value always wins
    """

    def __init__(self, key: str = None):
        self._key = key

    def __hash__(self, **kwargs) -> int:
        """
        hash value must elide non-significant differences to return matches
        e.g. "https://www.test.com?id=0&loc=1" should match
        "https://www.test.com?loc=1&id=0"
        """
        raise NotImplementedError

    @property
    def key(self):
        return self._key or hash(self)

    def __str__(self):
        return self.key or super().__str__()


ROUTING_TYPE = Dict[
    Union[
        Dict[str, Any],
        BaseMockRequest],
    MOCK_HTTP_RESPONSE
]


class MockHttpRequest(BaseMockRequest, HTTPServerRequest):
    """
    if creating your own request type for a fixture, you must set FACTORY_NAME on the class
    """
    HASHING_ATTRIBUTES = ('query_arguments', 'body_arguments',
                          'method', 'protocol', 'host')

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

    def __hash__(self) -> int:
        """

        :return: semi-unique integer
        """

        url_parts = urlparse(self.uri)
        hashable_dict = {
            'path': url_parts.path
        }
        if self.headers:
            hashable_dict['headers'] = self.headers if isinstance(
                self.headers, dict) else self.headers._dict
        for attribute in self.HASHING_ATTRIBUTES:
            hashable_dict[attribute] = getattr(self, attribute)

        return id(str(hashable_dict))
