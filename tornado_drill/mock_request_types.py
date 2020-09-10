from urllib.parse import urlparse
from typing import Hashable, Optional, Union
from enum import Enum
from requests import Response

from tornado.httputil import HTTPServerRequest

MOCK_HTTP_RESPONSE = Optional[Union[str, Response]]


# based on what the requests module supports
class HTTP_METHODS(Enum):
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    POST = 'post'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


class BaseMockRequest(Hashable):
    """
    dual-purpose class used to represent:
    - Actual Requests when created from parameters of @actual_request
    - Expected Requests when created from parameters of @mock_server
    (or similar fixture decorator)

    these are stored in fixture store by test, fixture name and BaseMockRequest
    object as key where newest hash value always wins
    """

    def __hash__(self, **kwargs) -> int:
        """
        hash value must elide non-significant differences to return matches
        e.g. "https://www.test.com?id=0&loc=1" should match
        "https://www.test.com?loc=1&id=0"
        """
        raise NotImplementedError


class MockHttpRequest(BaseMockRequest, HTTPServerRequest):
    def __init__(self, method: str = HTTP_METHODS.GET.value, path: Optional[str] = None, **kwargs):
        super().__init__(method=method, uri=path, **kwargs)

        # TODO make this more fake later but this trick will work if a user doesn't look too closely in the debugger
        self.connection = lambda: None
        setattr(self.connection, 'set_close_callback', lambda _: None)

    def __hash__(self) -> int:
        HASHING_ATTRIBUTES = ('query_arguments', 'body_arguments', 'method', 'protocol', 'host')

        url_parts = urlparse(self.uri)
        hashable_dict = {
            'path': url_parts.path
        }
        if self.headers:
            hashable_dict['headers'] = self.headers if isinstance(self.headers, dict) else self.headers._dict
        for attribute in HASHING_ATTRIBUTES:
            hashable_dict[attribute] = getattr(self, attribute)

        return id(str(hashable_dict))
