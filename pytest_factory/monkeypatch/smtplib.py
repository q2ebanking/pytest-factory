from typing import Sequence
from smtplib import SMTP

from pytest_factory.framework.mall import MALL
from pytest_factory.monkeypatch.utils import update_monkey_patch_configs
from pytest_factory.framework.smtp_types import MOCK_SMTP_RESPONSE

ERR_CODE = 1  # TODO
ERR_MSG = 'FAKE_ERROR' # TODO


class SMTPMonkeyPatches(SMTP):
    def sendmail(self,
                 from_addr: str,
                 to_addrs: str | Sequence[str],
                 msg: bytes | str,
                 mail_options: Sequence[str] = ...,
                 rcpt_options: Sequence[str] = ...,
                 ) -> MOCK_SMTP_RESPONSE:
        store = MALL.get_store()
        resp = store.get_next_response(factory_name='mock_smtp_server', req_obj=to_addrs)
        if resp is None:
            resp = {addr: (ERR_CODE, ERR_MSG) for addr in to_addrs}
        return resp

    def send(self, s):
        # TODO use host to further route
        pass


patch_members = {
    'sendmail': SMTPMonkeyPatches.sendmail,
    'send': SMTPMonkeyPatches.send
}
update_monkey_patch_configs(callable_obj=SMTP, patch_members=patch_members)
