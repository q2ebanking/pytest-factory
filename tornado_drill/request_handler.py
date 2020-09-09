"""
- access settings to load RequestHandler class and defaults
- generate the MockHttpRequest
- instantiate the RequestHandler to be tested
- load RequestHandler with the generated request
- attach run_test to RequestHandler
- return RequestHandler to the Store which will pass it to the test function
"""
from functools import wraps
from typing import Callable, Optional

from tornado import Application

from tornado_drill.fixtures.http import MockHttpRequest
from tornado_drill.framework.settings import SETTINGS


def mock_request(handler_class: Optional[Callable] = None,
                 req_obj: Optional[MockHttpRequest] = None,
                 **kwargs) -> Callable:
    """
    :param handler_class: class of RequestHandler being tested
    :param req_obj: MockHttpRequest object; required if not passing kwargs
    :param **kwargs: kwargs for MockHttpRequest if not passing req_obj param
    :return: returns modified test function or class TODO also class?
    """
    req_obj = req_obj or MockHttpRequest(**kwargs)

    handler_class = handler_class or SETTINGS.default_request_handler_class
    assert handler_class, 'could not load class of RequestHandler being tested!'

    handler_class(Application(), req_obj, **kwargs)

    def wrapper(pytest_func: Callable) -> Callable:
        @wraps(pytest_func)
        async def pytest_func_with_handler(*args, **kwargs) -> None:

            return await pytest_func(*args, **kwargs)

        return pytest_func_with_handler

        # check if callable is a class!!!

    return wrapper
