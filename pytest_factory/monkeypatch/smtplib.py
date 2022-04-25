from typing import Sequence, Callable, Optional
from smtplib import SMTP, SMTPException

from pytest_factory.monkeypatch.utils import update_monkey_patch_configs
from pytest_factory.framework.smtp_types import MOCK_SMTP_RESPONSE, SMTPRequest
from pytest_factory.framework.factory import make_factory, MALL
from pytest_factory.framework.base_types import MAGIC_TYPE

ERR_CODE = 550
ERR_MSG = 'Requested action not taken: mailbox unavailable'


def mock_smtp_server(to_addrs: Sequence[str], host: Optional[str] = None, from_addr: Optional[str] = None,
                     response: MAGIC_TYPE[MOCK_SMTP_RESPONSE] = None) -> Callable:
    req_obj = SMTPRequest(host=host, to_addrs=to_addrs, from_addr=from_addr or 'test@pytest-factory.org')
    return make_factory(factory_name='mock_smtp_server', req_obj=req_obj, response=response or {})


class SMTPMonkeyPatches(SMTP):

    def connect(self, host='localhost', port=0, source_address=None):
        self._host = host
        return 220, b''

    def sendmail(self,
                 from_addr: str,
                 to_addrs: str | Sequence[str],
                 msg: bytes | str,
                 mail_options: Sequence[str] = ...,
                 rcpt_options: Sequence[str] = ...,
                 ) -> MOCK_SMTP_RESPONSE:
        req_obj = SMTPRequest(from_addr=from_addr, to_addrs=to_addrs, msg=msg, host=self._host)
        store = MALL.get_store()
        resp = store.get_next_response(factory_name='mock_smtp_server', req_obj=req_obj)
        if isinstance(resp, SMTPException):
            raise resp
        if resp is None:
            resp = {addr: (ERR_CODE, ERR_MSG) for addr in to_addrs}
        store.messages.extend([req_obj, resp])
        return resp


patch_members = {
    'sendmail': SMTPMonkeyPatches.sendmail,
    'connect': SMTPMonkeyPatches.connect
}
update_monkey_patch_configs(callable_obj=SMTP, patch_members=patch_members)
