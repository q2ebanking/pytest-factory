import pytest

from pytest_factory.monkeypatch.tornado import tornado_handler
from pytest_factory.framework.exceptions import MissingHandlerException

pytestmark = pytest.mark.asyncio


async def test_function_missing_handler(store):
    expected_msg = 'this test case is missing a request handler factory! no RequestHandler defined to test!'
    with pytest.raises(expected_exception=MissingHandlerException, match=expected_msg):
        await store.sut.run_test()


@tornado_handler(url='solo')
async def test_function(store):
    resp = await store.sut.run_test()
    assert resp.body.decode() == 'Hello, world'


class TestInheritance:
    @tornado_handler(url='?num=0')
    class TestOverride:
        async def test_http_inherit_handler(self, store):
            resp = await store.sut.run_test()
            assert resp.body.decode() == ''

        @tornado_handler(url='something')
        async def test_http_explicit_handler(self, store):
            """
            """
            resp = await store.sut.run_test()
            assert resp.body.decode() == 'yay'
