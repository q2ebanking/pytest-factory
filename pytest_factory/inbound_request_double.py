"""
contains @mock_request factory used to create the request to be passed to RequestHandler
before test execution.

also definitions for methods to be bound to RequestHandler that can be used to wrap execution of RequestHandler methods
for testing purposes. this module comes with run_test() but plugins can define many more with the handler_overrides
parameter.
"""
import inspect
import functools
from typing import Callable, Optional, List, Dict, Any

from tornado.web import Application, RequestHandler

from pytest_factory.http import MockHttpRequest
from pytest_factory.framework.mall import MALL
from pytest_factory.framework.factory import _apply_func_recursive


def _get_handler_instance(req_obj: MockHttpRequest, handler_class: Optional[Callable] = None,
                          response_parser: Optional[Callable] = None,
                          handler_class_args: Optional[List[Any]] = None,
                          handler_class_kwargs: Optional[Dict[str, Any]] = None) -> RequestHandler:
    if not handler_class:
        handler_class = MALL.request_handler_class
    # TODO raise exception here instead! or are we already doing that earlier?
    assert handler_class, 'could not load class of RequestHandler being tested!'

    async def _run_test(self, assert_no_missing_calls: bool = None,
                        assert_no_extra_calls: bool = None):
        """
        TODO the two bool params need to pull defaults from the USER'S configs, via Mall
        this method will be bound to the RequestHandler, which is why it must receive the parameter 'self',
        and provides a way to advance the state of the RequestHandler while returning the response to the
        test method for assertions

        :param assert_no_missing_calls: if set to True, will raise AssertionError if handler calls
        a test double less times than it has responses; will no longer issue warning via logger
        this can also be set in conftest by setting ASSERT_NO_MISSING_CALLS to True
        :param assert_no_extra_calls: if set to False, will no longer raise AssertionError if handler calls
        a test double more times than it has responses; will issue warnings instead via logger
        :return:
        """
        # TODO log errors out here!
        store = self._pytest_store
        if assert_no_extra_calls is not None:
            store.assert_no_extra_calls = assert_no_extra_calls
        else:
            store.assert_no_extra_calls = MALL.assert_no_extra_calls

        if assert_no_missing_calls is not None:
            store.assert_no_missing_calls = assert_no_missing_calls
        else:
            store.assert_no_missing_calls = MALL.assert_no_missing_calls

        method_name = self.request.method.lower()
        assert hasattr(self, method_name), ''  # TODO do seomthing here?
        result = getattr(self, method_name)()
        if inspect.isawaitable(result):
            await result

        store.check_no_uncalled_test_doubles()

        if self._write_buffer:
            raw_resp = self._write_buffer[len(self._write_buffer) - 1].decode('utf-8')
            parsed_resp = response_parser(raw_resp) if response_parser else raw_resp
            return parsed_resp

    # TODO this could be done via pytest.fixture for monkeypatch - have it look up the handler in the store!
    # handler_overrides = {**{'run_test': _run_test}, **MALL.handler_monkeypatches}

    # TODO note that this is the one place with a true dependency on tornado
    def finish(self: Any, **kwargs: Any) -> None:  # pylint: disable=unused-argument
        return self._write_buffer

    handler_overrides = {'run_test': _run_test, '_transforms': [], 'finish': finish}

    for attribute, override in handler_overrides.items():
        if isinstance(override, Callable):  # setting methods on the handler class
            setattr(handler_class, attribute, override)

    args = handler_class_args or []
    kwargs = handler_class_kwargs or {}
    handler = handler_class(Application(), req_obj, *args, **kwargs)

    # TODO end tornado dependency

    for attribute, override in handler_overrides.items():
        if not isinstance(override, Callable):  # setting other properties on the handler object
            setattr(handler, attribute, override)

    return handler


def mock_request(handler_class: Optional[Callable] = None,
                 req_obj: Optional[MockHttpRequest] = None,
                 response_parser: Optional[Callable] = None,
                 handler_class_args: Optional[List[Any]] = None,
                 handler_class_kwargs: Optional[Dict[str, Any]] = None,
                 **kwargs) -> Callable:
    """
    generic tornado request double factory; can be invoked within a wrapper to customize

    :param handler_class: class of RequestHandler being tested
    :param req_obj: MockHttpRequest object; required if not passing kwargs
    :param response_parser: a method to parse the handler response for easier testing
    :param kwargs: kwargs for MockHttpRequest if not passing req_obj param
    :return: returns modified test function or class
    """
    req_obj = req_obj or MockHttpRequest(**kwargs)
    req_obj.FACTORY_NAME = 'mock_request'

    def register_test_func(pytest_func: Callable) -> Callable:
        if not req_obj and inspect.isclass(pytest_func):
            inspect.getmembers(pytest_func)   # TODO is this doing anything?
        store = MALL.get_store(test_name=pytest_func.__name__)

        final_handler_class = handler_class if handler_class else store.request_handler_class \
                                                                  or MALL.request_handler_class
        handler = _get_handler_instance(handler_class=final_handler_class, req_obj=req_obj,
                                        response_parser=response_parser, handler_class_kwargs=handler_class_kwargs,
                                        handler_class_args=handler_class_args)
        store.handler = handler
        handler._pytest_store = store

        @functools.wraps(pytest_func)
        async def modified_pytest_func(*args, **qwargs):
            """
            we need to override test function because the handler arg can be overridden
            :param args:
            :param qwargs: odd name to avoid shadowing kwargs
            :return:
            """
            if store.handler != handler:
                store.handler = handler
                handler._pytest_store = store

            await pytest_func(*args, **qwargs)

        return modified_pytest_func

    def callable_wrapper(callable_obj: Callable) -> Callable:
        return _apply_func_recursive(kallable=callable_obj, func=register_test_func)

    return callable_wrapper
