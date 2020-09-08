import inspect
import functools
import sys
from typing import Callable

from tornado_drill.fixtures.base import BaseMockRequest
from tornado_drill.fixtures.http import MOCK_HTTP_RESPONSE


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
    During the test collection, the pytest_generate_tests pytest hook will check all the lists of responses
    for each path/function combination, and if the length of the list is more than one it will parameterize
    the fixture.
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
            try:
                mocks_arg = kwargs.get('fixtures')
                assert mocks_arg is not None, 'Missing mocks arg for fixture: {}'.format(
                    fixture_name)

                # Callable is a function, meaning the fixture is defined on a function
                fixture_holder = None
                if hasattr(mocks_arg, fixture_name):
                    fixture_holder = getattr(mocks_arg, fixture_name)
                else:
                    fixture_holder = {}
                    setattr(mocks_arg, fixture_name, fixture_holder)

                fixture_holder[req_obj] = response

                post_test_args = pre_test() if pre_test else ()

                resp = await pytest_func(*args, **kwargs)
                return resp

            finally:
                if post_test:
                    if isinstance(post_test_args, tuple):
                        post_test(*post_test_args)
                    else:
                        post_test(post_test_args)

        return pytest_func_with_fixture

    def fixture_generator(callable_obj: Callable) -> Callable:
        if inspect.isclass(callable_obj):
            methods = inspect.getmembers(
                callable_obj, predicate=lambda x: inspect.isfunction(x))  # pylint ignore: unnecessary-lambda
            if methods is None:
                return callable_obj

            for name, method in methods:
                # If fixture is defined at the class level, need to loop through
                # and add them to each function in the class, so they will be processed
                # correctly
                setattr(callable_obj, name,
                        get_pytest_func_with_fixture(pytest_func=method))

            return callable_obj
        else:
            return get_pytest_func_with_fixture(pytest_func=callable_obj)

    return fixture_generator
