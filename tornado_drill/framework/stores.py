import pytest
from typing import Dict, Any, Optional

from tornado.web import RequestHandler

from tornado_drill.mock_request_types import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.framework.settings import StoreType, LOGGER

STORES = None


class Store(StoreType):
    """
    stores fixtures for a given async test method
    """

    def __init__(self, **kwargs):
        self.handler: Optional[RequestHandler] = None
        self.assert_no_extra_calls: bool = True
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def check_no_uncalled_fixtures(self, raise_assertion_error: bool = False):
        """
        checks if this Store has any fixtures that have not been called the number of times expected
        by default, it will log warnings to LOGGER
        :param raise_assertion_error: if True, will raise AssertionError if any uncalled fixtures remain
        :return:
        """
        uncalled_fixtures = {}
        if len(vars(self)) > 1:  # a Store will always at least have handler but we only care if it has other fixtures

            props = {k: v for k, v in vars(self).items() if isinstance(v, dict)}
            for fixture, response_dict in props.items():
                uncalled_fixture_endpoints = {}
                for key, responses in response_dict.items():
                    uncalled_responses = [resp[1] for resp in responses if not resp[0]]
                    if uncalled_responses:
                        uncalled_fixture_endpoints[key] = uncalled_responses
                if uncalled_fixture_endpoints:
                    uncalled_fixtures[fixture] = uncalled_fixture_endpoints
        if uncalled_fixtures:
            msg = f'the following fixtures have not been called: {uncalled_fixtures}!'
            if raise_assertion_error:
                LOGGER.error(msg)
                raise AssertionError(msg)
            else:
                LOGGER.warning(msg, 'if this is not expected, consider this a test failure!')

    def reset(self):
        for fixture_name, fixture in vars(self).items():
            if fixture_name not in ['handler', 'assert_no_extra_calls']:
                for req, responses in fixture.items():
                    reset_responses = [(False, response_tuple[1]) for response_tuple in responses]
                    fixture[req] = reset_responses


class Stores:
    """
    this class contains all of the stores for all collected tests and defines
    convenience methods for looking up fixtures
    """

    def __init__(self):
        self._by_test: Dict[str, Store] = {}

    def load(self, default_store: Store):
        """
        load with fixtures from SETTINGS mapped to a wildcard test name
        '*' so that they will apply to all test functions unless otherwise
        specified.

        always use this method to modify STORES BEFORE configuration stage ends
        
        :param default_store: the store to fall back on if no test-specific store is defined
            normally passed in from Settings
        """
        if default_store:
            self._by_test['*'] = default_store

    def update(self, test_name: str, fixture_name: str,
               req_obj: BaseMockRequest,
               response: MOCK_HTTP_RESPONSE):
        """
        always use this method to modify STORES AFTER configuration stage ends

        :param test_name: name of the pytest test function not including modules or classes 
        :param fixture_name: name of the tornado-drill fixture e.g. mock_http_server
        :param req_obj: BaseMockRequest object representing the expected request
        :param response: MOCK_HTTP_RESPONSE
        :return: 
        """
        # this is how we keep track of which fixtures have been used
        response = (False, response)
        responses = [response] if not isinstance(response, list) else response

        test_fixtures = self.get_store(test_name)
        if not test_fixtures:
            self._by_test[test_name] = Store(**{
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
                    if hash(k) != hash(req_obj):
                        fixture_dict[k] = responses
                        break

    def get_store(self, test_name: str) -> Store:
        """
        :param test_name: name of the pytest test function associated with the requested store
        :return: the Store associated with the given test_name; if a Store has not already been created for this test
            this will be a new, empty Store object
        """
        store = self._by_test.get(test_name)
        if not store:
            store = Store()
            self._by_test[test_name] = store
        return store

    def get_next_response(self, test_name: str, fixture_name: str, req_obj: BaseMockRequest) -> Any:
        """
        will look up responses corresponding to the given parameters, then find the next response that
        has not yet been called, and marks it as called.

        if it runs out of uncalled responses, it will raise AssertionError
        unless Store.assert_no_extra_calls is False. otherwise it will log warnings to LOGGER.

        :param test_name: name of the pytest test function we are currently executing
        :param fixture_name: name of the fixture being invoked
        :param req_obj: the request made by the RequestHandler represented as a BaseMockRequest
        :return: the next available mock response corresponding to the given req_obj
        """
        store = self.get_store(test_name=test_name)
        assert hasattr(store, fixture_name)
        fixture = getattr(store, fixture_name)
        mock_responses = fixture.get('*')
        for k, v in fixture.items():
            if hash(k) == hash(req_obj):
                mock_responses = v
                break

        for index, (called, response) in enumerate(mock_responses):
            if called:
                continue
            else:
                # this is where we mark the response as having been called so we don't call it again
                # unless we are allowed by the user
                mock_responses[index] = (True, response)
                return response

        if mock_responses:
            last_response = mock_responses[-1][1]
            msg = f'UNEXPECTED CALL DETECTED. expected only {len(mock_responses)} calls to {req_obj}'
            if store.assert_no_extra_calls:
                LOGGER.error(msg)  # TODO do we need these?
                raise AssertionError(msg)
            else:
                LOGGER.warning(msg, f'will repeat last response: {last_response}')
            return last_response
        return None


STORES = Stores()


@pytest.fixture(scope='function')
def store(request):
    """
    fixture store - this is where the test-specific store gets assigned to the test function
    :return:
    """
    test_name = request.node.name
    global STORES
    store = STORES.get_store(test_name=test_name)
    assert store, 'TORNADO-DRILL ERROR: you broke something. probably in helpers.py or in this module'
    return store
