import pytest

from pytest_factory import mock_request
from pytest_factory.framework.exceptions import MissingHandlerException

# TODO this is temporary - need to fix the config parsing so it loads this before it gets here
from tests.other_app import MockRequestTestHandler

pytestmark = pytest.mark.asyncio


async def test_function_missing_handler(store):
    with pytest.raises(expected_exception=MissingHandlerException,
                       match='this test case is missing a mock_request or similar factory! no RequestHandler defined to test!'):
        await store.handler.run_test()


@mock_request(handler_class=MockRequestTestHandler, path='solo')
async def test_function(store):
    resp = await store.handler.run_test()
    assert resp == 'Hello, world'


class TestInheritance:
    @mock_request(handler_class=MockRequestTestHandler, path='?num=0')
    class TestOverride:
        async def test_http_inherit_handler(self, store):
            resp = await store.handler.run_test()
            assert resp == ''

        @mock_request(handler_class=MockRequestTestHandler, path='something')
        async def test_http_explicit_handler(self, store):
            """
            """
            resp = await store.handler.run_test()
            assert resp == 'yay'
