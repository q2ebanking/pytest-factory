import functools
import inspect
import sys
from asyncio import iscoroutine, iscoroutinefunction
from typing import Callable, Optional, Union

from pytest_factory.framework.base_types import BaseMockRequest, BASE_RESPONSE_TYPE
from pytest_factory.framework.parse_configs import DEFAULT_FOLDER_NAME
from pytest_factory.framework.exceptions import MissingHandlerException
from pytest_factory.framework.mall import MALL


def make_factory(req_obj: Union[BaseMockRequest, str],
                 setup: Optional[Callable] = None,
                 teardown: Optional[Callable] = None,
                 response: Optional[BASE_RESPONSE_TYPE] = None,
                 factory_name: Optional[str] = None) -> Callable:
    """
    Creates a factory. For use by contributors and plugin
    developers to create new factories. A factory is a decorator that modifies a TestClass or test_method_or_function
    in order to populate the store fixture with test doubles during the pytest collection phase.

    See http.py for an example of usage.

    :param req_obj: used as key to map to mock responses; either a BaseMockRequest type object or a string
    :param response: test double or list of test doubles - generally a string or Message;
        should be None if the test double is the request;
        if a list of responses, this factory will return each response in order
    :param factory_name: name of the factory that create test doubles for the
        returned Callable (TestClass or test_method_or_function; defaults to name of function that called this
        function
    :param setup: a function that does work before the test is run
    :param teardown: a function that does work after the test is complete
    :return: the test class or test function that is being decorated
    """

    factory_name = factory_name if factory_name else sys._getframe(1).f_code.co_name
    if factory_name == '<module>':
        factory_name = 'make_factory'

    def register_test_func(pytest_func: Callable) -> Callable:
        """
        is executed during pytest collection; the store is bound to the test case at this time
        if response is not None, and store.sut is not yet assigned, this factory will create the
        system-under-test (SUT).
        """

        if iscoroutine(pytest_func) or iscoroutinefunction(pytest_func):
            @functools.wraps(pytest_func)
            async def pytest_func_wrapper(*args, **kwargs):
                """
                is executed during pytest run; executes setup, then the test function, finally teardown
                """
                resp = setup() if setup else None
                await pytest_func(*args, **kwargs)
                if teardown:
                    teardown(resp=resp)
        else:
            @functools.wraps(pytest_func)
            def pytest_func_wrapper(*args, **kwargs):
                """
                is executed during pytest run; executes setup, then the test function, finally teardown
                """
                resp = setup() if setup else None
                pytest_func(*args, **kwargs)
                if teardown:
                    teardown(resp=resp)

        test_name = pytest_func.__name__
        module_parts = pytest_func.__module__.split('.')
        if len(module_parts) > 1:
            test_dir = module_parts[-2]
        elif len(module_parts) == 1:
            p = MALL.get_full_path()
            p_list = list(p.rglob(module_parts[0]+'.py'))
            test_dir = p_list[0].parent.name
        else:
            test_dir = DEFAULT_FOLDER_NAME
        store = MALL.get_store(test_name=test_name, test_dir=test_dir)
        response_is_sut = False
        if response is None:
            response_is_sut = True
            if hasattr(req_obj, 'sut_callable') and req_obj.sut_callable:
                sut_callable = req_obj.sut_callable
            else:
                sut_callable = MALL.sut_callable
            if not sut_callable:
                raise MissingHandlerException
            if hasattr(req_obj, 'HANDLER_NAME'):
                key = req_obj.HANDLER_NAME
                constructor = MALL.get_constructor(handler_type=key)
                sut = constructor(sut_callable=sut_callable, req_obj=req_obj)
            else:
                sut = sut_callable(req_obj)
            final_response = sut
        else:
            final_response = response
        store.update(factory_name=factory_name,
                     req_obj=req_obj, response=final_response, response_is_sut=response_is_sut)

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
