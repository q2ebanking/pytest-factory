"""
- access settings to load RequestHandler class and defaults
- generate the MockHttpRequest
- instantiate the RequestHandler to be tested
- load RequestHandler with the generated request
- attach run_test to RequestHandler
- return RequestHandler to the Store which will pass it to the test function
"""
import pytest
import inspect
from functools import wraps
from typing import Callable, Optional

from tornado.web import Application

from tornado_drill.mock_request_types import MockHttpRequest
from tornado_drill.framework.settings import SETTINGS
from tornado_drill.framework.stores import STORES
from tornado_drill.framework.helpers import decorate_family


async def run_test(self):
    """
    this method will be bound to the RequestHandler and provides a way to
    advance the state of the RequestHandler while returning the response to the
    test method for assertions
    """
    method_name = self.request.method.lower()
    assert hasattr(self, method_name)
    result = getattr(self, method_name)()
    if inspect.isawaitable(result):
        await result

    # TODO maybe reconstitute this as a Response object?
    if self._write_buffer:
        return self._write_buffer[len(self._write_buffer) - 1].decode('utf-8')


def mock_request(handler_class: Optional[Callable] = None,
                 req_obj: Optional[MockHttpRequest] = None,
                 **kwargs) -> Callable:
    """
    :param handler_class: class of RequestHandler being tested
    :param req_obj: MockHttpRequest object; required if not passing kwargs
    :param **kwargs: kwargs for MockHttpRequest if not passing req_obj param
    :return: returns modified test function or class
    """
    req_obj = req_obj or MockHttpRequest(**kwargs)

    handler_class = handler_class or SETTINGS.default_request_handler_class
    assert handler_class, 'could not load class of RequestHandler being tested!'

    handler_overrides = {**{'run_test': run_test},  # we have to bury this here unfortunately to avoid circular imports
                         **SETTINGS.handler_overrides}  # but this line will guarantee that plugins can still override it

    for attribute, override in handler_overrides.items():
        if isinstance(override, Callable):  # setting methods on the class because otherwise they don't get 'self'
            setattr(handler_class, attribute, override)

    handler = handler_class(Application(), req_obj)

    for attribute, override in handler_overrides.items():
        if not isinstance(override, Callable):  # setting other properties on the object
            setattr(handler, attribute, override)

    def func_wrapper(pytest_func: Callable) -> Callable:
        @wraps(pytest_func)
        async def pytest_func_with_handler(*args, **kwargs) -> None:
            test_name = pytest_func.__qualname__
            kwargs['handler'] = handler
            if not kwargs.get('store'):
                kwargs['store'] = STORES.get_store(test_name)
            return await pytest_func(*args, **kwargs)

        return pytest_func_with_handler

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return decorate_family(callable=callable_obj, decorator=func_wrapper)

    return callable_wrapper


@pytest.fixture(scope='function')
def handler(request):
    """
    handler fixture

    this gets overridden later with the actual handler but we are defining it here so pytest picks it up
    :return:
    """
    pass
