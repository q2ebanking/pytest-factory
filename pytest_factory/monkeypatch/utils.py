from typing import Callable, Dict, Optional, Any

from pytest_factory.framework.mall import MALL


def get_generic_caller(request_callable: Callable, method_name: Optional[str] = None,
                       response_callable: Optional[Callable] = None, is_async=False) -> Callable:
    """
    this method will redefine the method with method_name in the module being
    monkeypatched while including in the new method the name of test function
    so it can look up mock responses
    if the method being monkeypatched is for sending requests to a DOC, then it must extend store.messages
    with the request and response

    :param method_name: the name of the method in the module being
        monkeypatched for this test unless this is unambiguous
    :param request_callable: class of the request object or function that will
        return one; must always take keyword argument method_name and return a
        MockHttpRequest
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
        if method_name:
            kwargs['method_name'] = method_name

        req_obj = request_callable(*args, **kwargs)
        store = MALL.get_store()
        mock_response = store.get_next_response(factory_name=req_obj.FACTORY_NAME, req_obj=req_obj)

        if isinstance(mock_response, Exception):
            raise mock_response

        if response_callable:
            mock_response = response_callable(mock_response=mock_response, *args, **kwargs)
        store.messages.extend([req_obj, mock_response])
        return mock_response

    if is_async:
        async def async_generic_caller(*args, **kwargs) -> Any:
            return generic_caller(*args, **kwargs)

        return async_generic_caller
    else:

        return generic_caller


def update_monkey_patch_configs(callable_obj: Any,
                                patch_members: Dict[str, Any],
                                constructor: Optional[Callable] = None):
    """
    Call this method at the bottom of your non HQ mock module to set up the fixtures.
    :param callable_obj: class or module that will have its method monkeypatched
    :param patch_members: dictionary of members where keys are the name of the member of callable_obj to be patched,
        and the values are the replacement member
    :return:
    """
    key = callable_obj.__name__
    patch_configs = MALL.monkey_patch_configs.get(key)
    if patch_configs:
        MALL.monkey_patch_configs[key].get('patch_methods').update(patch_members)
        if constructor:
            MALL.monkey_patch_configs[key]['constructor'] = constructor
    else:
        MALL.monkey_patch_configs[callable_obj.__name__] = {
            'callable': callable_obj,
            'patch_methods': patch_members,
            'constructor': constructor
        }
