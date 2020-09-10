from tornado.httputil import HTTPServerRequest
from typing import Hashable, Optional, Union
from enum import Enum
from requests import Response

MOCK_HTTP_RESPONSE = Optional[Union[str, Response]]


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
    def __init__(self, path: Optional[str] = None, **kwargs):
        super().__init__(uri=path, **kwargs)

    def __hash__(self) -> int:
        # todo: need to see in testing if HTTPServerRequest behaves or if we
        # need a more explicit hashing
        return str(vars(self))
