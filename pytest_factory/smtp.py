from typing import Sequence, Callable, Optional

from pytest_factory.framework.smtp_types import SMTPRequest, MOCK_SMTP_RESPONSE
from pytest_factory.framework.base_types import MAGIC_TYPE
from pytest_factory.framework.factory import make_factory


def mock_smtp_server(to_addrs: Sequence[str], from_addr: Optional[str] = None,
                     response: MAGIC_TYPE[MOCK_SMTP_RESPONSE] = None) -> Callable:
    req_obj = SMTPRequest(to_addrs=to_addrs, from_addr=from_addr or 'test@pytest-factory.org')
    return make_factory(factory_name='mock_smtp_server', req_obj=req_obj, response=response or {})
