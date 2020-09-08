import json
from urllib.parse import urlparse, parse_qs
from typing import Union, Dict, Optional, Callable
from requests import Response

from tornado_drill.fixtures.base import BaseMockRequest

OPT_STR_DICT = Optional[Union[str, Dict[str, str]]]

MOCK_HTTP_RESPONSE = Optional[Union[str, Response]]


class MockHttpRequest(BaseMockRequest):
    def __init__(self, method: str = 'get', path: str = '',
                 body: OPT_STR_DICT = '', query: OPT_STR_DICT = '',
                 headers: Dict[str, str] = None):
        """
        TODO docs
        """
        parsed_url = urlparse(path)
        self.path = parsed_url.path
        self.method = method

        if not query:
            query_dict = parsed_url.query
        elif isinstance(query, dict):
            query_dict = query
        else:
            query_dict = parse_qs(query)
        self.query = query_dict

        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = body
        self.body = self.raw = body_str

        self.headers = headers

    def __hash__(self) -> int:
        return id(str(vars(self)))


def mock_server() -> Callable:
    # TODO do http stuff
    return get_reducer()


def mock_request() -> Callable:
    return get_reducer()
