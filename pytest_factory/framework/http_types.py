from __future__ import annotations
from enum import Enum
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs

from pytest_factory.framework.base_types import BaseMockRequest, BaseMockResponse
from pytest_factory.framework.mall import MALL
from pytest_factory.framework.default_configs import http_req_wildcard_fields as default_http_req_wildcard_fields


class MockHttpResponse(BaseMockResponse):
    def __init__(self, body: Optional[bytes] = None, status: Optional[int] = None,
                 headers: Optional[Dict[str, str]] = None, exchange_id: Optional[str] = None,
                 timestamp: Optional[str] = None):
        self.kwargs = {k: v for k, v in locals().items() if k != 'self'}
        self.body = body or b''
        self.status = status or 200
        self.headers = headers or {}
        super().__init__(exchange_id=exchange_id, timestamp=timestamp)


# based on what the requests module supports
class HTTP_METHODS(Enum):
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    POST = 'post'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


class MockHttpRequest(BaseMockRequest):
    """
    abstract HTTP request class representing simulated and actual inbound and outbound requests.
    normalizing all requests within pytest-factory allows for direct comparison of requests, which has
    different purposes for each request type:
     - inbound: enables redefinition of inputs to system-under-test at method level over class-level
     - outbound: enables routing of inputs to depended-on-component to corresponding test double response
    if creating your own request type for a factory, and it is for a transfer protocol,
    you must set FACTORY_NAME on the class
    """

    FACTORY_NAME = 'mock_http_server'
    FACTORY_PATH = 'pytest_factory.http'

    def __init__(self, url: str, method: str = 'get', body: Optional[bytes] = b'', headers: Optional[dict] = None,
                 exchange_id: Optional[str] = None, timestamp: Optional[str] = None, **kwargs):
        """
        :param url:
        :param method:
        :param body:
        :param headers:
        :param exchange_id:
        """
        self.kwargs = {k: v for k, v in locals().items() if k not in {'kwargs', 'self'}}
        self.kwargs.update(kwargs)
        self.allow_redirects = False
        self.url = url
        self.method = method
        self.body = body
        self.headers = headers or {}

    @staticmethod
    def _urlparse_to_dict(uri: str) -> dict:
        url_parts = urlparse(uri)
        url_component_dict = {key: getattr(url_parts, key) for key in ("scheme", "netloc", "params", "fragment")}
        url_component_dict["query"] = url_parts.query if url_parts.query == "*" else parse_qs(url_parts.query)
        for index, path_part in enumerate(url_parts.path.split('/')):
            url_component_dict[f"path_{index}"] = path_part
        return url_component_dict

    def compare(self, other: MockHttpRequest) -> bool:
        """
        compares this HTTP request to another
        """
        if isinstance(other, str):
            substr_index = self.url.find(other)
            return substr_index > -1

        if self.method != other.method:
            return False

        this_dict = self._urlparse_to_dict(self.url)
        that_dict = self._urlparse_to_dict(other.url)

        for key, this_val in this_dict.items():
            wildcard_fields = MALL.http_req_wildcard_fields or default_http_req_wildcard_fields
            if this_val == "*" or that_dict[key] == "*" or key in wildcard_fields \
                    and (not this_val or not that_dict[key]):
                continue
            elif this_val != that_dict[key]:
                return False

        return True
