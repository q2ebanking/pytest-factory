import pytest
import json

from pytest_factory import mock_request
from tests.mock_plugin.factories import mock_service0, mock_service1

pytestmark = pytest.mark.asyncio


def get_body(service_name: str, service_param: str) -> bytes:
    return json.dumps({
        'service_name': service_name,
        'service_param': service_param
    }).encode()


@mock_service0(key='route0', response='yup')
class TestFactoryPlugin:
    @mock_request(method='post', path="plugin0", body=get_body('mock_service0', 'route0'))
    async def test_plugin_simple_routing(self, store):
        resp = await store.handler.run_test()
        assert resp == 'yup'

    @mock_request(method='post', path="plugin0", body=get_body('mock_service0', 'route0'))
    @mock_service0(key='route0', response='nope')
    async def test_plugin_override(self, store):
        resp = await store.handler.run_test()
        assert resp == 'nope'

    @mock_request(method='post', path="plugin0", body=get_body('mock_service1', 'route0'))
    @mock_service1(key='route0', response='wild')
    async def test_plugin_complex_routing(self, store):
        resp = await store.handler.run_test()
        assert resp == 'wild'