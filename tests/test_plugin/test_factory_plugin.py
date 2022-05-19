import pytest
import json
from typing import Optional

from pytest_factory.monkeypatch.tornado import tornado_handler

from tests.test_plugin.mock_plugin.plugin import mock_service0, mock_service1

pytestmark = pytest.mark.asyncio


def get_body(service_name: str, service_param: str, tpd_url: Optional[str] = None) -> bytes:
    return json.dumps({
        'third_party_url': tpd_url or '',
        'service_name': service_name,
        'service_param': service_param
    }).encode()


@mock_service0(key='route0', response='yup')
class TestFactoryPlugin:
    @tornado_handler(method='post', url="plugin0", body=get_body('mock_service0', 'route0'))
    async def test_plugin_simple_routing(self, store):
        resp = await store.sut.run_test()
        assert resp.body.decode() == 'yup'

    @tornado_handler(method='post', url="endpoint0", body=get_body('mock_service0', 'route0'))
    async def test_plugin_simple_routing_fail(self, store):
        resp = await store.sut.run_test(assert_no_missing_calls=False)
        assert resp.status == 404

    @tornado_handler(method='post', url="plugin0_alt", body=get_body('mock_service0', 'route0'))
    async def test_plugin_alternate_url(self, store):
        resp = await store.sut.run_test()
        assert resp.body.decode() == 'yup'

    @tornado_handler(method='post', url="plugin0", body=get_body('mock_service0', 'route0'))
    @mock_service0(key='route0', response='nope')
    async def test_plugin_override(self, store):
        resp = await store.sut.run_test(response_parser=lambda x: x.body.decode())
        assert resp == 'nope'

    @tornado_handler(method='post', url="plugin0", body=get_body('mock_service1', 'route0'))
    @mock_service1(key='route0', response='wild')
    async def test_plugin_complex_routing(self, store):
        resp = await store.sut.run_test(assert_no_missing_calls=False)
        assert resp.body.decode() == 'wild'
