import inspect
from typing import Callable, Optional, Union, Any

import requests
from tornado.web import Application, RequestHandler

from pytest_factory.monkeypatch.utils import update_monkey_patch_configs
from pytest_factory.framework.mall import MALL
from pytest_factory.framework.exceptions import PytestFactoryBaseException
from pytest_factory.http import MockHttpRequest
from pytest_factory.logger import get_logger

logger = get_logger(__name__)


class TornadoMonkeyPatchException(PytestFactoryBaseException):
    def get_error_msg(self, log_msg: str, *args, **kwargs) -> str:
        return log_msg


def read_from_write_buffer(buffer) -> Optional[str]:
    result = buffer[len(buffer) - 1].decode('utf-8') if buffer else None
    return result


def get_handler_instance(req_obj: MockHttpRequest, handler_class: Callable) -> RequestHandler:
    """
    this is a tornado-specific adapter for converting a req_obj into an instance of the handler under test and should
    be generic across all handlers within a test suite
    """
    handler = handler_class(Application(), req_obj)
    return handler


class TornadoMonkeyPatches(RequestHandler):
    """
    this class is purely to provide the pytest-factory contributor the context of the class that will be monkeypatched;
    it should NOT be instantiated directly
    it can also be inherited by a plugin developer to modify the monkeypatches for specialized subclasses of RequestHandler
    to apply these monkeypatches:
    1. the plugin module invokes update_monkey_patch_configs
    2. the end-user includes the plugin module in their config.ini imports
    """

    async def run_test(self, assert_no_missing_calls: bool = None,
                       assert_no_extra_calls: bool = None,
                       response_parser: Optional[Callable] = None) -> Union[Any, requests.Response]:
        """
        this method will be bound to the RequestHandler, which is why it must receive the parameter 'self',
        and provides a way to advance the state of the RequestHandler while returning the response to the
        test method for assertions

        :param assert_no_missing_calls: if set to True, will raise UnCalledTestDoubleException if handler calls
        a test double less times than it has responses; will no longer issue warning via logger
        this can also be set in conftest by setting ASSERT_NO_MISSING_CALLS to True
        :param assert_no_extra_calls: if set to False, will no longer raise OverCalledTestDoubleException if handler calls
        a test double more times than it has responses; will issue warnings instead via logger
        :param response_parser: a function that receives a requests.Response object and parses it for the data that the test
        needs to make an assertion against (e.g. some data within the Response.content)
        :return:
        """
        store = self._pytest_store
        with store.open(assert_no_extra_calls=assert_no_extra_calls,
                        assert_no_missing_calls=assert_no_missing_calls) as store:
            method_name = self.request.method.lower()
            if not hasattr(self, method_name):
                msg = f'self does not have attr: {method_name}. should be subclass of tornado.web.RequestHandler!'
                raise TornadoMonkeyPatchException(log_msg=msg)

            result = getattr(self, method_name)()
            try:
                if inspect.isawaitable(result):
                    await result
            except Exception as ex:
                store.checkout(ex)
                raise ex

            if self._write_buffer:
                raw_resp = self._write_buffer[len(self._write_buffer) - 1]
                # TODO consider casting into requests.Response object
                store.checkout(raw_resp)
                response_obj = requests.Response()
                response_obj._content = raw_resp
                response_obj.status_code = self.get_status()
                if response_parser:
                    response_obj = response_parser(response_obj)
                return response_obj

    def finish(self, *_, **__) -> None:  # pylint: disable=unused-argument
        # TODO pytest_factory.recorder.TornadoRecorderMixin.finish will get overwritten! maybe toggle by config?
        pass


patch_members = {'run_test': TornadoMonkeyPatches.run_test, '_transforms': [], 'finish': TornadoMonkeyPatches.finish}
MALL.get_handler_instance = get_handler_instance
update_monkey_patch_configs(callable_obj=RequestHandler, patch_members=patch_members)
