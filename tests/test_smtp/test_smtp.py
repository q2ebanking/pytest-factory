import pytest
import json
from typing import Optional

from pytest_factory.smtp import mock_smtp_server
from pytest_factory.framework.base_types import MAGIC_TYPE
from pytest_factory.framework.exceptions import MissingFactoryException
from pytest_factory import mock_request
from pytest_factory import logger

logger = logger.get_logger(__name__)

pytestmark = pytest.mark.asyncio

DEFAULT_TO_ADDRS = ["mom@aol.com", "test@pytest-factory.com"]


def get_body(to_addrs: MAGIC_TYPE[str] = None, from_addr: Optional[str] = None):
    body_dict = {'to_addrs': to_addrs or DEFAULT_TO_ADDRS}
    if from_addr:
        body_dict['from_addr'] = from_addr
    return json.dumps(body_dict).encode()


@mock_request(method='post', path='/', body=get_body())
class TestSmtp:
    @mock_smtp_server(to_addrs=DEFAULT_TO_ADDRS, response={})
    async def test_smtp_sendmail(self, store):
        resp = await store.handler.run_test()
        assert resp.content.decode() == '{}'

    async def test_smtp_missing_factory_raises(self, store):
        with pytest.raises(MissingFactoryException):
            await store.handler.run_test(assert_no_missing_calls=True)

    async def test_smtp_missing_factory_no_exception(self, store):
        resp = await store.handler.run_test()
        assert resp.content.decode() == '{}'  # TODO
