from __future__ import annotations
from json import loads, dumps, JSONDecodeError
from importlib import import_module
from typing import Any, List, Optional, Union, Tuple
from datetime import datetime

import pytest_factory.framework.base_types as types
from pytest_factory.framework.exceptions import RecorderException


class LiveException(types.Writable, Exception):
    pass


def infer_type(s: Any):
    if type(s) in types.ALLOWED_TYPES and not isinstance(s, str):
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


def deserialize(path) -> types.BASE_RESPONSE_TYPE[types.Message]:
    if not isinstance(path, str) or path[:6] != '<class':
        return path
    path_parts = path.split('\'')[1].split('.')
    kwargs = None
    if len(path.split(':')) > 1:
        kwarg_str = ':'.join(path.split(':')[1:]).strip(' ')
        kwargs = {k: infer_type(v) for k, v in loads(kwarg_str).items()}
    if len(path_parts) > 1:
        name = '.'.join(path_parts[0:-1])
        module = import_module(name=name)
        kallable = getattr(module, path_parts[-1])
    elif len(path_parts) == 1:
        kallable = __builtins__.get(path_parts[0])
    else:
        raise Exception
    if kwargs:
        return kallable(**kwargs)
    return kallable


class Recording(types.Message):
    """
    represents the inputs and output of the SUT, including those of any DOC. can be created from deployed code
    or locally when running pytest
    """

    def __init__(self, incident_type: Union[Exception, type], sut_exchange: types.Exchange,
                 doc_exchanges: Optional[List[types.Exchange]] = None) -> None:
        """
        :param incident_type: the Exception whose raising led to the system-under-test needing to ship out a Recording
        :param sut_exchange: the Exchange of the Message received by the system-under-test and the Message to be sent
        :param doc_exchanges: the list of Exchanges between the system-under-test and its depended-on-components
        """
        if not isinstance(incident_type, Exception) and not issubclass(incident_type, Exception):
            raise RecorderException(log_msg=f"Recording.__init__ expects incident_type to be of type "
                                            f"Exception, not {type(incident_type)}!")
        # TODO more validation?
        self.sut_exchange = sut_exchange
        self.handler_path = self.first.handler_class_path if hasattr(self.first, 'handler_class_path') else None  # TODO needed?
        self.doc_exchanges = doc_exchanges or []
        self.incident_type = incident_type
        self.created_at = datetime.utcnow()

    @classmethod
    def deserialize(cls, b_a: bytes) -> Recording:
        r = loads(b_a.decode())
        incident_type_str = r['incident_type']
        incident_type = deserialize(incident_type_str)
        r['incident_type'] = incident_type
        last = r['sut_exchange'][1]
        first = deserialize(r['sut_exchange'][0])
        docs = r['doc_exchanges']
        for index, (request_str, response_str) in enumerate(docs):
            reified_doc = (deserialize(request_str), deserialize(response_str))
            docs[index] = reified_doc
        if last == incident_type_str:
            last = incident_type
        else:
            last = deserialize(last)
        r['sut_exchange'] = (first, last)
        return Recording(**r)

    @property
    def raises(self) -> bool:
        return isinstance(self.last, Exception) or isinstance(self.last, type) and issubclass(self.last, Exception)

    @property
    def first(self) -> Union[Any, types.BaseMockRequest]:
        return self.sut_exchange[0]

    @property
    def request_factory(self) -> Tuple[str, str]:
        if hasattr(self.first, 'FACTORY_PATH') and hasattr(self.first, 'FACTORY_NAME'):
            return getattr(self.first, 'FACTORY_PATH'), getattr(self.first, 'FACTORY_NAME')
        else:
            return 'pytest_factory.framework.factory', 'make_factory'

    @property
    def last(self) -> types.BASE_RESPONSE_TYPE:
        return self.sut_exchange[1]

    def serialize(self) -> bytes:
        sut_exchange = self.sut_exchange
        if self.raises:
            sut_exchange = (sut_exchange[0].serialize(), str(sut_exchange[1]))

        self_dict = {
            'doc_exchanges': self.doc_exchanges,
            'sut_exchange': sut_exchange,
            'incident_type': self.incident_type
        }
        return dumps(self_dict, default=serialize_default).encode()


def serialize_default(x):
    if hasattr(x, 'serialize'):
        return x.serialize()
    else:
        return str(x)
