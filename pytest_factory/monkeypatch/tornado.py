import inspect
import json
from typing import Callable, Optional, Union, Any

import requests
from tornado.web import Application, RequestHandler
from tornado.httputil import HTTPServerRequest, HTTPHeaders

from pytest_factory.monkeypatch.utils import update_monkey_patch_configs
from pytest_factory.framework.mall import MALL, import_from_str_path
from pytest_factory.framework.exceptions import PytestFactoryBaseException
from pytest_factory.framework.http_types import HTTP_METHODS
from pytest_factory.http import MockHttpRequest, make_factory, MockHttpResponse


class TornadoMonkeyPatchException(PytestFactoryBaseException):
    def get_error_msg(self, log_msg: str, *args, **kwargs) -> str:
        return log_msg


def connection(): pass


setattr(connection, 'set_close_callback', lambda _: None)


def constructor(req_obj: MockHttpRequest, sut_callable: Callable) -> RequestHandler:
    request = HTTPServerRequest(method=req_obj.method, uri=req_obj.url, body=req_obj.body, headers=req_obj.headers)
    request.connection = connection
    return sut_callable(application=Application(), request=request)


def read_from_write_buffer(buffer) -> Optional[bytes]:
    result = buffer[len(buffer) - 1] if buffer else None
    return result


class TornadoRequest(MockHttpRequest):
    FACTORY_NAME = 'tornado_handler'
    FACTORY_PATH = 'pytest_factory.monkeypatch.tornado'
    HANDLER_NAME = 'RequestHandler'
    HANDLER_PATH = 'tornado.web'

    def __init__(self, sut_callable: Union[Callable, str], method: str = HTTP_METHODS.GET.value,
                 exchange_id: Optional[str] = None,
                 url: Optional[str] = None, **kwargs):
        """
        :param sut_callable: the class of the Tornado RequestHandler that will handle this request
        :param method: HTTP method, e.g. GET or POST
        :param exchange_id: should only be provided if being deserialized from a serialized live Recording
            or if being instantiated within a TornadoRecorderRequestHandler that already has a uuid for
            uniquely identifying requests
        :param url: HTTP url or path
        :param kwargs: additional properties of an HTTP request e.g. headers, body, etc.
        """
        if sut_callable is None:
            sut_callable = MALL.sut_callable
        self.sut_callable = import_from_str_path(sut_callable) if isinstance(sut_callable, str) else sut_callable
        qwargs = {
            'method': method,
            'url': url or '',
            'sut_callable': sut_callable
        }

        if kwargs.get('headers'):
            qwargs['headers'] = HTTPHeaders(kwargs.get('headers'))

        if kwargs.get('json'):
            json_dict = kwargs.pop('json')
            qwargs['body'] = json.dumps(json_dict).encode()
        elif kwargs.get('body'):
            qwargs['body'] = kwargs.get('body')

        super().__init__(exchange_id=exchange_id, **qwargs)

    @property
    def content(self) -> bytes:
        return self.body


def tornado_handler(req_obj: Optional[MockHttpRequest] = None,
                    sut_callable: Optional[Union[Callable, str]] = None, **kwargs) -> Callable:
    if req_obj is None:
        req_obj = TornadoRequest(**kwargs, sut_callable=sut_callable)
    return make_factory(req_obj=req_obj,
                        factory_name='tornado_handler')


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
        it must execute

        :param assert_no_missing_calls: if set to True, will raise UnCalledTestDoubleException if handler calls
        a test double less times than it has responses; will no longer issue warning via logger
        this can also be set in conftest by setting ASSERT_NO_MISSING_CALLS to True
        :param assert_no_extra_calls: if set to False, will no longer raise OverCalledTestDoubleException if handler calls
        a test double more times than it has responses; will issue warnings instead via logger
        :param response_parser: a function that receives a requests.Response object and parses it for the data that the test
        needs to make an assertion against (e.g. some data within the Response.content)
        :return:
        """
        store = MALL.get_store()
        with store.shop(assert_no_extra_calls=assert_no_extra_calls,
                        assert_no_missing_calls=assert_no_missing_calls,
                        request_attr='request',
                        response_attr='_response') as _:
            method_name = self.request.method.lower()
            if not hasattr(self, method_name):
                msg = f'self does not have attr: {method_name}. should be subclass of tornado.web.RequestHandler!'
                raise TornadoMonkeyPatchException(log_msg=msg)

            result = getattr(self, method_name)()

            if inspect.isawaitable(result):
                await result
            raw_resp = b''
            if self._write_buffer:
                raw_resp = read_from_write_buffer(self._write_buffer)
            response_obj = MockHttpResponse(body=raw_resp, status=self.get_status())
            if response_parser:
                response_obj = response_parser(response_obj)
            self._response = response_obj
            return response_obj

    def finish(self, chunk: Optional[Union[str, bytes, dict]] = None) -> "Future[None]":
        pass


patch_members = {'run_test': TornadoMonkeyPatches.run_test,
                 'finish': TornadoMonkeyPatches.finish,
                 '_transforms': []}
update_monkey_patch_configs(callable_obj=RequestHandler, patch_members=patch_members,
                            constructor=constructor)
