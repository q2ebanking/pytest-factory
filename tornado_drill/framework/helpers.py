import inspect
import functools
import sys
from typing import Callable

from tornado_drill.mock_request_types import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.framework.stores import STORES


def get_decorated_callable(
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

    def pytest_func_wrapper(pytest_func: Callable) -> Callable:
        @functools.wraps(pytest_func)
        async def pytest_func_with_fixture(*args, **kwargs):
            test_name = pytest_func.__name__
            store = STORES.get_store(test_name)

            if hasattr(store, fixture_name):
                fixture_holder = getattr(store, fixture_name)
            else:
                fixture_holder = {}
                setattr(store, fixture_name, fixture_holder)

            fixture_holder[req_obj] = response

            post_test_args = pre_test() if pre_test else ()
            kwargs['store'] = store
            await pytest_func(*args, **kwargs)

            if post_test:
                if isinstance(post_test_args, tuple):
                    post_test(*post_test_args)
                else:
                    post_test(post_test_args)

        return pytest_func_with_fixture

    def decorated_callable_wrapper(callable_obj: Callable) -> Callable:
        return decorate_family(callable=callable_obj,
                               decorator=pytest_func_wrapper)

    return decorated_callable_wrapper


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
        for _, member in inspect.getmembers(callable):
            if inspect.isfunction(member) or inspect.isclass(member) and member.__name__[:4] == 'Test':
                decorate_family(decorator=decorator, callable=member)

        return callable
    elif inspect.isfunction(callable):
        return decorator(pytest_func=callable)
