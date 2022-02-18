import pytest

from pytest_factory import mock_request

pytestmark = pytest.mark.asyncio


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

# conftest.py
        fixture_a = mock_request(path='something')


# test.py
        async def test_http_explicit_handler(self, fixture_a, fixture_b, fixture_c):
            """
            """
            resp = await store.handler.run_test()
            assert resp == 'yay'

        async def test_http_explicit_handler0(self, fixture_c, fixture_b):
            resp = await store.handler.run_test()
            assert resp == 'yay'