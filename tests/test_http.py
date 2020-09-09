'''
1. identify RequestHandler
2. instantiate and attach request fixture
3.


'''
import pytest

from tornado_drill import mock_http_server, mock_request

pytestmark = pytest.mark.asyncio


async def test_function():
    pass


@mock_http_server(path='mock_endpoint', response='yup')
class TestInheritance:
    @mock_request()
    class TestOverride:
        @mock_http_server(path='mock_endpoint', response='nope')
        @mock_request()
        async def test_a(self, handler, store):
            resp = await handler.run_test()
            store.mock_server
