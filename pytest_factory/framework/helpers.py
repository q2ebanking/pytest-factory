import inspect
import sys
from typing import Callable, Optional, Any, List, Union

import pytest_factory.mock_request_types as mrt
from pytest_factory.framework.stores import STORES


def make_fixture_factory(req_signature: Union[mrt.BaseMockRequest, str],
                         response: mrt.MOCK_HTTP_RESPONSE,
                         failure_modes: Optional[List[mrt.FailureMode]] = None,
                         factory_name: Optional[str] = None) -> Callable:
    """
    Creates a fixture factory. For use by contributors and plugin
    developers to create new fixture factories.

    See http.py for an example of usage.

    :param req_signature: used as key to map to mock responses; either a BaseMockRequest type object or a string
    :param response: string or Response
    :param failure_modes: defines the ways the service mocked by this factory
        could fail independent of the functioning of the component under test;
        used if your test is marked pytest.mark.cause_failures
    :param factory_name: name of the fixture factory that will be applied to
        to returned Callable; defaults to name of function that called this
        function
    :return: the test class or test function that is being decorated
    """

    factory_name = factory_name or sys._getframe(1).f_code.co_name
    failure_modes = failure_modes or {}

    def register_test_func(pytest_func: Callable) -> Callable:
        test_name = pytest_func.__name__
        key = req_signature if isinstance(req_signature, str) else hash(req_signature)
        # TODO this needs to handle plugin adapters with compound factory names
        STORES.update(test_name=test_name, factory_name=factory_name,
                      key=key, response=response,
                      failure_modes=failure_modes)

        return pytest_func

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return _apply_func_recursive(callable=callable_obj,
                                     func=register_test_func)

    return callable_wrapper


def _apply_func_recursive(func: Callable, callable: Callable) -> Callable:
    """
    if callable is a class, this method will iterate and apply the decorator to
    all children.
    if a child is itself a class, this method will recurse

    :param func: the function that will return the test function after doing
        some work
    :param callable: if a class, will find children and recurse, if function
        will apply func
    is defined
    """
    if inspect.isclass(callable):
        for _, member in inspect.getmembers(callable):
            if inspect.isfunction(member) or inspect.isclass(member) \
                    and member.__name__[:4] == 'Test':
                _apply_func_recursive(func=func, callable=member)

        return callable
    elif inspect.isfunction(callable):
        return func(pytest_func=callable)


def get_generic_caller(method_name: str, test_func_name: str,
                       request_callable: Callable,
                       response_callable: Optional[Callable] = None) -> Callable:
    """
    this method will redefine the method with method_name in the module being
    monkeypatched while including in the new method the name of test function
    so it can look up mock responses

    :param method_name: the name of the method in the module being
        monkeypatched for this test
    :param test_func_name: name of the test function that this fixture is for
    :param request_callable: class of the request object or function that will
        return one; must always take method_name as kwarg
    :param response_callable: class of the response object or function that
        will return one
    :return: the method that will replace the old one in the module being
        monkeypatched
    """

    def generic_caller(*args, **kwargs) -> Any:
        """
        this method replaces method_name in the module being monkeypatched
        """

        req_obj = request_callable(method_name=method_name, *args, **kwargs)
        factory_name = req_obj.FACTORY_NAME
        mock_response = STORES.get_next_response(test_name=test_func_name,
                                                 factory_name=factory_name,
                                                 req_obj=req_obj)
        if isinstance(mock_response, Callable):
            mock_response = mock_response(req_obj)

        if isinstance(mock_response, Exception):
            raise mock_response

        if response_callable:
            mock_response = response_callable(
                mock_response=mock_response, *args, **kwargs)
        return mock_response

    return generic_caller
