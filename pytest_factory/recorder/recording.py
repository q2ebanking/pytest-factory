from __future__ import annotations
from json import loads, dumps, JSONDecodeError
from importlib import import_module
from typing import Any, List, Optional, Union, Tuple

from pytest_factory.framework.base_types import Exchange, BaseMockRequest, BASE_RESPONSE_TYPE, ALLOWED_TYPES


def infer_type(s: Any):
    if type(s) in ALLOWED_TYPES and not isinstance(s, str):
        return s
    r = {
        'None': None,
        'True': True,
        'False': False
    }.get(s, Exception)
    if r is not Exception:
        return r
    if len(s) > 2 and s[:2] in {'b"', "b'"}:
        return s[2:-1].encode()
    try:
        d = loads(s)
        return d
    except JSONDecodeError as _:
        if len(s.split('.')) == 2:
            return float(s)
        try:
            return int(s)
        except ValueError as _:
            return s


def reify(path) -> BASE_RESPONSE_TYPE:
    if not isinstance(path, str) or path[:6] != '<class':
        return path
    path_parts = path.split('\'')[1].split('.')
    kwargs = None
    if len(path.split(':')) > 1:
        kwarg_str = ':'.join(path.split(':')[1:]).strip(' ')
        kwargs = {k: infer_type(v) for k, v in loads(kwarg_str).items()}
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
        r = loads(b_a.decode())
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
        return isinstance(self.last, Exception) or isinstance(self.last, type) and issubclass(self.last, Exception)

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

    def serialize(self) -> bytes:
        sut_exchange = self.sut_exchange
        if self.raises:
            sut_exchange = (sut_exchange[0].serialize(), str(sut_exchange[1]))

        self_dict = {
            'doc_exchanges': self.doc_exchanges,
            'sut_exchange': sut_exchange,
            'incident_type': str(self.incident_type)
        }
        return dumps(self_dict, default=lambda x: x.serialize()).encode()
