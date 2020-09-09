from typing import Union, Dict, Optional, Callable
from tornado_drill.framework.helpers import get_decorated_callable
from tornado_drill.mock_request_types import MockHttpRequest, \
    MOCK_HTTP_RESPONSE

OPT_STR_DICT = Optional[Union[str, Dict[str, str]]]


def mock_http_server(response: MOCK_HTTP_RESPONSE,  # TODO this should be an array to allow for
# changing response over time
# and also find a way to track this! like a "fixtures_never_called" report
# attached to each test case using a pytest hook
                     req_obj: Optional[MockHttpRequest] = None,
                     **kwargs) -> Callable:
    """
    :param response: actual response from mock server. can be a list to
    represent changing responses. final response in list repeats indefinitely
    if handler persists in calling.
    :param req_obj: MockHttpRequest if kwargs not provided
    :param **kwargs: see help(MockHttpRequest.__init__) if not passing req_obj
    :return: the test class or function being decorated
    """
    expected_request = req_obj or MockHttpRequest(**kwargs)
    assert expected_request, 'failed to load MockHttpRequest object!'
    return get_decorated_callable(req_obj=expected_request, response=response)
