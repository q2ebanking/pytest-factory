"""
contains fixture factory @mock_request used to create the request to be passed to RequestHandler
before test execution.

also definitions for methods to be bound to RequestHandler that can be used to wrap execution of RequestHandler methods
for testing purposes. this module comes with run_test() but plugins can define many more with the handler_overrides
parameter.

finally, this contains the pytest fixture definition. make sure this file is imported by pytest.py so the framework
can pick this up, or you will not have the fixture available in tests!
"""
import inspect
import functools
from typing import Callable, Optional

from tornado.web import Application, RequestHandler

from pytest_factory.mock_request_types import MockHttpRequest
from pytest_factory.framework.settings import SETTINGS
from pytest_factory.framework.stores import STORES
from pytest_factory.framework.helpers import _apply_func_recursive


async def _run_test(self, assert_no_missing_calls: bool = False, assert_no_extra_calls: bool = True):
    """
    this method will be bound to the RequestHandler, which is why it must receive the parameter 'self',
    and provides a way to advance the state of the RequestHandler while returning the response to the
    test method for assertions

    :param assert_no_missing_calls: if set to True, will raise AssertionError if handler calls
    a fixture less times than it has responses; will no longer issue warning via LOGGER
    :param assert_no_extra_calls: if set to False, will no longer raise AssertionError if handler calls
    a fixture more times than it has responses; will issue warnings instead via LOGGER
    :return:
    """

    store = self._pytest_store
    if assert_no_extra_calls is False:
        store.assert_no_extra_calls = assert_no_extra_calls

    method_name = self.request.method.lower()
    assert hasattr(self, method_name)
    result = getattr(self, method_name)()
    if inspect.isawaitable(result):
        await result

    store.check_no_uncalled_fixtures(raise_assertion_error=assert_no_missing_calls)

    if self._write_buffer:
        return self._write_buffer[len(self._write_buffer) - 1].decode('utf-8')


def _get_handler_instance(handler_class: Callable, req_obj: MockHttpRequest) -> RequestHandler:
    handler_class = handler_class or SETTINGS.default_request_handler_class
    assert handler_class, 'could not load class of RequestHandler being tested!'

    handler_overrides = {**{'run_test': _run_test},  # this is here instead of settings.py to avoid circular imports
                         **SETTINGS.handler_overrides}  # but this will guarantee that plugins can still override it

    for attribute, override in handler_overrides.items():
        if isinstance(override, Callable):  # setting methods on the handler class
            setattr(handler_class, attribute, override)

    handler = handler_class(Application(), req_obj)

    for attribute, override in handler_overrides.items():
        if not isinstance(override, Callable):  # setting other properties on the handler object
            setattr(handler, attribute, override)

    return handler


def mock_request(handler_class: Optional[Callable] = None,
                 req_obj: Optional[MockHttpRequest] = None,
                 **kwargs) -> Callable:
    """
    TODO
    :param handler_class: class of RequestHandler being tested
    :param req_obj: MockHttpRequest object; required if not passing kwargs
    :param kwargs: kwargs for MockHttpRequest if not passing req_obj param
    :return: returns modified test function or class
    """
    req_obj = req_obj or MockHttpRequest(**kwargs)
    req_obj.FIXTURE_NAME = 'mock_request'

    handler = _get_handler_instance(handler_class=handler_class, req_obj=req_obj)

    def register_test_func(pytest_func: Callable) -> Callable:
        store = STORES.get_store(test_name=pytest_func.__name__)
        store.handler = handler
        handler._pytest_store = store

        @functools.wraps(pytest_func)
        async def modified_pytest_func(*args, **qwargs):
            """
            we need to override test function because the handler arg can be overridden
            :param args:
            :param qwargs: odd name to avoid shadowing kwargs
            :return:
            """
            if store.handler != handler:
                store.handler = handler
                handler._pytest_store = store

            await pytest_func(*args, **qwargs)

        return modified_pytest_func

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return _apply_func_recursive(callable=callable_obj, func=register_test_func)

    return callable_wrapper
