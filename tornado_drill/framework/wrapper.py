import inspect
import functools
import sys
from typing import Callable

from tornado_drill.mock_request import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.framework.stores import STORES


def get_fixture_decorator(
        req_obj: BaseMockRequest,
        response: MOCK_HTTP_RESPONSE = None,
        pre_test: Callable = None,
        post_test: Callable = None) -> Callable:
    """
    Define wrapper function used by all mocking fixture/decorators.  The wrapper is executed
    when the function loads, at which case we store all mock responses as HttpResponse objects for
    each path as a list in a dictionary indexed by path, then store that dictionary in the global
    mock response holder indexed by the function name.
    In the inner_wrapper, which is executed when the test function runs and the fixture is loaded,
    we load the dictionary of associated responses for the given function into the global object, where th
    mock server will search for them.  After we run the test function, we clear all the function specific
    response information so it will not interfere with other tests.
    :param req_obj: used as key to map to mock responses
    :param response: string or Response
    :param pre_test: function to be called just prior to executing test method; returns arguments to be passed to post_test
    :param post_test: function to be called just after executing test method; takes arguments returned by pre_test
    :return:
    """

    # this will grab the name of the decorator method that called this method
    fixture_name = sys._getframe(1).f_code.co_name

    # TODO generic logic for plugins goes here! set response = something

    def get_pytest_func_with_fixture(pytest_func: Callable) -> Callable:
        @functools.wraps(pytest_func)
        async def pytest_func_with_fixture(*args,
                                           **kwargs) -> MOCK_HTTP_RESPONSE:
            post_test_args = None
            test_name = pytest_func.__qualname__
            store = STORES.get_store(test_name)

            fixture_holder = None
            if hasattr(store, fixture_name):
                fixture_holder = getattr(store, fixture_name)
            else:
                fixture_holder = {}
                setattr(store, fixture_name, fixture_holder)

            fixture_holder[req_obj] = response

            post_test_args = pre_test() if pre_test else ()
            kwargs['store'] = store
            resp = await pytest_func(*args, **kwargs)
            return resp

            if post_test:
                if isinstance(post_test_args, tuple):
                    post_test(*post_test_args)
                else:
                    post_test(post_test_args)

        return pytest_func_with_fixture

    def fixture_decorator(callable_obj: Callable) -> Callable:
        return decorate_family(callable=callable_obj,
                               decorator=get_pytest_func_with_fixture)

    return fixture_decorator


def decorate_family(decorator: Callable, callable: Callable) -> Callable:
    """
    if callable is a class, this method will iterate and apply the decorator to
    all children.
    if a child is itself a class, this method will recurse

    :param decorator: the function that will return the decorated test function
    :param callable: the class or function or method on which the decorator
    is defined
    """
    if inspect.isclass(callable):
        for member in inspect.getmembers(callable):
            decorate_family(member)
        return callable
    elif inspect.isfunction(callable):
        return decorator(pytest_func=callable)
    else:
        raise Exception('should not happen!')
