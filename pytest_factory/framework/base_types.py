from __future__ import annotations
import json
from uuid import uuid4
from datetime import datetime
from typing import Any, Dict, Union, List, Tuple, Optional, TypeVar, Set

ALLOWED_TYPES = {int, bytes, str, type(None), bool, dict, type}

HIDDEN_MSG_PROPS = {'exchange_id', '_exchange_id', 'timestamp', '_timestamp'}


def convert(x):
    if isinstance(x, bytes):
        return f"b'{x.decode()}'"
    elif isinstance(x, str):
        return f'"{x}"'
    elif x is None:
        return 'None'
    elif x is True:
        return 'True'
    elif x is False:
        return 'False'
    elif isinstance(x, type):
        return x.__module__ + '.' + x.__name__
    else:
        return str(x)


class Writable:
    def _get_kwargs(self, pre_not_de: bool = False, allowed_types: Optional[Set[type]] = None) -> Dict[str, Any]:
        allowed_types = allowed_types or ALLOWED_TYPES
        d = self.kwargs if pre_not_de and hasattr(self, 'kwargs') else vars(self)
        d = {k: v if type(v) in allowed_types else str(v)
             for k, v in d.items()
             if v is not self and k not in {'__class__', 'kwargs'}}
        return d

    def __str__(self):
        kwargs = {k: v for k, v in self._get_kwargs().items() if k not in HIDDEN_MSG_PROPS}
        return f"<class {self.__class__.__module__}.{self.__class__.__name__}: {kwargs}>"

    def __repr__(self):
        return str(self)

    def write(self, just_args: bool = False) -> str:
        d = self._get_kwargs(pre_not_de=True)
        s = ', '.join([f"{k}={v.split('.')[-1] if k == 'sut_callable' else convert(v)}"
                       for k, v in d.items() if k not in HIDDEN_MSG_PROPS])
        if just_args:
            return s
        return f"{self.__class__.__name__}({s})"

    def serialize(self):
        d = self._get_kwargs(pre_not_de=True)
        return f"{self.__class__}: {json.dumps(d, default=convert)}"


class Message(Writable):
    @property
    def exchange_id(self):
        if not hasattr(self, '_exchange_id'):
            setattr(self, '_exchange_id', uuid4())
        self._exchange_id = self._exchange_id or uuid4()
        return self._exchange_id

    @property
    def timestamp(self):
        if not hasattr(self, '_timestamp'):
            setattr(self, '_timestamp', uuid4())
        self._timestamp = self._timestamp or datetime.utcnow()
        return self._timestamp


OptDateOrStr = Optional[Union[datetime, str]]


class BaseMockRequest(Message):
    """
    dual-purpose class used to represent:
    - Actual Requests when created from parameters of @actual_request
    - Expected Requests when created from parameters of @mock_server
    (or similar factory)

    these are stored in store fixture, indexed by: test name, factory name(s), then BaseMockRequest
    object
    """

    FACTORY_NAME = 'make_factory'
    FACTORY_PATH = 'pytest_factory.framework.factory'

    def __init__(self, exchange_id: Optional[str] = None, timestamp: OptDateOrStr = None):
        timestamp = timestamp or datetime.utcnow()
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        self._timestamp = timestamp
        self._exchange_id = exchange_id

    def compare(self, other) -> bool:
        """
        we are effectively simulating the third-party endpoint's router here. note that "this" is the request object of
        the test double that MAY match actual. the "other" request object is the actual request generated by the
        component under test
        e.g. "https://www.test.com?id=0&loc=1" should match
        "https://www.test.com?loc=1&id=0"
        """
        raise NotImplementedError

    def __hash__(self) -> int:
        """
        this is necessary because https://stackoverflow.com/questions/1608842/types-that-define-eq-are-unhashable
        """
        return id(self)


class BaseMockResponse(Message):
    def __init__(self, exchange_id: str, timestamp: datetime = None):
        self._exchange_id = exchange_id
        self._timestamp = self.timestamp or timestamp


def compare_unknown_types(a, b) -> bool:
    if hasattr(a, 'compare'):
        compare_result = a.compare(b)
    elif hasattr(b, 'compare'):
        compare_result = b.compare(a)
    else:
        compare_result = a == b
    return compare_result


class TrackedResponses(list):
    def __init__(self, *args, exchange_id: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 0
        self.exchange_id = exchange_id

    @classmethod
    def from_any(cls, exchange_id: str, response: Union[Any, List]):
        responses = [response] if not isinstance(response, list) else response
        tracked_responses = [(False, _response) for _response in responses]
        tr = cls(tracked_responses, exchange_id=exchange_id)
        return tr

    def response(self, i=0):
        if len(self) == 0:
            return None
        return self[i][1]

    def mark_and_retrieve_next(self) -> Any:
        if self.count >= len(self):
            self.count += 1
            return None
        response = self[self.count][1]
        self[self.count] = (True, response)
        self.count += 1
        return response


class Factory(dict):
    def __init__(self, req_obj: Union[str, BaseMockRequest], responses: TrackedResponses):
        super().__init__()
        self.__setitem__(req_obj, responses)

    def __setitem__(self, key, value):
        for _key in self.keys():
            if compare_unknown_types(key, _key):
                return
        super().__setitem__(key, value)

    @property
    def get_sut(self) -> Any:
        return list(self.values())[0].response()

    @property
    def FACTORY_NAME(self):
        return list(self.keys())[0]


class BasePlugin:
    """
    to create a pytest-factory plugin, inherit from this base class and define the following:
    - self.PLUGIN_URL
    - self.get_plugin_responses

    PLUGIN_URL is the url that corresponds to the depended-on-component that this plugin simulates
    """
    # TODO seems unnecessary to make this a class - rework to replace with module
    PLUGIN_URL = None

    def __init__(self):
        if self.PLUGIN_URL is None:
            raise NotImplementedError()

    @staticmethod
    def get_plugin_responses(req_obj: BaseMockRequest) -> Any:
        """
        this method will be called by Store.get_next_response when the system-under-test calls a url matching
        self.PLUGIN_URL. the user-defined plugin should override this method to implement a router that returns
        the plugin-defined test double response
        """
        raise NotImplementedError


ROUTING_TYPE = Dict[
    Union[
        Dict[str, Any],
        BaseMockRequest],
    Any
]
T = TypeVar("T")

MAGIC_TYPE = Optional[Union[List[T], T]]

BASE_RESPONSE_TYPE = Union[Exception, T]
MOCK_RESPONSES_TYPE = List[Tuple[bool, BASE_RESPONSE_TYPE]]
ANY_MOCK_RESPONSE = MAGIC_TYPE[BASE_RESPONSE_TYPE[T]]
Exchange = Tuple[Union[BaseMockRequest], BASE_RESPONSE_TYPE]
