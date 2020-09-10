import pytest
from typing import Dict, Optional

from tornado_drill.mock_request_types import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.framework.settings import StoreType

STORES = None


class Store(StoreType):
    """
    stores fixtures for a given async test method
    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def update(self, test_qualname: str, fixture_name: str,
               req_obj: BaseMockRequest,
               response=MOCK_HTTP_RESPONSE):
        test_fixtures = self.fixtures_by_test.get(test_qualname)
        if not test_fixtures:
            new_fixture = {
                fixture_name: {
                    req_obj: response
                }
            }
            self.fixtures_by_test[test_qualname] = new_fixture
        else:
            fixture_def = test_fixtures.get(fixture_name)
            if not fixture_def:
                test_fixtures[fixture_name] = {req_obj: response}
            else:
                fixture_def[req_obj] = response


class Stores:
    def __init__(self, default_store: Optional[Store] = None):
        """
        initialized with fixtures from SETTINGS mapped to a wildcard test name
        '*' so that they will apply to all test functions unless otherwise
        specified.
        """
        self.by_test: Dict[str, Store] = {}
        if default_store:
            self.by_test['*'] = default_store

        global STORES
        STORES = self

    def get_store(self, test_name: str):
        store = self.by_test.get(test_name)
        if not store:
            self.by_test[test_name] = store = self.by_test.get('*') or Store()
        return store


@pytest.fixture(scope='function')
def store(request):
    """
    fixture store
    :return:
    """
    test_name = request.node.name
    global STORES
    store = STORES.get_store(test_name=test_name)
    return store
