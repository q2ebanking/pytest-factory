import pytest

from aiohttp import ClientConnectionError

from pytest_factory.http import mock_http_server, MockHttpResponse
from pytest_factory.monkeypatch.tornado import tornado_handler
from pytest_factory import logger

logger = logger.get_logger(__name__)

pytestmark = pytest.mark.asyncio


@tornado_handler(path='endpoint0')
@mock_http_server(path='http://www.test.com/endpoint0', response='TestHttp')
class TestAioHttp:
    @mock_http_server(path='http://www.test.com/endpoint0', response='test_http_func_override')
    async def test_http_func_override_aio(self, store):
        resp = await store.sut.run_test(assert_no_extra_calls = False)
        assert resp.content.decode() == 'test_http_func_override'
        assert len(store.messages) == 4
        assert store.messages[3] == resp
        assert await store.messages[2].text() == resp.content.decode()

    @mock_http_server(path='http://www.test.com/endpoint0', response=MockHttpResponse(status=500))
    async def test_http_500_aio(self, store):
        resp = await store.sut.run_test()
        assert resp.status_code == 500

    @tornado_handler(path='endpoint0/wildcard')
    @mock_http_server(path='http://www.test.com/endpoint0/*', response='test_http_wildcard_path')
    async def test_http_wildcard_path_aio(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'test_http_wildcard_path'

    @mock_http_server(path='http://www.test.com/endpoint0', response=lambda x: x.url)
    async def test_http_response_function_aio(self, store):
        resp = await store.sut.run_test()
        assert resp.content.decode() == 'http://www.test.com/endpoint0'

    @mock_http_server(path='http://www.test.com/endpoint0', response=ClientConnectionError)
    async def test_http_response_exception_aio(self, store):
        resp = await store.sut.run_test()
        msg = "caught RequestException: <pytest_factory.framework.http_types.MockHttpRequest: " \
              "{'url': 'http://www.test.com/endpoint0', 'method': 'get', 'body': b'', 'headers': '{}'}>"
        assert resp.content.decode() == msg
