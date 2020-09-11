import pytest

from tornado_drill import mock_request

pytestmark = pytest.mark.asyncio


@mock_request(path='solo')
async def test_function(handler, store):
    resp = await handler.run_test()
    assert resp == 'Hello, world'


class TestInheritance:
    @mock_request(path='?num=0')
    class TestOverride:
        async def test_http_inherit_handler(self, handler, store):
            resp = await handler.run_test()
            assert resp == ''

        @mock_request(path='something')
        async def test_http_explicit_handler(self, handler, store):
            """
            """
            resp = await handler.run_test()
            assert resp == 'yay'
