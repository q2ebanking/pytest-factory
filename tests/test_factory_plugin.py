import pytest
import json

from pytest_factory.monkeypatch.tornado import tornado_handler
from tests.mock_plugin.plugin import mock_service0, mock_service1

pytestmark = pytest.mark.asyncio


def get_body(service_name: str, service_param: str) -> bytes:
    return json.dumps({
        'service_name': service_name,
        'service_param': service_param
    }).encode()


@mock_service0(key='route0', response='yup')
class TestFactoryPlugin:
    @tornado_handler(method='post', path="plugin0", body=get_body('mock_service0', 'route0'))
    async def test_plugin_simple_routing(self, store):
        resp = await store.handler.run_test()
        assert resp.content.decode() == 'yup'

    @tornado_handler(method='post', path="plugin0", body=get_body('mock_service0', 'route0'))
    @mock_service0(key='route0', response='nope')
    async def test_plugin_override(self, store):
        # also testing response_parser TODO move elsewhere?
        resp = await store.handler.run_test(response_parser=lambda x: x.content.decode())
        assert resp == 'nope'

    @tornado_handler(method='post', path="plugin0", body=get_body('mock_service1', 'route0'))
    @mock_service1(key='route0', response='wild')
    async def test_plugin_complex_routing(self, store):
        resp = await store.handler.run_test()
        assert resp.content.decode() == 'wild'
