import inspect
import sys
from typing import Callable, Optional, Any

from tornado_drill.mock_request_types import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.framework.stores import STORES


def get_decorated_callable(req_obj: BaseMockRequest, response: MOCK_HTTP_RESPONSE) -> Callable:
    """
    Generic decorator maker. For use by contributors and plugin developers to create new fixture decorators. See http.py
    for an example of usage.

    NOTE that this method is dependent on sys._getframe(1) returning the interface decorator itself e.g.
    tornado_drill.http.mock_http_server or it may incorrectly index the fixture in the Store

    :param req_obj: used as key to map to mock responses
    :param response: string or Response
    :return: the test class or test function that is being decorated
    """

    # this will grab the name of the decorator method that called this method
    fixture_name = sys._getframe(1).f_code.co_name

    def register_test_func(pytest_func: Callable) -> Callable:
        test_name = pytest_func.__name__
        STORES.update(test_name=test_name, fixture_name=fixture_name, req_obj=req_obj, response=response)

        return pytest_func

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return _apply_func_recursive(callable=callable_obj, func=register_test_func)

    return callable_wrapper


def _apply_func_recursive(func: Callable, callable: Callable) -> Callable:
    """
    if callable is a class, this method will iterate and apply the decorator to
    all children.
    if a child is itself a class, this method will recurse

    :param func: the function that will return the test function after doing some work
    :param callable: if a class, will find children and recurse, if function will apply func
    is defined
    """
    if inspect.isclass(callable):
        for _, member in inspect.getmembers(callable):
            if inspect.isfunction(member) or inspect.isclass(member) and member.__name__[:4] == 'Test':
                _apply_func_recursive(func=func, callable=member)

        return callable
    elif inspect.isfunction(callable):
        return func(pytest_func=callable)


def get_generic_caller(method_name: str, test_func_name: str,
                       req_generator: Callable,
                       resp_generator: Optional[Callable] = None) -> Callable:
    """
    this method will redefine the method with method_name in the module being monkeypatched
    while including in the new method the name of test function so it can look up mock responses

    :param method_name: the name of the method in the module being monkeypatched for this test
    :param test_func_name: name of the test function that this fixture is for
    :param req_generator: class of the request object or function that will return one; must always
        take method_name as kwarg
    :param resp_generator: class of the response object or function that will return one
    :return: the method that will replace the old one in the module being monkeypatched
    """

    def generic_caller(*args, **kwargs) -> Any:
        """
        this method replaces method_name in the module being monkeypatched
        """

        req_obj = req_generator(method_name=method_name, *args, **kwargs)
        fixture_name = req_obj.FIXTURE_NAME
        mock_response = STORES.get_next_response(test_name=test_func_name,
                                                 fixture_name=fixture_name,
                                                 req_obj=req_obj)
        if isinstance(mock_response, Callable):
            mock_response = mock_response(req_obj)

        if isinstance(mock_response, Exception):
            raise mock_response

        if resp_generator:
            mock_response = resp_generator(mock_response)
        return mock_response

    return generic_caller

# def parameterize_test(item: Item) -> List[Item]:
#     new_tests = []
#
#     store = STORES.get_store(item.name)
#
#
#
#     return new_tests
