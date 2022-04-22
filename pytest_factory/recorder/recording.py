from typing import Tuple, List, Optional, Set, Union

from pytest_factory.http import MOCK_HTTP_RESPONSE, MockHttpRequest

Exchange = Tuple[MockHttpRequest, MOCK_HTTP_RESPONSE]


class Recording:
    def __init__(self, incident_type: Exception, sut_exchange: Exchange,
                 doc_exchanges: Optional[List[Exchange]] = None) -> None:
        self.sut_exchange = sut_exchange
        self.doc_exchanges = doc_exchanges or []
        self.incident_type = incident_type

    @property
    def raises(self) -> bool:
        return isinstance(self.last, type) and issubclass(self.last, Exception)

    @property
    def first(self) -> MockHttpRequest:
        return self.sut_exchange[0]

    @property
    def last(self) -> Union[MOCK_HTTP_RESPONSE, type]:
        return self.sut_exchange[1]

    def get_factories(self) -> Set[str]:
        factories = {(request.FACTORY_PATH, request.FACTORY_NAME) for request, _ in self.doc_exchanges}
        return factories

    def serialize(self) -> bytes:
        return b'TODO'
