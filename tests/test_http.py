'''
1. identify RequestHandler
2. instantiate and attach request fixture
3.


'''
import pytest

from tornado_drill.http import mock_http_server
from tornado_drill.mock_request import mock_request
from tornado_drill.framework.pytest import LOGGER

pytestmark = pytest.mark.asyncio


@mock_request(path='solo')
async def test_function(handler, store):
    resp = await handler.run_test()
    assert resp == 'Hello, world'


@mock_http_server(path='http://www.test.com/mock_endpoint', response='yup')
class TestInheritance:
    @mock_request()
    class TestOverride:
        @mock_http_server(path='http://www.test.com/mock_endpoint', response='nope')
        async def test_http_func_override(self, handler, store):
            resp = await handler.run_test()
            assert resp == 'nope'

        async def test_http_inherit_handler(self, handler, store):
            resp = await handler.run_test()
            assert resp == 'yup'

        @mock_request(path='something')
        async def test_http_explicit_handler_no_calls_warning(self, handler, store):
            """
            please note that this test is expected to raise a non-fatal UserWarning

            :param handler:
            :param store:
            :param recwarn:
            :return:
            """
            resp = await handler.run_test()
            assert resp == 'yay'

        @mock_request(path='?num=2')
        async def test_http_explicit_handler_extra_call_warning(self, handler, store):
            """
            please note that this test is expected to raise a non-fatal UserWarning

            :param handler:
            :param store:
            :param recwarn:
            :return:
            """
            resp = await handler.run_test()
            assert resp == 'yup'


        def teardown_method(self, method):
            """
            this is ugly but it's what you get when you write tests for a test framework
            :param method:
            :return:
            """
            if method == self.test_http_explicit_handler_no_calls_warning:
                assert LOGGER.buffer[-1] == '''
TORNADO-DRILL WARNING: test_http_explicit_handler_no_calls_warning failed to call the following fixtures during execution: {'mock_http_server': {MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None): ['yup']}}!
TORNADO-DRILL WARNING: if this is not expected, consider this a test failure!'''
            elif method == self.test_http_explicit_handler_extra_call_warning:
                assert LOGGER.buffer[-1] == '''
TORNADO-DRILL WARNING: UNEXPECTED CALL DETECTED. expected only 1 calls to MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None)
TORNADO-DRILL WARNING: will repeat last response: yup'''
