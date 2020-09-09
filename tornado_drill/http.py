from typing import Union, Dict, Optional, Callable
from tornado_drill.framework.wrapper import get_fixture_decorator
from tornado_drill.mock_request_types import MockHttpRequest, MOCK_HTTP_RESPONSE

OPT_STR_DICT = Optional[Union[str, Dict[str, str]]]


def mock_http_server(req_obj: Optional[MockHttpRequest],
                     response: MOCK_HTTP_RESPONSE, **kwargs) -> Callable:
    req_obj = req_obj or MockHttpRequest(**kwargs)
    assert req_obj, 'failed to load MockHttpRequest object!'
    return get_fixture_decorator(req_obj=req_obj, response=response, **kwargs)
