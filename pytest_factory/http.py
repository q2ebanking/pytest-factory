from typing import Optional, Callable
from pytest_factory.framework.helpers import make_fixture_factory
from pytest_factory.mock_request_types import MockHttpRequest, \
    MOCK_HTTP_RESPONSE


def mock_http_server(response: MOCK_HTTP_RESPONSE = None,
                     req_obj: Optional[MockHttpRequest] = None,
                     **kwargs) -> Callable:
    """
    TODO implement full wildcarding!
    TODO load from swagger, WSDL, etc.

    TODO document method fully

    :param response: can be single response or list of responses (for changing
    responses to consecutive calls to same endpoint) where response is of type:
    - str: will get returned as requests.Response where the response string is
        the body
    - Exception: will get raised as if the requests method failed
    - Response: returned directly
    - Callable: must be a function that takes the req_obj as argument and
        returns one of the above types
        - for when user wants mock server to have some correlation between
            request and response (like id of requested asset)
        - for more sophisticated behavior, consider a fixture adapter instead
    :param req_obj: MockHttpRequest if kwargs not provided
    :param kwargs: see help(MockHttpRequest.__init__) if not passing req_obj
    :return: the test class or function being decorated
    """
    expected_request = req_obj or MockHttpRequest(**kwargs)
    assert expected_request, 'failed to load MockHttpRequest object!'  # todo make test for this
    return make_fixture_factory(req_obj=expected_request, response=response)
