"""
contains @mock_request factory used to create the request to be passed to RequestHandler
before test execution.

also definitions for methods to be bound to RequestHandler that can be used to wrap execution of RequestHandler methods
for testing purposes. this module comes with run_test() but plugins can define many more with the handler_overrides
parameter.
"""
import inspect
import functools
from typing import Callable, Optional

from pytest_factory.http import MockHttpRequest
from pytest_factory.framework.mall import MALL
from pytest_factory.framework.factory import _apply_func_recursive
from pytest_factory.monkeypatch.tornado import get_handler_instance


def mock_request(handler_class: Optional[Callable] = None,
                 req_obj: Optional[MockHttpRequest] = None,
                 response_parser: Optional[Callable] = None,
                 **kwargs) -> Callable:
    """
    generic tornado request double factory; can be invoked within a wrapper to customize

    :param handler_class: class of RequestHandler being tested
    :param req_obj: MockHttpRequest object; required if not passing kwargs
    :param response_parser: a method to parse the handler response for easier testing
    :param kwargs: kwargs for MockHttpRequest if not passing req_obj param
    :return: returns modified test function or class
    """
    req_obj = req_obj or MockHttpRequest(**kwargs)
    req_obj.FACTORY_NAME = 'mock_request'

    def register_test_func(pytest_func: Callable) -> Callable:
        if not req_obj and inspect.isclass(pytest_func):
            inspect.getmembers(pytest_func)  # TODO is this doing anything?
        store = MALL.get_store(test_name=pytest_func.__name__)

        final_handler_class = handler_class if handler_class else store.request_handler_class \
                                                                  or MALL.request_handler_class
        handler = get_handler_instance(handler_class=final_handler_class, req_obj=req_obj)
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
        return _apply_func_recursive(kallable=callable_obj, func=register_test_func)

    return callable_wrapper
