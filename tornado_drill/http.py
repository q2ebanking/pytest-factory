from typing import Union, Dict, Optional, Callable
from tornado_drill.framework.helpers import get_decorated_callable
from tornado_drill.mock_request_types import MockHttpRequest, \
    MOCK_HTTP_RESPONSE

OPT_STR_DICT = Optional[Union[str, Dict[str, str]]]


def mock_http_server(response: MOCK_HTTP_RESPONSE,
# TODO find a way to track this! like a "fixtures_never_called" report attached to each test case using a pytest hook
# TODO implement full wildcarding!
                     req_obj: Optional[MockHttpRequest] = None,
                     **kwargs) -> Callable:
    """
    :param response: can be single response or list of responses (for changing responses to consecutive calls to same
    endpoint) where response is of type:
    - str: will get returned as requests.Response where the response string is the body
    - Exception: will get raised as if the requests method failed
    - Response: returned directly
    :param req_obj: MockHttpRequest if kwargs not provided
    :param kwargs: see help(MockHttpRequest.__init__) if not passing req_obj
    :return: the test class or function being decorated
    """
    expected_request = req_obj or MockHttpRequest(**kwargs)
    assert expected_request, 'failed to load MockHttpRequest object!'
    return get_decorated_callable(req_obj=expected_request, response=response)
