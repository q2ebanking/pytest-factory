from __future__ import annotations
from typing import Dict, Optional, Any, Union, List, Callable, Set, Tuple
from functools import cached_property

import pytest_factory.framework.exceptions as exceptions
from pytest_factory.framework.base_types import Factory, BaseMockRequest, MOCK_RESPONSES_TYPE, ROUTING_TYPE
from pytest_factory import logger
from pytest_factory.framework.default_configs import (assert_no_missing_calls as default_assert_no_missing_calls,
                                                      assert_no_extra_calls as default_assert_no_extra_calls)

logger = logger.get_logger(__name__)


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


class Store:
    """
    stores test doubles for a given test method
    """

    def __init__(self, _test_name: str, **kwargs):
        self._test_name = _test_name
        self.request_handler_class: Optional[Callable] = None
        self._request_factory: Optional[Factory] = None
        self.assert_no_extra_calls: bool = default_assert_no_extra_calls
        self.assert_no_missing_calls: bool = default_assert_no_missing_calls
        self.factory_names: Set[str] = set()
        self.messages = []
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    @property
    def handler(self) -> object:
        if not self._request_factory:
            raise exceptions.MissingHandlerException
        return list(self._request_factory.values())[0]

    def open(self, **kwargs) -> Shopper:
        return Shopper(store=self, **kwargs)

    def checkout(self, response: Any) -> Any:
        self.messages.append(response)
        return self.messages[-1]

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
            new_factory = Factory(req_obj=req_obj, responses=responses)
            setattr(self, factory_name, new_factory)
        else:  # store already has test doubles from this factory
            old_factory = getattr(self, factory_name)
            if not old_factory.get(req_obj):
                old_factory[req_obj] = responses

    def get_next_response(self, factory_name: str,
                          req_obj: BaseMockRequest) -> Any:
        """
        will look up responses corresponding to the given parameters, then find
        the next response that has not yet been called, and marks it as called.

        if it runs out of uncalled responses, it will raise OverCalledTestDoubleException
        unless Store.assert_no_extra_calls is False. otherwise it will log
        warnings to logger.

        if not response can be found, this indicates a user error in setting up factories such that the expected
        test double was not generated. this will log errors to logger and raise an MissingTestDoubleException if
        the factory exists but test double does not, or MissingFactoryException if the factory also does not exist

        :param factory_name: name of the first factory used to create the response test double
        :param req_obj: the request made by the RequestHandler represented as a
            BaseMockRequest
        :return: the next available mock response corresponding to the given
            req_obj
        """
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
        final_response, mock_responses = self._mark_and_retrieve_test_double(req_obj=req_obj,
                                                                             mock_responses=mock_responses)
        self.messages.extend([req_obj, final_response])

        if mock_responses and final_response is None:
            final_response = self._check_overcalled_test_doubles(req_obj=req_obj, mock_responses=mock_responses)
        return final_response

    @staticmethod
    def _mark_and_retrieve_test_double(req_obj: BaseMockRequest,
                                       mock_responses: MOCK_RESPONSES_TYPE) -> Tuple[
        Optional[Any], MOCK_RESPONSES_TYPE]:
        final_response = None
        for index, (called, response) in enumerate(mock_responses):
            if called:
                continue
            else:
                # if response requires mapping values from original request:
                if isinstance(response, Callable):
                    final_response = response(req_obj)
                else:
                    final_response = response

                # this is where we mark the response as having been called so
                # we don't call it again unless we are allowed by the user
                mock_responses[index] = (True, response)
        return final_response, mock_responses

    def _check_overcalled_test_doubles(self, req_obj: BaseMockRequest, mock_responses: MOCK_RESPONSES_TYPE) -> Any:
        final_response = mock_responses[-1][1]
        exception = exceptions.OverCalledTestDoubleException(mock_responses=mock_responses,
                                                             req_obj=req_obj,
                                                             log_error=self.assert_no_extra_calls)
        if self.assert_no_extra_calls:
            raise exception
        return final_response

    def register_plugins(self, plugins: Dict[str, Callable]):
        if hasattr(self, 'mock_http_server'):
            self.mock_http_server.update(plugins)
        else:
            setattr(self, 'mock_http_server', plugins)

    @cached_property
    def _get_test_doubles(self) -> Dict[str, ROUTING_TYPE]:
        test_doubles = {factory_name: getattr(self, factory_name)
                        for factory_name in self.factory_names
                        if factory_name is not list(self._request_factory.keys())[0]}
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


class Shopper:
    def __init__(self, response_attr: str, request_attr: str, store: Store, *_, **kwargs):
        self.store = store
        self.response_attr = response_attr
        self.request_attr = request_attr
        for k, v in kwargs.items():
            setattr(self.store, k, v)

    def __enter__(self):
        sut_input = getattr(self.store.handler, self.request_attr)
        self.store.messages.append(sut_input)
        return self.store

    def __exit__(self, exc_type, exc_val, traceback):
        response = exc_val if exc_val else getattr(self.store.handler, self.response_attr)
        self.store.messages.append(response)
        if len(self.store.messages) % 2 != 0:
            raise exceptions.RecorderException(log_msg='failed to record even number of messages!')
        self.store.check_no_uncalled_test_doubles()
