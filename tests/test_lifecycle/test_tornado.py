import pytest
from typing import Callable

from pytest_factory.http import mock_http_server, MockHttpResponse as mhr, MockHttpRequest as mhrq
from pytest_factory.monkeypatch.tornado import tornado_handler, TornadoRequest as tr
from pytest_factory.lifecycle.recording import Recording

from tests.test_lifecycle.app import dependency_url, LiveException, InstrumentedHandler

pytestmark = pytest.mark.asyncio
ACC_URL = 'https://staging.accumulator.local/accumulate'


def get_validator(expected: Recording) -> Callable:
    def validate_payload(req_obj: mhrq) -> mhr:
        r = Recording.deserialize(req_obj.body)
        assert r.incident_type == expected.incident_type
        assert r.first.compare(expected.first)
        assert r.last == expected.last
        for actual_x, expected_x in zip(r.doc_exchanges, expected.doc_exchanges):
            assert actual_x[0].compare(expected_x[0])
            assert actual_x[1] == expected_x[1]
        return mhr()
    return validate_payload

sut_exchange = (tr(sut_callable=InstrumentedHandler), mhr(status=500))
EXC_REC = Recording(sut_exchange=sut_exchange, incident_type=LiveException)
doc_exchanges = [(mhrq(url=dependency_url), mhr(body=b'foo'))]
DEP_EXC_REC = Recording(sut_exchange=sut_exchange, doc_exchanges=doc_exchanges, incident_type=LiveException)


class TestLifecycle:
    @mock_http_server(method='post', url=ACC_URL, response=get_validator(expected=EXC_REC))
    @tornado_handler()
    async def test_exception(self, store):
        resp = await store.sut.run_test()
        assert resp.status == 500
        # TODO assert store._messages matches

    @mock_http_server(method='get', url=dependency_url, response=b'foo')
    @mock_http_server(method='post', url=ACC_URL, response=get_validator(expected=DEP_EXC_REC))
    @tornado_handler(url='dependency')
    async def test_dependency_exception(self, store):
        resp = await store.sut.run_test()
        assert resp.status == 500
