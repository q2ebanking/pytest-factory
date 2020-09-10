'''
1. identify RequestHandler
2. instantiate and attach request fixture
3.


'''
import pytest

from tornado_drill.http import mock_http_server
from tornado_drill.mock_request import mock_request

pytestmark = pytest.mark.asyncio


@mock_request(path='solo')
async def test_function(handler, store):
    resp = await handler.run_test()
    assert resp == 'Hello, world'


@mock_http_server(path='http://www.test.com/mock_endpoint', response='yup')
@mock_request(method='put')
class TestInheritance:
    @mock_request(method='post')
    class TestOverride:
        @mock_http_server(path='http://www.test.com/mock_endpoint', response='nope')
        @mock_request()
        async def test_a(self, handler, store):
            resp = await handler.run_test()
            assert resp == 'nope'
