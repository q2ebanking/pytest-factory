from __future__ import annotations
import json
from importlib import import_module
from typing import Any, List, Callable, Optional, Set, Union, Tuple

from pytest_factory.framework.base_types import Exchange, BaseMockRequest, BASE_RESPONSE_TYPE


def reify(path) -> BASE_RESPONSE_TYPE:
    if not isinstance(path, str) or path[:6] != '<class':
        return path
    path_parts = path.split('\'')[1].split('.')
    kwargs = None
    if len(path.split(':')) > 1:
        kwarg_str = path.split('>:')[1]
        kwargs = json.loads(kwarg_str)
    name = '.'.join(path_parts[0:-1]) if len(path_parts) > 2 else None
    module = import_module(name=name)
    kallable = getattr(module, path_parts[-1])
    if kwargs:
        return kallable(**kwargs)
    return kallable


class Recording:
    """
    represents the inputs and output of the SUT, including those of any DOC. can be created from deployed code
    or locally when running pytest
    """

    def __init__(self, incident_type: Union[Exception, type], sut_exchange: Exchange,
                 doc_exchanges: Optional[List[Exchange]] = None) -> None:
        if not isinstance(incident_type, Exception) and not issubclass(incident_type, Exception):
            raise Exception  # TODO
        self.sut_exchange = sut_exchange
        self.doc_exchanges = doc_exchanges or []
        self.incident_type = incident_type

    @classmethod
    def deserialize(cls, b_a: bytes) -> Recording:
        r = json.loads(b_a.decode())
        incident_type_str = r['incident_type']
        incident_type = reify(incident_type_str)
        r['incident_type'] = incident_type
        last = r['sut_exchange'][1]
        first = reify(r['sut_exchange'][0])
        docs = r['doc_exchanges']
        for index, (request_str, response_str) in enumerate(docs):
            reified_doc = (reify(request_str), reify(response_str))
            docs[index] = reified_doc
        if last == incident_type_str:
            last = incident_type
        r['sut_exchange'] = (first, last)
        return Recording(**r)

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
        sut_exchange = self.sut_exchange
        if self.raises:
            sut_exchange = (str(sut_exchange[0]), str(sut_exchange[1]))
        self_dict = {
            'doc_exchanges': self.doc_exchanges,
            'sut_exchange': sut_exchange,
            'incident_type': str(self.incident_type)
        }
        return json.dumps(self_dict, default=str).encode()
