import pytest
import json
from typing import Optional
from smtplib import SMTPConnectError

from pytest_factory.framework.base_types import MAGIC_TYPE
from pytest_factory.framework.exceptions import MissingFactoryException, MissingTestDoubleException
from pytest_factory.monkeypatch.tornado import tornado_handler
from pytest_factory.monkeypatch.smtplib import mock_smtp_server
from pytest_factory import logger
from tests.smtp_app import test_url_map

logger = logger.get_logger(__name__)

pytestmark = pytest.mark.asyncio

DEFAULT_TO_ADDRS = ["mom@aol.com", "test@pytest-factory.com"]


def get_body(to_addrs: MAGIC_TYPE[str] = None, from_addr: Optional[str] = None):
    body_dict = {'to_addrs': to_addrs or DEFAULT_TO_ADDRS}
    if from_addr:
        body_dict['from_addr'] = from_addr
    return json.dumps(body_dict).encode()


@tornado_handler(method='post', path='endpoint0', body=get_body())
class TestSmtp:
    @mock_smtp_server(host=test_url_map.get('endpoint0'), to_addrs=DEFAULT_TO_ADDRS, response={})
    async def test_smtp_sendmail(self, store):
        resp = await store.handler.run_test()
        assert resp.content.decode() == '{}'

    @mock_smtp_server(host=test_url_map.get('endpoint0'), to_addrs='dad@yahoo.com', response={})
    async def test_smtp_sendmail_wrong_addr(self, store):
        resp = await store.handler.run_test(assert_no_missing_calls=False)
        assert resp.content == b"{'mom@aol.com': (550, 'Requested action not taken: mailbox unavailable'), 'test@pytest-factory.com': (550, 'Requested action not taken: mailbox unavailable')}"

    @mock_smtp_server(host=test_url_map.get('endpoint0'), to_addrs=DEFAULT_TO_ADDRS, response={})
    @tornado_handler(method='post', path='endpoint1', body=get_body())
    @mock_smtp_server(host=test_url_map.get('endpoint1'), to_addrs=DEFAULT_TO_ADDRS,
                      response=SMTPConnectError(code=550, msg=b''))
    async def test_smtp_sendmail_diff_host(self, store):
        resp = await store.handler.run_test(assert_no_missing_calls=False)
        assert resp.content.decode() == "(550, b'')"

    async def test_smtp_missing_factory_raises(self, store):
        with pytest.raises(MissingFactoryException):
            await store.handler.run_test(assert_no_missing_calls=True)

    async def test_smtp_missing_factory_no_exception(self, store):
        resp = await store.handler.run_test()
        msg = "{'mom@aol.com': (550, 'Requested action not taken: mailbox unavailable'), 'test@pytest-factory.com': (550, 'Requested action not taken: mailbox unavailable')}"
        assert resp.content.decode() == msg
        assert len(store.messages) == 4
        assert str(store.messages[2]) == msg

    @mock_smtp_server(to_addrs=DEFAULT_TO_ADDRS, response=SMTPConnectError(msg='foo', code=500))
    async def test_smtp_raises_exception(self, store):
        resp = await store.handler.run_test()
        assert resp.content.decode() == "(500, 'foo')"
