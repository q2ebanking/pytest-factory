import pytest

from tornado_drill.http import mock_http_server
from tornado_drill import mock_request
from tornado_drill.framework.pytest import LOGGER

pytestmark = pytest.mark.asyncio


@mock_http_server(path='http://www.test.com/mock_endpoint', response='yup')
@mock_request()
class TestHttp:
    @mock_http_server(path='http://www.test.com/mock_endpoint', response='nope')
    async def test_http_func_override(self, handler, store):
        resp = await handler.run_test()
        assert resp == 'nope'

    @mock_http_server(path='http://www.test.com/*', response='wild')
    async def test_http_wildcard_path(self, handler, store):
        """
        TODO this might just be stupid hard
        :param handler:
        :param store:
        :return:
        """
        resp = await handler.run_test()
        assert resp == 'wild'

    class TestResponseTracking:
        @mock_request(path='?num=0')
        async def test_http_no_calls_warning(self, handler, store):
            """
            see self.teardown_method
            """
            resp = await handler.run_test()
            assert resp == ''

        @mock_request(path='?num=2')
        async def test_http_extra_call_warning(self, handler, store):
            """
            please note that this test is expected to raise a non-fatal UserWarning
            see self.teardown_method
            """
            resp = await handler.run_test(assert_no_extra_calls=False)
            assert resp == 'yupyup'

        def teardown_method(self, method):
            """
            this is ugly but it's what you get when you write tests for a test framework

            be aware that if AssertionError gets raised here the debugger will likely jump context to a method called
            f"{test_func}_teardown" that does not exist after the pytest.Session ends.

            for PyCharm this means, when attempting to debug just the method from within the dedicated "Debug" tile,
            it will try to execute and debug the "_teardown" method which no longer exists, and PyTest will claim
            it could not find any tests to collect.
            :param method:
            :return:
            """
            if method == self.test_http_no_calls_warning:
                assert LOGGER.buffer[-1] == '''
TORNADO-DRILL WARNING: test_http_no_calls_warning failed to call the following fixtures: {'mock_http_server': {MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None): ['yup']}}!
TORNADO-DRILL WARNING: if this is not expected, consider this a test failure!'''
            elif method == self.test_http_extra_call_warning:
                assert LOGGER.buffer[-1] == '''
TORNADO-DRILL WARNING: UNEXPECTED CALL DETECTED. expected only 1 calls to MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None)
TORNADO-DRILL WARNING: will repeat last response: yup'''
