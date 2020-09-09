'''
1. identify RequestHandler
2. instantiate and attach request fixture
3.


'''
import pytest

from tornado_drill.fixtures.http import mock_server, mock_request

pytestmark = pytest.mark.asyncio


async def test_function():
    pass


@mock_server()
class TestInheritance:
    class TestOverride:
        @mock_request()
        async def test_a(self, handler, fixtures):
            resp = await handler.run_test()
            fixtures
