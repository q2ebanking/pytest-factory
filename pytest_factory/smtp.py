"""
Mocking support for SMTP
"""
from typing import Callable, Union, List
from smtplib import SMTP, SMTPRecipientsRefused

from pytest_factory.framework.fixture_factory import make_fixture_factory


def smtp(to_addrs: Union[str, List[str]],
         response: str = None,
         ) -> Callable:
    """
    test decorator to mock smtp
    :param to_addrs: recipient e-mail address or addresses as list
    :param response: None success, error code tuple for failures
    :return: test method with smtp fixture attached
    """

    to_addrs = to_addrs if isinstance(to_addrs, list) else [to_addrs]
    return make_fixture_factory(str(to_addrs), response)


def __init__(self, host='', port=0, local_hostname=None,
             timeout=15,
             source_address=None):
    """
    monkeypatch method for SMTP. see method by same name for SMTP to see parameter definitions
    :return:
    """
    pass


def starttls(self, keyfile=None, certfile=None, context=None):
    return 220, ''


def sendmail(self, from_addr: str, to_addrs: Union[str, List[str]], msg, mail_options=(),
             rcpt_options=()):
    """
    monkeypatch method for SMTP. see method by same name for SMTP to see parameter definitions
    :return:
    """

    to_addrs = to_addrs if isinstance(to_addrs, list) else [to_addrs]
    try:
        result = mock_helpers.Q2_HOLDER['smtp'][str(to_addrs)]
    except (KeyError, TypeError):
        return {str(to_addrs): SMTPRecipientsRefused(recipients={addr: 'generic error' for addr in to_addrs})}
    key = str(to_addrs)
    if SMTP_HISTORY.get(key):
        SMTP_HISTORY[key].append(msg)
    else:
        SMTP_HISTORY[key] = [msg]
    return result or {}


def quit(self):
    pass


# this method must always be called to set up the fixture
update_monkey_patch_configs('smtp', SMTP, [__init__, sendmail, quit, starttls])
