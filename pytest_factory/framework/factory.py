import inspect
import sys
from typing import Callable, Optional, List, Union

import pytest_factory.outbound_mock_request as mrt
from pytest_factory.framework.stores import STORES


def make_factory(req_obj: Union[mrt.BaseMockRequest, str],
                 response: mrt.MOCK_HTTP_RESPONSE,
                 failure_modes: Optional[List[mrt.FailureMode]] = None,
                 factory_names: Optional[Union[List[str], str]] = None) -> Callable:
    """
    Creates a factory. For use by contributors and plugin
    developers to create new factories. A factory is a decorator that modifies a TestClass or test_method_or_function
    in order to populate the store fixture with test mocks during the pytest collection phase.

    See http.py for an example of usage.

    :param req_obj: used as key to map to mock responses; either a BaseMockRequest type object or a string
    :param response: string or Response
    :param failure_modes: defines the ways the service mocked by this factory
        could fail independent of the functioning of the component under test;
        used if your test is marked pytest.mark.cause_failures
    :param factory_names: name of the fixture factory that will be applied to
        returned Callable; defaults to name of function that called this
        function
    :return: the test class or test function that is being decorated
    """

    factory_names = factory_names if factory_names else sys._getframe(1).f_code.co_name
    factory_names = factory_names if isinstance(factory_names, list) else [factory_names]
    failure_modes = failure_modes or {}
    if not isinstance(req_obj, mrt.BaseMockRequest) and not isinstance(req_obj, str):
        try:
            req_obj = str(req_obj)
        except Exception as _:
            req_obj = id(req_obj)

    def register_test_func(pytest_func: Callable) -> Callable:
        test_name = pytest_func.__name__
        STORES.update(test_name=test_name, factory_names=factory_names,
                      req_obj=req_obj, response=response,
                      failure_modes=failure_modes)

        return pytest_func

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return _apply_func_recursive(kallable=callable_obj,
                                     func=register_test_func)

    return callable_wrapper


def _apply_func_recursive(func: Callable, kallable: Callable) -> Callable:
    """
    if callable is a class, this method will iterate and apply the decorator to
    all children.
    if a child is itself a class, this method will recurse

    :param func: the function that will return the test function after doing
        some work
    :param kallable: if a class, will find children and recurse, if method or function,
        will pass kallable to func and invoke func
    is defined
    """
    if inspect.isclass(kallable):
        for _, member in inspect.getmembers(kallable):
            if inspect.isfunction(member) or inspect.isclass(member) \
                    and member.__name__[:4] == 'Test':
                _apply_func_recursive(func=func, kallable=member)

        return kallable
    elif inspect.isfunction(kallable):
        return func(pytest_func=kallable)
