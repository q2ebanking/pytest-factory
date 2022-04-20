from typing import Sequence, Tuple, Dict

from pytest_factory.framework.base_types import BaseMockRequest

MOCK_SMTP_RESPONSE = Dict[str, Tuple[int, str]]


class SMTPRequest(BaseMockRequest):
    def __init__(self,
                 from_addr: str,
                 to_addrs: str | Sequence[str], *args, **kwargs):
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.args = args
        self.kwargs = kwargs

    def compare(self, other) -> bool:
        if isinstance(other, Sequence) or isinstance(other, str):
            return self.to_addrs == other
        elif isinstance(other, SMTPRequest):
            return self.to_addrs == other.to_addrs
        else:
            # TODO raise warning?
            return False
