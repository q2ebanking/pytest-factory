import pytest
from warnings import warn
from typing import Dict, Any, Optional

from tornado.web import RequestHandler

from tornado_drill.mock_request_types import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.framework.settings import StoreType

STORES = None


class Store(StoreType):
    """
    stores fixtures for a given async test method
    """

    def __init__(self, **kwargs):
        self.handler: Optional[RequestHandler] = None
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def reset(self):
        for fixture_name, fixture in vars(self).items():
            if fixture_name != 'handler':
                for req, responses in fixture.items():
                    reset_responses = [(False, response_tuple[1]) for response_tuple in responses]
                    fixture[req] = reset_responses




class Stores:
    def __init__(self):
        self.by_test: Dict[str, Store] = {}

    def reset(self, test_name: str):
        self.get_store(test_name=test_name).reset()

    def load(self, default_store: Store):
        """
        load with fixtures from SETTINGS mapped to a wildcard test name
        '*' so that they will apply to all test functions unless otherwise
        specified.
        """
        if default_store:
            self.by_test['*'] = default_store

    def update(self, test_name: str, fixture_name: str,
               req_obj: BaseMockRequest,
               response: MOCK_HTTP_RESPONSE):
        # this is how we keep track of which fixtures have been used
        response = (False, response)
        responses = [response] if not isinstance(response, list) else response

        test_fixtures = self.get_store(test_name)
        if not test_fixtures:
            self.by_test[test_name] = Store(**{
                fixture_name: {
                    req_obj: responses
                }
            })
        else:
            if not hasattr(test_fixtures, fixture_name):
                setattr(test_fixtures, fixture_name, {req_obj: responses})
            else:
                fixture_dict = getattr(test_fixtures, fixture_name)
                for k, v in fixture_dict.items():
                    if k.__hash__() != req_obj.__hash__():
                        fixture_dict[k] = responses
                        break

    def get_store(self, test_name: str) -> Store:
        store = self.by_test.get(test_name)
        if not store:
            store = Store()
            self.by_test[test_name] = store
        return store

    def get_next_response(self, test_name: str, fixture_name: str, req_obj: BaseMockRequest) -> Any:
        store = self.get_store(test_name=test_name)
        assert hasattr(store, fixture_name)
        fixture = getattr(store, fixture_name)
        mock_responses = fixture.get('*')
        for k, v in fixture.items():
            if k.__hash__() == req_obj.__hash__():
                mock_responses = v
                break

        for index, (called, response) in enumerate(mock_responses):
            if called:
                continue
            else:
                mock_responses[index] = (True, response)
                return response

        if mock_responses:
            warn(f'TORNADO-DRILL WARNING: UNEXPECTED CALL DETECTED. expected only {len(mock_responses)} calls to {req_obj}')
        return None

    def get_uncalled_fixtures(self, test_name: str) -> dict:
        store = self.get_store(test_name=test_name)
        uncalled_fixtures = {}
        if len(vars(
                store)) > 1:  # a Store will always at least have handler but we only care if it has other fixtures

            props = {k: v for k, v in vars(store).items() if v != store.handler}
            for fixture, response_dict in props.items():
                uncalled_fixture_endpoints = {}
                for key, responses in response_dict.items():
                    uncalled_responses = [resp[1] for resp in responses if not resp[0]]
                    if uncalled_responses:
                        uncalled_fixture_endpoints[key] = uncalled_responses
                if uncalled_fixture_endpoints:
                    uncalled_fixtures[fixture] = uncalled_fixture_endpoints
        return uncalled_fixtures


STORES = Stores()


def get_unique_test_name(request) -> str:
    return request.module.__name__ + '.' + request.node.name


@pytest.fixture(scope='function')
def store(request):
    """
    fixture store
    :return:
    """
    test_name = request.node.name
    global STORES
    store = STORES.get_store(test_name=test_name)
    assert store, 'TORNADO-DRILL ERROR: you broke something. probably in helpers.py'
    return store
