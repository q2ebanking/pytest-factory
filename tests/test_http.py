import pytest

from pytest_factory.http import mock_http_server, MockHttpRequest as mhr
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


@mock_http_server(path='http://www.test.com/endpoint0', response='TestHttp')
class TestHttp:
    @mock_request(path='endpoint0/wildcard')
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

    class TestResponseTracking:
        @mock_request(path='?num=0')
        async def test_http_no_calls_warning(self, store):
            resp = await store.handler.run_test()
            assert resp == ''
            # TODO assert warning made it to logger

        @mock_request(path='?num=2')
        async def test_http_extra_call_warning(self, store):
            """
            please note that this test is expected to raise a non-fatal
            UserWarning
            """
            resp = await store.handler.run_test(assert_no_extra_calls=False)
            assert resp == 'yupyup'
            # TODO assert warning made it to logger

        async def test_http_call_same_endpoint_diff_test(self, store, caplog):
            """
            """
            resp = await store.handler.run_test()
            assert resp == 'yup'
            actual = [rec.message for rec in caplog.records]
            # TODO expected log should NOT have any warnings related to extra or missed calls to endpoint


@mock_request(req_obj=mhr(path="query_params_test?wild=card"))
class TestQueryParams:
    @mock_http_server(path='http://www.test.com/mock_endpoint', response='wild params')
    async def test_http_wildcard_params(self, store):
        resp = await store.handler.run_test()
        assert resp == 'wild params'

    @mock_http_server(path='http://www.test.com/*', response='wild path and params')
    async def test_http_wildcard_path_and_params(self, store):
        resp = await store.handler.run_test()
        assert resp == 'wild path and params'

    @mock_http_server(path='http://www.test.com/mock_endpoint?wild=card', response='exact match!')
    async def test_http_query_params_routing(self, store):
        resp = await store.handler.run_test()
        assert resp == 'exact match!'

    @mock_http_server(path='http://www.test.com/mock_endpoint?foo=bar', response='exact match!')
    async def test_http_query_params_routing_fail(self, store):
        with pytest.raises(expected_exception=MissingTestDoubleException,
                           match=r'.*http://www.test.com/mock_endpoint\?wild=card.*'):
            await store.handler.run_test()

    @mock_request(req_obj=mhr(path="query_params_test?wild=card&foo=bar"))
    @mock_http_server(path='http://www.test.com/mock_endpoint?foo=bar&wild=card', response='exact match!')
    async def test_http_query_params_misordered_success(self, store):
        resp = await store.handler.run_test()
        assert resp == 'exact match!'
