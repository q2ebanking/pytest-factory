from typing import Dict, Optional, Any, Union, List, Callable
from functools import cached_property

from tornado.web import RequestHandler

from pytest_factory.framework.exceptions import UnCalledTestDoubleException, MissingTestDoubleException
from pytest_factory.outbound_response_double import BaseMockRequest
from pytest_factory import logger

logger = logger.get_logger(__name__)

ROUTING_TYPE = Dict[
    Union[
        Dict[str, Any],
        BaseMockRequest],
    Any
]


class Store:
    """
    stores test doubles for a given test method
    """

    def __init__(self, plugins: Optional[Dict[str, Callable]] = None, **kwargs):
        self.handler: Optional[RequestHandler] = None
        self.assert_no_extra_calls: bool = True
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)
        if plugins:
            if hasattr(self, 'mock_http_server'):
                self.mock_http_server.update(plugins)
            else:
                self.mock_http_server = plugins

    def update(self, req_obj: Union[BaseMockRequest, str], factory_name: str, responses: List[Any]):
        if not hasattr(self, factory_name):  # store does not already have a test double from factory
            setattr(self, factory_name, {req_obj: responses})
        else:  # store already has test doubles from this factory
            test_double_dict = getattr(self, factory_name)
            for k, v in test_double_dict.items():
                # store has test double that matches new test double's request object
                if k == req_obj:
                    # overwriting with new test double
                    test_double_dict[k] = responses
                    return

    def get_next_response(self, factory_name: str,
                          req_obj: BaseMockRequest) -> Any:
        """
        will look up responses corresponding to the given parameters, then find
        the next response that has not yet been called, and marks it as called.

        if it runs out of uncalled responses, it will raise AssertionError
        unless Store.assert_no_extra_calls is False. otherwise it will log
        warnings to logger.

        if not response can be found, this indicates a user error in setting up factories such that the expected
        test double was not generated. this will log errors to logger and raise an

        :param factory_name: name of the first factory used to create the response test double
        :param req_obj: the request made by the RequestHandler represented as a
            BaseMockRequest
        :return: the next available mock response corresponding to the given
            req_obj
        """
        assert hasattr(self, factory_name)
        factory = getattr(self, factory_name)
        mock_responses = None
        for k, v in factory.items():
            if k.compare(req_obj):
                if isinstance(v, Callable):
                    mock_responses = v(req_obj)

                else:
                    mock_responses = v
                break

        if mock_responses is None:
            raise MissingTestDoubleException(req_obj=req_obj)

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
            if self.assert_no_extra_calls:
                logger.error(msg)  # TODO do we need these?
                raise AssertionError(msg)
            else:
                logger.warning(f"{msg}, will repeat last response: {last_response}")
            return last_response
        return None

    def register_plugins(self, plugins: Dict[str, Callable]):
        pass

    @cached_property
    def _get_test_doubles(self) -> Dict[str, ROUTING_TYPE]:
        test_doubles = {}
        for key, response_dict in vars(self).items():
            if key not in ['handler', 'assert_no_extra_calls'] \
                    and isinstance(response_dict, dict):
                test_doubles[key] = response_dict
        return test_doubles

    def load_defaults(self, default_routes: Dict[str, ROUTING_TYPE]):
        for key, route in default_routes.items():
            if hasattr(self, key):
                getattr(self, key).update(route)
            else:
                setattr(self, key, route)

    def check_no_uncalled_test_doubles(self, raise_assertion_error: bool = False):
        """
        checks if this Store has any test_doubles that have not been called the
        number of times expected by default, it will log warnings to logger
        :param raise_assertion_error: if True, will raise AssertionError if any
            uncalled test_doubles remain
        :return:
        """
        uncalled_test_doubles = {}

        for test_double, response_dict in self._get_test_doubles.items():
            uncalled_test_double_endpoints = {}
            for key, responses in response_dict.items():
                uncalled_responses = [resp[1]
                                      for resp in responses if not resp[0]]
                if uncalled_responses:
                    uncalled_test_double_endpoints[key] = uncalled_responses
            if uncalled_test_double_endpoints:
                uncalled_test_doubles[test_double] = uncalled_test_double_endpoints
        if uncalled_test_doubles:
            msg = 'the following test_doubles have not been called: ' + \
                  f'{uncalled_test_doubles}!'
            if raise_assertion_error:
                logger.error(msg)
                raise UnCalledTestDoubleException(uncalled_test_doubles=uncalled_test_doubles)
            else:
                logger.warning(f"{msg}, if this is not expected, consider this a test failure!")
