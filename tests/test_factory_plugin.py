import pytest

from pytest_factory import mock_request
from tests.mock_plugin.factories import mock_service0, mock_service1

pytestmark = pytest.mark.asyncio


@mock_service0(key='', response='yup')
class TestFactoryPlugin:
    @mock_request(path="factory_plugin?mock_service0=foo")
    async def test_plugin_simple_routing(self, store):
        resp = await store.handler.run_test()
        assert resp == 'yup'

    @mock_request(path="factory_plugin?mock_service0=foo")
    @mock_service0(key='', response='nope')
    async def test_plugin_override(self, store):
        resp = await store.handler.run_test()
        assert resp == 'nope'

    @mock_service1(key='', response='wild')
    @mock_request(path="factory_plugin?mock_service0=foo&mock_service1=bar")
    async def test_plugin_complex_routing(self, store):
        resp = await store.handler.run_test()
        assert resp == 'wild'
