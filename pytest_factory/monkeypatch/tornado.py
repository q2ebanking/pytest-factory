import inspect
from typing import Callable, Any

from tornado.web import Application, RequestHandler

from pytest_factory.monkeypatch.utils import update_monkey_patch_configs
from pytest_factory.framework.mall import MALL
from pytest_factory.http import MockHttpRequest
from pytest_factory.logger import get_logger

logger = get_logger(__name__)


def response_parser(body: str) -> Any:
    """
    this can be overridden but by default just returns the body unparsed
    """
    logger.info('HELLO')
    return body


def get_handler_instance(req_obj: MockHttpRequest, handler_class: Callable) -> RequestHandler:
    handler = handler_class(Application(), req_obj)
    return handler


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


def _finish(self, *_, **__) -> None:  # pylint: disable=unused-argument
    return self._write_buffer


patch_members = {'run_test': _run_test, '_transforms': [], 'finish': _finish}
update_monkey_patch_configs(factory_name='mock_request', callable_obj=RequestHandler, patch_members=patch_members)
