import functools
import inspect
import sys
from asyncio import iscoroutine, iscoroutinefunction
from typing import Callable, Optional, Union

from pytest_factory.framework.base_types import BaseMockRequest, Factory, BASE_RESPONSE_TYPE
from pytest_factory.framework.exceptions import MissingHandlerException
from pytest_factory.framework.mall import MALL


def make_factory(req_obj: Union[BaseMockRequest, str],
                 setup: Optional[Callable] = None,
                 teardown: Optional[Callable] = None,
                 response: Optional[BASE_RESPONSE_TYPE] = None,
                 handler_class: Optional[Callable] = None,
                 factory_name: Optional[str] = None) -> Callable:
    """
    Creates a factory. For use by contributors and plugin
    developers to create new factories. A factory is a decorator that modifies a TestClass or test_method_or_function
    in order to populate the store fixture with test mocks during the pytest collection phase.

    See http.py for an example of usage.

    :param req_obj: used as key to map to mock responses; either a BaseMockRequest type object or a string
    :param response: test double - generally a string or Response - should be None if handler_class defined
    :param handler_class: the class of the handler that this factory will mock - should be None if response is defined
    within the given factory is the correct test double
    :param factory_name: name of the factory that create test doubles for the
        returned Callable (TestClass or test_method_or_function; defaults to name of function that called this
        function
    :param setup: a function that does work before the test is run
    :param teardown: a function that does work after the test is complete
    :return: the test class or test function that is being decorated
    """

    factory_name = factory_name if factory_name else sys._getframe(1).f_code.co_name

    if not isinstance(req_obj, BaseMockRequest) and not isinstance(req_obj, str):
        try:
            req_obj = str(req_obj)
        except Exception as _:
            req_obj = id(req_obj)

    def register_test_func(pytest_func: Callable) -> Callable:
        test_name = pytest_func.__name__
        store = MALL.get_store(test_name=test_name)

        @functools.wraps(pytest_func)
        async def pytest_func_wrapper(*args, **kwargs):
            resp = setup(store) if setup else None
            if iscoroutine(pytest_func) or iscoroutinefunction(pytest_func):
                await pytest_func(*args, **kwargs)
            else:
                pytest_func(*args, **kwargs)
            if teardown:
                teardown(resp=resp, store=store)

        if hasattr(store, factory_name) and store._request_factory \
                and store._request_factory.FACTORY_NAME == factory_name:
            return pytest_func_wrapper
        store.update(factory_name=factory_name,
                     req_obj=req_obj, response=response)
        if response is None:
            final_handler_class = handler_class or store.request_handler_class or MALL.request_handler_class
            if not final_handler_class:
                raise MissingHandlerException
            if hasattr(req_obj, 'HANDLER_NAME'):
                key = req_obj.HANDLER_NAME
                init_request = MALL.monkey_patch_configs.get(key, {}).get('_get_handler_instance')
                handler = init_request(handler_class=final_handler_class, req_obj=req_obj)
            else:
                handler = final_handler_class(req_obj)
            store._request_factory = Factory(req_obj=factory_name, responses=handler)
            handler._pytest_store = store

        return pytest_func_wrapper

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return apply_func_recursive(target=callable_obj,
                                    test_func_wrapper=register_test_func)

    return callable_wrapper


def apply_func_recursive(test_func_wrapper: Callable, target: Callable) -> Callable:
    """
    if target is a class, this method will iterate and invoke func on
    each member of the class.
    if the member is itself a class, this function will recurse

    :param test_func_wrapper: the function that will return the test function after doing
        some work
    :param target: if a class, will find children and recurse, if method or function,
        will pass target to decorator
    """
    if inspect.isclass(target):
        for _, member in inspect.getmembers(target):
            if inspect.isfunction(member) or inspect.isclass(member) \
                    and member.__name__[:4] == 'Test':
                apply_func_recursive(test_func_wrapper=test_func_wrapper, target=member)

        return target
    elif inspect.isfunction(target):
        return test_func_wrapper(pytest_func=target)
