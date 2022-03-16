from typing import Dict, Optional, Any, Union
from functools import cached_property

from tornado.web import RequestHandler

from pytest_factory.framework.exceptions import UnCalledTestDoubleException
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

    def __init__(self, **kwargs):
        self.handler: Optional[RequestHandler] = None
        self.assert_no_extra_calls: bool = True
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def update(self, req_obj, parent_factory, responses):
        if not hasattr(self, parent_factory):  # store does not already have a test double from factory
            setattr(self, parent_factory, {req_obj: responses})
        else:  # store already has test doubles from this factory
            test_double_dict = getattr(self, parent_factory)
            for k, v in test_double_dict.items():
                # store has test double that matches new test double's request object
                if k == req_obj:
                    # overwriting with new test double
                    test_double_dict[k] = responses
                    return

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
