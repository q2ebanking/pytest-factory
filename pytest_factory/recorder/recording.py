from typing import Any, List, Optional, Set, Union, Tuple

from pytest_factory.framework.base_types import Exchange, BaseMockRequest, BASE_RESPONSE_TYPE


class Recording:
    def __init__(self, incident_type: Exception, sut_exchange: Exchange,
                 doc_exchanges: Optional[List[Exchange]] = None) -> None:
        self.sut_exchange = sut_exchange
        self.doc_exchanges = doc_exchanges or []
        self.incident_type = incident_type

    @property
    def raises(self) -> bool:
        return isinstance(self.last, Exception) or issubclass(self.last, Exception)

    @property
    def first(self) -> Union[Any, BaseMockRequest]:
        return self.sut_exchange[0]

    @property
    def request_factory(self) -> Tuple[str, str]:
        if hasattr(self.first, 'FACTORY_PATH') and hasattr(self.first, 'FACTORY_NAME'):
            return getattr(self.first, 'FACTORY_PATH'), getattr(self.first, 'FACTORY_NAME')
        else:
            return 'pytest_factory.framework.factory', 'make_factory'

    @property
    def last(self) -> BASE_RESPONSE_TYPE:
        return self.sut_exchange[1]

    def get_factories(self) -> Set[str]:
        factories = {(request.FACTORY_PATH, request.FACTORY_NAME) for request, _ in self.doc_exchanges}
        return factories

    def serialize(self) -> bytes:
        return b'TODO'
