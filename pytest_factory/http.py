from typing import Optional, Callable

from pytest_factory.framework.factory import make_factory
from pytest_factory.framework.http_types import HTTP_METHODS, MockHttpRequest, MOCK_HTTP_RESPONSE
from pytest_factory.framework.exceptions import RequestNormalizationException


def mock_http_server(response: MOCK_HTTP_RESPONSE = None,
                     req_obj: Optional[MockHttpRequest] = None,
                     method: Optional[str] = HTTP_METHODS.GET.value,
                     path: Optional[str] = None, **kwargs) -> Callable:
    """
    decorate your test method or class with this factory to generate test doubles for an HTTP depended-on
    component

    :param response: defaults to empty string; can be single response or list of responses (for changing
    responses to consecutive calls to same endpoint) where response is of type:
    - str: will get returned as requests.Response where the response string is
        the body
    - Exception: will get raised as if the requests method failed and not attempt to generate a response
    - Response: returned directly
    - Callable: must be a function that takes the req_obj as argument and
        returns one of the above types
        - for when user wants mock server to have some correlation between
            request and response (like id of requested asset)
        - for raising Exceptions conditioned on content of the request
        - for more sophisticated behavior, consider creating a plugin instead
    :param req_obj: MockHttpRequest if kwargs not provided
    :param method: if req_obj not provided, HTTP method for creating MockHttpRequest
    :param path: if req_obj not provided, url path for creating MockHttpRequest
    :param kwargs: see help(MockHttpRequest.__init__) if not passing req_obj
    :return: the test class or function being decorated
    """
    try:
        expected_request = req_obj or MockHttpRequest(method=method, path=path, **kwargs)
    except Exception as ex:
        raise RequestNormalizationException(req_obj_cls=MockHttpRequest, method=method, path=path, ex=ex, **kwargs)
    if isinstance(response, str):
        response = response.encode()
    return make_factory(req_obj=expected_request, response=response)
