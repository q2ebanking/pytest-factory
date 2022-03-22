from __future__ import annotations
from typing import Dict, Any, Optional, List, Union, Callable
from functools import cached_property

from pytest_factory.outbound_response_double import BaseMockRequest
from pytest_factory.framework.store import Store, is_plugin
from pytest_factory import logger

logger = logger.get_logger(__name__)


class Mall:
    """
    this class contains all the stores for all collected tests and defines
    convenience methods for looking up test doubles
    """

    def __init__(self):
        self._by_test: Dict[str, Store] = {}
        self._by_dir: Dict[str, Dict] = {}

    def _get_prop(self, key: str) -> Any:
        return self._by_dir.get('tests', {}).get(key)

    @property
    def http_req_wildcard_fields(self) -> List[str]:
        return self._get_prop('http_req_wildcard_fields')

    @property
    def request_handler_class(self) -> Callable:
        return self._get_prop('request_handler_class')

    @property
    def assert_no_missing_calls(self) -> bool:
        return self._get_prop('assert_no_missing_calls')

    @property
    def assert_no_extra_calls(self) -> bool:
        return self._get_prop('assert_no_extra_calls')

    def load(self, conf: dict, key: str) -> dict:
        """
        always use this method to modify MALL BEFORE configuration stage ends

        :param conf: the store config to fall back on if no test-specific
            store is defined normally passed in from Settings
        :param key:
        """

        if self._by_dir.get(key):
            # New values in conf will by combined with values in self._by_dir
            # If the same key exists in both, the one in self._by_dir wins
            conf.update(self._by_dir[key])
            # Reset self._by_dir with the updated values
            self._by_dir = conf
        else:
            # If self._by_dir doesn't have anything for the key yet,
            # add the entire dict
            self._by_dir[key] = conf

        return self._by_dir

    @cached_property
    def plugins(self) -> Dict[str, Callable]:
        return_dict = {}
        for _, v in self._by_dir.get('tests').items():
            if is_plugin(v):
                return_dict[v.PLUGIN_URL] = v
        return return_dict

    def get_store(self, test_name: str) -> Store:
        """
        :param test_name: name of the pytest test function associated with the
            requested store
        :return: the Store associated with the given test_name; a new Store if
            a Store has not already been created for this test
        """
        store = self._by_test.get(test_name)
        if not store:
            store = Store(_test_name=test_name)

            self._by_test[test_name] = store
        return store


MALL = Mall()
