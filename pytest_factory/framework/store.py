from typing import Dict, Optional, Any, Union, List, Callable, Set
from functools import cached_property

from tornado.web import RequestHandler

import pytest_factory.framework.exceptions as exceptions
from pytest_factory.outbound_response_double import BaseMockRequest
from pytest_factory import logger

logger = logger.get_logger(__name__)

ROUTING_TYPE = Dict[
    Union[
        Dict[str, Any],
        BaseMockRequest],
    Any
]


def is_plugin(kallable: Callable) -> bool:
    return hasattr(kallable, 'get_plugin_responses')


def compare_unknown_types(a, b) -> bool:
    if hasattr(a, 'compare'):
        compare_result = a.compare(b)
    elif hasattr(b, 'compare'):
        compare_result = b.compare(a)
    else:
        compare_result = a == b
    return compare_result


class MissingHandler(RequestHandler):
    def __init__(self):
        pass

    async def run_test(self):
        raise exceptions.MissingHandlerException


class Store:
    """
    stores test doubles for a given test method
    """

    def __init__(self, _test_name: str, **kwargs):
        self._test_name = _test_name
        self.request_handler_class: Optional[Callable] = None
        self.handler: Optional[RequestHandler] = MissingHandler()
        self.assert_no_extra_calls: Optional[bool] = None
        self.assert_no_missing_calls: Optional[bool] = None
        self.factory_names: Set[str] = set()
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def update(self, req_obj: Union[BaseMockRequest, str], factory_name: str, response: Union[Any, List[Any]]):
        """
        always use this method to modify store AFTER configuration stage ends
        note that this will get invoked depth-first
        :param req_obj:
        :param factory_name:
        :param response:
        """
        responses = [response] if not isinstance(response, list) else response
        responses = [(False, _response) for _response in responses]
        self.factory_names.add(factory_name)
        if not hasattr(self, factory_name):  # store does not already have a test double from factory
            setattr(self, factory_name, {req_obj: responses})
        else:  # store already has test doubles from this factory
            test_double_dict = getattr(self, factory_name)
            if not test_double_dict.get(req_obj):
                test_double_dict[req_obj] = responses

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
        # TODO break up this method!!!
        if not hasattr(self, factory_name):
            raise exceptions.MissingFactoryException(factory_name=factory_name)
        factory = getattr(self, factory_name)
        mock_responses = None
        for k, v in factory.items():
            compare_result = compare_unknown_types(k, req_obj)
            if compare_result:
                if is_plugin(v):
                    try:
                        mock_responses = v.get_plugin_responses(req_obj=req_obj)
                    except exceptions.PytestFactoryBaseException as ex:
                        raise ex
                    except Exception as ex:
                        raise exceptions.UnhandledPluginException(plugin_name=v.__qualname__, exception=ex)
                else:
                    mock_responses = v
                break

        if mock_responses is None:
            raise exceptions.MissingTestDoubleException(req_obj=req_obj)

        for index, (called, response) in enumerate(mock_responses):
            if called:
                continue
            else:
                # if response requires mapping values from original request:
                if isinstance(response, Callable):
                    response = response(req_obj)

                # this is where we mark the response as having been called so
                # we don't call it again unless we are allowed by the user
                mock_responses[index] = (True, response)  # TODO this mechanism is too brittle! what if the plugin handles routing?
                return response

        if mock_responses:
            last_response = mock_responses[-1][1]
            exception = exceptions.OverCalledTestDoubleException(mock_responses=mock_responses,
                                                                 req_obj=req_obj,
                                                                 log_error=self.assert_no_extra_calls)
            if self.assert_no_extra_calls:
                raise exception
            return last_response
        return None

    def register_plugins(self, plugins: Dict[str, Callable]):
        if hasattr(self, 'mock_http_server'):
            self.mock_http_server.update(plugins)
        else:
            setattr(self, 'mock_http_server', plugins)

    @cached_property
    def _get_test_doubles(self) -> Dict[str, ROUTING_TYPE]:
        test_doubles = {factory_name: getattr(self, factory_name) for factory_name in self.factory_names}
        return test_doubles

    def load_defaults(self, default_routes: Dict[str, ROUTING_TYPE]):
        for key, route in default_routes.items():
            if hasattr(self, key):
                getattr(self, key).update(route)
            else:
                setattr(self, key, route)

    def check_no_uncalled_test_doubles(self):
        """
        checks if this Store has any test_doubles that have not been called the
        number of times expected by default, it will log warnings to logger
        :param assert_no_missing_calls: if True, will raise AssertionError if any
            uncalled test_doubles remain
        :return:
        """
        uncalled_test_doubles = {}

        for test_double, response_dict in self._get_test_doubles.items():
            uncalled_test_double_endpoints = {}
            for key, responses in response_dict.items():
                if is_plugin(responses):
                    continue
                uncalled_responses = [resp[1]
                                      for resp in responses if not resp[0]]
                if uncalled_responses:
                    uncalled_test_double_endpoints[key] = uncalled_responses
            if uncalled_test_double_endpoints:
                uncalled_test_doubles[test_double] = uncalled_test_double_endpoints
        if uncalled_test_doubles:
            exception = exceptions.UnCalledTestDoubleException(uncalled_test_doubles=uncalled_test_doubles,
                                                               log_error=self.assert_no_missing_calls)
            if self.assert_no_missing_calls:
                raise exception
