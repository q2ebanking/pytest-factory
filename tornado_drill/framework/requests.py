"""
monkeypatches requests module to intercept http calls and lookup mock response
in fixtures store
"""
import requests
import pytest
from typing import Any
from enum import Enum

from tornado_drill.framework.stores import STORES
from tornado_drill.mock_request_types import MockHttpRequest


# based on what the requests module supports
class HTTP_METHODS(Enum):
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    POST = 'post'
    PATCH = 'patch'
    HEAD = 'head'
    OPTIONS = 'options'


@pytest.fixture(scope='function', autouse=True)
def monkey_patch_requests(monkeypatch: Any) -> None:
    async def generic_caller(**kwargs: Any) -> requests.Response:
        # generate MockHttpRequest from kwargs
        # check STORES
        # retrieve response if available
        # if not then 404 (unless there is a wildcard default!)
        pass

    for method in HTTP_METHODS:
        monkeypatch.setattr(requests, method, generic_caller)
