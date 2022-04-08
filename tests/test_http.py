from typing import List
import pytest

from requests import Timeout

from pytest_factory.http import mock_http_server
from pytest_factory.framework.exceptions import MissingTestDoubleException
from pytest_factory import mock_request
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


@mock_request(path='endpoint0')
@mock_http_server(path='http://www.test.com/endpoint0', response='TestHttp')
class TestHttp:
    @mock_http_server(path='http://www.test.com/endpoint0', response='test_http_func_override')
    async def test_http_func_override(self, store):
        resp = await store.handler.run_test()
        assert resp == 'test_http_func_override'

    @mock_request(path='endpoint0/wildcard')
    @mock_http_server(path='http://www.test.com/endpoint0/*', response='test_http_wildcard_path')
    async def test_http_wildcard_path(self, store):
        resp = await store.handler.run_test()
        assert resp == 'test_http_wildcard_path'

    @mock_http_server(path='http://www.test.com/endpoint0', response=lambda x: x.path)
    async def test_http_response_function(self, store):
        resp = await store.handler.run_test()
        assert resp == 'http://www.test.com/endpoint0'

    @mock_http_server(path='http://www.test.com/endpoint0', response=Timeout)
    async def test_http_response_exception(self, store):
        resp = await store.handler.run_test()
        assert resp == 'caught RequestException: MockHttpRequest(protocol=\'http\', host=\'127.0.0.1\', ' \
                       'method=\'get\', uri=\'http://www.test.com/endpoint0\', version=\'HTTP/1.0\', remote_ip=None)'

    class TestResponseTracking:
        @mock_request(path='endpoint0?num=0')
        async def test_http_no_calls_warning(self, store, caplog):
            resp = await store.handler.run_test()
            assert resp == ''
            actual = get_logs(caplog)
            assert actual == [
                "the following test doubles were NOT used in this test: {'mock_http_server': {MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/endpoint0', version='HTTP/1.0', remote_ip=None): ['TestHttp']}} if this is not expected, set assert_no_missing_calls to True"]

        @mock_request(path='endpoint0?num=2')
        async def test_http_extra_call_warning(self, store, caplog):
            """
            """
            resp = await store.handler.run_test()
            assert resp == 'TestHttpTestHttp'
            actual = get_logs(caplog)
            assert actual == [
                "expected only 1 calls to MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/endpoint0', version='HTTP/1.0', remote_ip=None)! will repeat last response: TestHttp"]

        async def test_http_call_same_endpoint_diff_test(self, store, caplog):
            """
            """
            resp = await store.handler.run_test()
            assert resp == 'TestHttp'
            actual = get_logs(caplog)
            assert actual == []


@mock_request(path="endpoint0?wild=card")
class TestQueryParams:
    @mock_http_server(path='http://www.test.com/endpoint0', response='wild params')
    async def test_http_wildcard_params(self, store):
        resp = await store.handler.run_test()
        assert resp == 'wild params'

    @mock_http_server(path='http://www.test.com/endpoint0/*', response='wild path and params')
    async def test_http_wildcard_path_and_params(self, store):
        resp = await store.handler.run_test()
        assert resp == 'wild path and params'

    @mock_http_server(path='http://www.test.com/endpoint0?wild=card', response='exact match!')
    async def test_http_query_params_routing(self, store):
        resp = await store.handler.run_test()
        assert resp == 'exact match!'

    @mock_http_server(path='http://www.test.com/endpoint0?foo=bar', response='exact match!')
    async def test_http_query_params_routing_fail(self, store):
        with pytest.raises(expected_exception=MissingTestDoubleException,
                           match=r'.*http://www.test.com/endpoint0\?wild=card.*'):
            await store.handler.run_test()

    @mock_request(path="endpoint0?wild=card&foo=bar")
    @mock_http_server(path='http://www.test.com/endpoint0?foo=bar&wild=card', response='exact match!')
    async def test_http_query_params_misordered_success(self, store):
        resp = await store.handler.run_test()
        assert resp == 'exact match!'
