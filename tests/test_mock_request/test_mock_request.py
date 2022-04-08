import pytest

from pytest_factory import mock_request
from pytest_factory.framework.exceptions import MissingHandlerException

pytestmark = pytest.mark.asyncio


async def test_function_missing_handler(store):
    expected_msg = 'this test case is missing a mock_request or similar factory! no RequestHandler defined to test!'
    with pytest.raises(expected_exception=MissingHandlerException, match=expected_msg):
        await store.handler.run_test()


@mock_request(path='solo')
async def test_function(store):
    resp = await store.handler.run_test()
    assert resp == 'Hello, world'


class TestInheritance:
    @mock_request(path='?num=0')
    class TestOverride:
        async def test_http_inherit_handler(self, store):
            resp = await store.handler.run_test()
            assert resp == ''

        @mock_request(path='something')
        async def test_http_explicit_handler(self, store):
            """
            """
            resp = await store.handler.run_test()
            assert resp == 'yay'
