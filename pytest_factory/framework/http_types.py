from __future__ import annotations
import json
from enum import Enum
from typing import Callable, Union, List, Optional
from urllib.parse import urlparse, parse_qs

from requests import Response
from tornado.httputil import HTTPServerRequest, HTTPHeaders

from pytest_factory.framework.base_types import BaseMockRequest, Serializable, Writable
from pytest_factory.framework.mall import MALL
from pytest_factory.framework.default_configs import http_req_wildcard_fields as default_http_req_wildcard_fields

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


class MockHttpRequest(HTTPServerRequest, BaseMockRequest, Serializable, Writable):
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

    def __init__(self, method: str = HTTP_METHODS.GET.value, path: Optional[str] = None, **kwargs):
        """
        :param method: HTTP method, e.g. GET or POST
        :param path: HTTP url
        :param kwargs: additional properties of an HTTP request e.g. headers, body, etc.
        """
        self.kwargs = {**kwargs, 'method': method, 'path': path}

        if kwargs.get('headers'):
            kwargs['headers'] = HTTPHeaders(kwargs.get('headers'))

        if kwargs.get('json'):
            json_dict = kwargs.pop('json')
            kwargs['body'] = json.dumps(json_dict).encode()

        super().__init__(method=method, uri=path, **kwargs)

        self.connection = lambda: None
        setattr(self.connection, 'set_close_callback', lambda _: None)

    @staticmethod
    def _urlparse_to_dict(uri: str) -> dict:
        # TODO maybe support wildcarding names/values of query params as opposed to the whole query param string
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
            substr_index = self.full_url().find(other)
            return substr_index > -1
        this_dict = self._urlparse_to_dict(self.uri)
        that_dict = self._urlparse_to_dict(other.uri)

        for key, this_val in this_dict.items():
            wildcard_fields = MALL.http_req_wildcard_fields or default_http_req_wildcard_fields
            if this_val == "*" or (not this_val and key in wildcard_fields):
                continue
            elif this_val != that_dict[key]:
                return False

        return True

    @property
    def content(self) -> bytes:
        return self.body

    def __hash__(self) -> int:
        """
        this is necessary because https://stackoverflow.com/questions/1608842/types-that-define-eq-are-unhashable
        """
        return id(self)
