from typing import Sequence, Tuple, Dict, Union, Optional

from pytest_factory.framework.base_types import BaseMockRequest

MOCK_SMTP_RESPONSE = Union[Exception, Dict[str, Tuple[int, str]]]


class SMTPRequest(BaseMockRequest):
    def __init__(self,
                 from_addr: str,
                 to_addrs: str | Sequence[str], *args,
                 host: Optional[str],
                 **kwargs):
        self.host = host
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.args = args
        self.kwargs = {**kwargs, **{'from_addr': from_addr, 'to_addrs': to_addrs, 'host': host}}

    def compare(self, other) -> bool:
        attr_name = 'host' if self.host else 'to_addrs'
        if isinstance(other, Sequence) or isinstance(other, str):
            return getattr(self, attr_name) == other
        elif isinstance(other, SMTPRequest):
            addr_agreement = self.to_addrs == other.to_addrs if attr_name == 'host' else True
            return getattr(self, attr_name) == getattr(other, attr_name) and addr_agreement
        else:
            # TODO raise warning?
            return False

    def __str__(self) -> str:
        return f"{self.__class__}:{self.kwargs}"
