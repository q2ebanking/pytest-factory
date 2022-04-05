from typing import Callable, List, Optional, Any

from pytest_factory.framework.mall import MALL


def get_generic_caller(method_name: str, request_callable: Callable,
                       response_callable: Optional[Callable] = None, is_async=False) -> Callable:
    """
    this method will redefine the method with method_name in the module being
    monkeypatched while including in the new method the name of test function
    so it can look up mock responses

    :param method_name: the name of the method in the module being
        monkeypatched for this test
    :param request_callable: class of the request object or function that will
        return one; must always take method_name as kwarg
    :param response_callable: class of the response object or function that
        will return one
    :param is_async: must set to True if the monkeypatched method is async
    :return: the method that will replace the old one in the module being
        monkeypatched
    """

    def generic_caller(*args, **kwargs) -> Any:
        """
        this method replaces method_name in the module being monkeypatched
        """

        req_obj = request_callable(method_name=method_name, *args, **kwargs)
        store = MALL.get_store()
        mock_response = store.get_next_response(factory_name=req_obj.FACTORY_NAME, req_obj=req_obj)

        if isinstance(mock_response, Exception):
            # TODO are we testing this? maybe handle inside get_next_response?
            raise mock_response

        if response_callable:
            mock_response = response_callable(mock_response=mock_response, *args, **kwargs)
        return mock_response

    if is_async:
        async def async_generic_caller(*args, **kwargs) -> Any:
            return generic_caller(*args, **kwargs)

        return async_generic_caller
    else:

        return generic_caller


def update_monkey_patch_configs(factory_name: str, callable_obj: Any, patch_methods: List[Callable]):
    """
    Call this method at the bottom of your non HQ mock module to set up the fixtures.
    :param factory_name: name of the mock module and decorator
    :param callable_obj: class or module that will have its method monkeypatched
    :param patch_methods: list of methods that will monkeypatch the above callable_obj
    :return:
    """
    MALL.monkey_patch_configs[factory_name] = {
        'callable': callable_obj,
        'patch_methods': patch_methods
    }
