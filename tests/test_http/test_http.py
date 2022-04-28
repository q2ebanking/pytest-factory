from json import JSONDecodeError
from typing import List
import pytest

from requests import Timeout

from pytest_factory.http import mock_http_server, MockHttpResponse
from pytest_factory.framework.exceptions import UnCalledTestDoubleException
from pytest_factory.monkeypatch.tornado import tornado_handler
from pytest_factory import logger

logger = logger.get_logger(__name__)

pytestmark = pytest.mark.asyncio

EXPECTED_WARNINGS = {
    'test_http_no_calls_warning': '''
pytest-factory WARNING: the following test doubles have not been called: {'mock_http_server': {MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None): ['yup']}}!
pytest-factory WARNING: if this is not expected, consider this a test failure!''',
    'test_http_extra_call_warning': '''
pytest-factory WARNING: UNEXPECTED CALL DETECTED. expected only 1 calls to MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None)
pytest-factory WARNING: will repeat last response: yup'''
}


def get_logs(caplog, levelname: str = 'WARNING') -> List[str]:
    actual = [rec.message for rec in caplog.records if rec.levelname == levelname]
    return actual


@tornado_handler(url='endpoint0')
@mock_http_server(url='http://www.test.com/endpoint0', response='TestHttp')
class TestHttp:
    @mock_http_server(url='http://www.test.com/endpoint0', response='test_http_func_override')
    async def test_http_func_override(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'test_http_func_override'
        assert len(store.messages) == 4
        assert store.messages[3] == resp
        assert store.messages[2].content == resp.content

    @mock_http_server(url='http://www.test.com/endpoint0', response=MockHttpResponse(status=500))
    async def test_http_500(self, store):
        resp = await store.sut.run_test()
        assert resp.status_code == 500

    @tornado_handler(url='endpoint0/wildcard')
    @mock_http_server(url='http://www.test.com/endpoint0/*', response='test_http_wildcard_path')
    async def test_http_wildcard_path(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'test_http_wildcard_path'

    @mock_http_server(url='http://www.test.com/endpoint0', response=lambda x: x.url)
    async def test_http_response_function(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'http://www.test.com/endpoint0'

    @mock_http_server(url='http://www.test.com/endpoint0', response=Timeout)
    async def test_http_response_exception(self, store):
        resp = await store.sut.run_test()
        msg = "caught RequestException: <class pytest_factory.framework.http_types.MockHttpRequest: {'url': " \
              "'http://www.test.com/endpoint0', 'method': 'get', 'body': b'', 'headers': '{}'}>"
        assert resp.content.decode() == msg

    class TestResponseTracking:
        @tornado_handler(url='endpoint0?num=0')
        async def test_http_no_calls_warning(self, store, caplog):
            resp = await store.sut.run_test(assert_no_missing_calls=False)
            assert resp.content.decode() == ''
            actual = get_logs(caplog)
            msg = ['UnCalledTestDoubleException: the following test doubles were NOT used in '
                   "this test: {'mock_http_server': "
                   "{<class pytest_factory.framework.http_types.MockHttpRequest: {'url': "
                   "'http://www.test.com/endpoint0', 'method': 'get', 'body': b'', 'headers': "
                   "'{}'}>: [<class pytest_factory.framework.http_types.MockHttpResponse: {'body': "
                   "b'TestHttp', 'status': 200, 'headers': '{}'}>]}} if this is not expected, "
                   'set assert_no_missing_calls to True']
            assert actual == msg

        @tornado_handler(url='endpoint0?num=2')
        async def test_http_extra_call_warning(self, store, caplog):
            """
            """
            resp = await store.sut.run_test(assert_no_extra_calls=False)
            assert resp.content.decode() == 'TestHttpTestHttp'
            actual = get_logs(caplog)
            assert actual == ['OverCalledTestDoubleException: expected only 1 calls to <class '
                              "pytest_factory.framework.http_types.MockHttpRequest: {'url': "
                              "'http://www.test.com/endpoint0', 'method': 'get', 'body': b'', 'headers': "
                              '\'{}\'}>! will repeat last response: "<class '
                              "pytest_factory.framework.http_types.MockHttpResponse: {'body': b'TestHttp', "
                              '\'status\': 200, \'headers\': \'{}\'}>"']

        async def test_http_call_same_endpoint_diff_test(self, store, caplog):
            """
            """
            resp = await store.sut.run_test()
            assert resp.content.decode() == 'TestHttp'
            actual = get_logs(caplog)
            assert actual == []

        @tornado_handler(method='post', url='endpoint0', body='<xmlDoc>foo</xmlDoc>',
                         headers={'Content-Type': 'text/xml'})
        async def test_http_call_xml(self, store):
            with pytest.raises(JSONDecodeError):
                await store.sut.run_test(assert_no_missing_calls=False)


@tornado_handler(url="endpoint0?wild=card")
class TestQueryParams:
    @mock_http_server(url='http://www.test.com/endpoint0', response='wild params')
    async def test_http_wildcard_params(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'wild params'

    @mock_http_server(url='http://www.test.com/endpoint0/*', response='wild path and params')
    async def test_http_wildcard_path_and_params(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'wild path and params'

    @mock_http_server(url='http://www.test.com/endpoint0?wild=card', response='exact match!')
    async def test_http_query_params_routing(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'exact match!'

    @mock_http_server(url='http://www.test.com/endpoint0?foo=bar', response='exact match!')
    async def test_http_query_params_routing_fail(self, store):
        with pytest.raises(expected_exception=UnCalledTestDoubleException):
            await store.sut.run_test()

    @tornado_handler(url="endpoint0?wild=card&foo=bar")
    @mock_http_server(url='http://www.test.com/endpoint0?foo=bar&wild=card', response='exact match!')
    async def test_http_query_params_misordered_success(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'exact match!'
