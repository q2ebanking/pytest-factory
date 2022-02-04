from typing import Dict, Any, Optional, List, Union
from types import ModuleType

from tornado.web import RequestHandler

import pytest_factory.mock_request_types as mrt
from pytest_factory.framework.settings import LOGGER

STORES = None


class Store:
    """
    stores fixtures for a given async test method
    """

    def __init__(self, **kwargs):
        self.handler: Optional[RequestHandler] = None
        self.assert_no_extra_calls: bool = True
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    @property
    def get_fixtures(self) -> Dict[str, mrt.ROUTING_TYPE]:
        fixtures = {}
        for fixture, response_dict in vars(self).items():
            if fixture not in ['handler', 'assert_no_extra_calls'] \
                    and isinstance(response_dict, dict):
                fixtures[fixture] = response_dict
        return fixtures

    def load_defaults(self, default_routes: Dict[str, mrt.ROUTING_TYPE]):
        for fixture_name, route in default_routes.items():
            if hasattr(self, fixture_name):
                getattr(self, fixture_name).update(route)
            else:
                setattr(self, fixture_name, route)

    def check_no_uncalled_fixtures(self, raise_assertion_error: bool = False):
        """
        checks if this Store has any fixtures that have not been called the
        number of times expected by default, it will log warnings to LOGGER
        :param raise_assertion_error: if True, will raise AssertionError if any
            uncalled fixtures remain
        :return:
        """
        uncalled_fixtures = {}

        for fixture, response_dict in self.get_fixtures.items():
            uncalled_fixture_endpoints = {}
            for key, responses in response_dict.items():
                uncalled_responses = [resp[1]
                                      for resp in responses if not resp[0]]
                if uncalled_responses:
                    uncalled_fixture_endpoints[key] = uncalled_responses
            if uncalled_fixture_endpoints:
                uncalled_fixtures[fixture] = uncalled_fixture_endpoints
        if uncalled_fixtures:
            msg = 'the following fixtures have not been called: ' + \
                  f'{uncalled_fixtures}!'
            if raise_assertion_error:
                LOGGER.error(msg)
                raise AssertionError(msg)
            else:
                LOGGER.warning(msg, 'if this is not expected, consider '
                               + 'this a test failure!')


class Stores:
    """
    this class contains all of the stores for all collected tests and defines
    convenience methods for looking up fixtures
    """

    def __init__(self):
        self._by_test: Dict[str, Store] = {}

    def load(self, default_store: Store):
        """
        # TODO rework so it gets applied to child Store
        # TODO this needs to work to load mock adapters
        load with fixture factories from SETTINGS mapped to a wildcard test
        name '*' so that they will apply to all test functions unless otherwise
        specified.

        always use this method to modify STORES BEFORE configuration stage ends

        :param default_store: the store to fall back on if no test-specific
            store is defined normally passed in from Settings
        """
        if default_store:
            self._by_test['*'] = default_store

    def update(self, test_name: str, factory_name: str,
               req_signature: Union[mrt.BaseMockRequest, str],
               response: mrt.MOCK_HTTP_RESPONSE = None,
               failure_modes: Optional[List[mrt.FailureMode]] = None):
        """
        TODO update so when
        always use this method to modify STORES AFTER configuration stage ends

        :param test_name: name of the pytest test function not including
            modules or classes
        :param factory_name: name of the fixture factory e.g. mock_http_server

        :param req_signature: used as key to map to mock responses; either a BaseMockRequest type object or a string
        :param response: MOCK_HTTP_RESPONSE
        :param failure_modes: failure modes associated with the given factory
        :return:
        """
        # this is how we keep track of which fixtures have been used
        response = (False, response)
        responses = [response] if not isinstance(response, list) else response

        store = self.get_store(test_name)
        if not store:
            self._by_test[test_name] = Store(**{
                factory_name: {
                    req_signature: responses,
                    '_failure_modes': failure_modes or []
                }
            })
        else:
            if not hasattr(store, factory_name):
                setattr(store, factory_name, {req_signature: responses})
            else:
                fixture_dict = getattr(store, factory_name)
                for k, v in fixture_dict.items():
                    existing_key = k if isinstance(k, str) else k.key
                    new_key = req_signature if isinstance(req_signature, str) else req_signature.key
                    if existing_key != new_key:
                        fixture_dict[k] = responses
                        break

    def get_store(self, test_name: str) -> Store:
        """
        :param test_name: name of the pytest test function associated with the
            requested store
        :return: the Store associated with the given test_name; a new Store if
            a Store has not already been created for this test
        """
        store = self._by_test.get(test_name)
        if not store:
            store = Store()
            self._by_test[test_name] = store
        return store

    def get_next_response(self, test_name: str, factory_name: str,
                          req_obj: mrt.BaseMockRequest) -> Any:
        """
        will look up responses corresponding to the given parameters, then find
        the next response that has not yet been called, and marks it as called.

        if it runs out of uncalled responses, it will raise AssertionError
        unless Store.assert_no_extra_calls is False. otherwise it will log
        warnings to LOGGER.

        :param test_name: name of the pytest test function we are currently
            executing
        :param factory_name: name of the fixture being invoked
        :param req_obj: the request made by the RequestHandler represented as a
            BaseMockRequest
        :return: the next available mock response corresponding to the given
            req_obj
        """
        store = self.get_store(test_name=test_name)
        assert hasattr(store, factory_name)
        fixture = getattr(store, factory_name)
        mock_responses = fixture.get('*')
        for k, v in fixture.items():
            if hash(k) == hash(req_obj):
                if type(v) is dict and type(list(v.values)[0]) is ModuleType:
                    # then we need to go down a level into fixtures associated with module
                    mock_responses =
                else:
                    mock_responses = v
                break

        for index, (called, response) in enumerate(mock_responses):
            if called:
                continue
            else:
                # this is where we mark the response as having been called so
                # we don't call it again
                # unless we are allowed by the user
                mock_responses[index] = (True, response)
                return response

        if mock_responses:
            last_response = mock_responses[-1][1]
            msg = 'UNEXPECTED CALL DETECTED. expected only ' + \
                  f'{len(mock_responses)} calls to {req_obj}'
            if store.assert_no_extra_calls:
                LOGGER.error(msg)  # TODO do we need these?
                raise AssertionError(msg)
            else:
                LOGGER.warning(
                    msg, f'will repeat last response: {last_response}')
            return last_response
        return None


STORES = Stores()
