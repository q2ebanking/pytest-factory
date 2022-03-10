from typing import Dict, Any, Optional, List, Union
from types import ModuleType

from tornado.web import RequestHandler
from configparser import ConfigParser

import pytest_factory.outbound_mock_request as mrt
from pytest_factory.framework.exceptions import FixtureNotFoundException, FixtureNotCalledException
from pytest_factory import logger

logger = logger.get_logger(__name__)

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
                raise FixtureNotCalledException(uncalled_fixtures=uncalled_fixtures)
            else:
                logger.warning(f"{msg}, if this is not expected, consider this a test failure!")


class Stores:
    """
    this class contains all of the stores for all collected tests and defines
    convenience methods for looking up fixtures
    """

    def __init__(self):
        self._by_test: Dict[str, Store] = {}
        self._by_dir: Dict[str, Store] = {}
        self.default_handler_class = None
        self.handler_monkeypatches = {}

    def load(self, conf: ConfigParser, key: str):
        """
        # TODO rework so it gets applied to child Store

        always use this method to modify STORES BEFORE configuration stage ends

        :param init_store: the store to fall back on if no test-specific
            store is defined normally passed in from Settings
        """
        # TODO iterate over self._from_config to populate self._by_test EXCEPT where keys collide!
        # NOTE Took this over for the directory-level update
        # NOTE removed the init_store arg b/c I'm not sure what it was supposed to do
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

    def update(self, test_name: str, factory_names: Union[str, List[str]],
               req_obj: Union[mrt.BaseMockRequest, str],
               response: mrt.MOCK_HTTP_RESPONSE = None,
               failure_modes: Optional[List[mrt.FailureMode]] = None):
        """
        always use this method to modify STORES AFTER configuration stage ends

        :param test_name: name of the pytest test function not including
            modules or classes
        :param factory_names: names of the fixture factories used for the fixture being updated in the store e.g. mock_http_server

        :param req_obj: used as key to map to mock responses; either a BaseMockRequest type object or a string
        :param response: MOCK_HTTP_RESPONSE
        :param failure_modes: failure modes associated with the given factory
        :return:
        """
        # this is how we keep track of which fixtures have been used
        response = (False, response)
        assert 1 <= len(factory_names) <= 2, ""  # TODO make something happen here
        responses = [response] if not isinstance(response, list) else response
        parent_factory = factory_names[0]
        child_factory = factory_names[1] if len(factory_names) == 2 else None

        store = self.get_store(test_name)
        if not store:
            self._by_test[test_name] = Store(**{
                parent_factory: {
                    req_obj: responses,
                    '_failure_modes': failure_modes or []
                }
            })
        else:
            if not hasattr(store, parent_factory):
                setattr(store, parent_factory, {req_obj: responses})
            else:
                fixture_dict = getattr(store, parent_factory)
                for k, v in fixture_dict.items():
                    if k == req_obj:
                        # TODO handle child_factory!!!
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

    def get_next_response(self, test_name: str, factory_names: List[str],
                          req_obj: mrt.BaseMockRequest) -> Any:
        """
        will look up responses corresponding to the given parameters, then find
        the next response that has not yet been called, and marks it as called.

        if it runs out of uncalled responses, it will raise AssertionError
        unless Store.assert_no_extra_calls is False. otherwise it will log
        warnings to LOGGER.

        if not response can be found, this indicates a user error in setting up factories such that the expected
        fixture was not generated. this will log errors to LOGGER and raise an

        :param test_name: name of the pytest test function we are currently
            executing
        :param factory_names: names of the factories used to create the response fixture
        :param req_obj: the request made by the RequestHandler represented as a
            BaseMockRequest
        :return: the next available mock response corresponding to the given
            req_obj
        """
        store = self.get_store(test_name=test_name)
        assert hasattr(store, factory_names[0])
        factory = getattr(store, factory_names[0])
        mock_responses = None
        for k, v in factory.items():
            if k.compare(req_obj):
                if type(v) is dict and type(list(v.values)[0]) is ModuleType:
                    # then we need to go down a level into fixtures associated with module
                    mock_responses = v.get(
                        factory_names[1])  # TODO is this safe to assume only two levels of factory nesting?
                else:
                    mock_responses = v
                break

        if mock_responses is None:
            raise FixtureNotFoundException(req_obj=req_obj)  # TODO do we need to pass more here?

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
            msg = f'UNEXPECTED CALL DETECTED. expected only {len(mock_responses)} calls to {req_obj}'
            if store.assert_no_extra_calls:
                logger.error(msg)  # TODO do we need these?
                raise AssertionError(msg)
            else:
                logger.warning(f"{msg}, will repeat last response: {last_response}")
            return last_response
        return None


STORES = Stores()
