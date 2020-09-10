'''
1. identify RequestHandler
2. instantiate and attach request fixture
3.


'''
import pytest

from tornado_drill.http import mock_http_server
from tornado_drill.mock_request import mock_request

pytestmark = pytest.mark.asyncio


async def test_function():
    pass


@mock_http_server(path='mock_endpoint', response='yup')
@mock_request(method='put')
class TestInheritance:
    @mock_request(method='post')
    class TestOverride:
        @mock_http_server(path='mock_endpoint', response='nope')
        @mock_request()
        async def test_a(self, handler, store):
            resp = await handler.run_test()
            store.mock_server
