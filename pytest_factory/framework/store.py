from __future__ import annotations
from typing import Dict, Optional, Any, Union, List, Callable, Set
from functools import cached_property
from pytest import Item

import pytest_factory.framework.exceptions as exceptions
from pytest_factory.framework.base_types import Factory, BaseMockRequest, MOCK_RESPONSES_TYPE, ROUTING_TYPE, \
    compare_unknown_types, TrackedResponses
from pytest_factory.framework.default_configs import (assert_no_missing_calls as default_assert_no_missing_calls,
                                                      assert_no_extra_calls as default_assert_no_extra_calls)


def is_plugin(kallable: Callable) -> bool:
    return hasattr(kallable, 'get_plugin_responses')


class Store:
    """
    stores test doubles for a given test method
    """

    def __init__(self, test_path: str):
        """
        :param test_path: the full name of the test this Store belongs to
        """
        self._test_name = test_path
        self._item: Optional[Item] = None
        self._sut_callable: Optional[Callable] = None
        self._sut_factory: Optional[Factory] = None
        self.assert_no_extra_calls: bool = default_assert_no_extra_calls
        self.assert_no_missing_calls: bool = default_assert_no_missing_calls
        self.factory_names: Set[str] = set()
        self.messages = []
        self._opened: bool = False

    @property
    def sut(self) -> object:
        """
        the system-under-test
        """
        if not self._sut_factory and self._opened:
            raise exceptions.MissingHandlerException
        if not self._sut_factory:
            return None
        try:
            _sut = self._sut_factory.get_sut
        except AttributeError as _:
            return None
        return _sut

    def shop(self, **kwargs) -> Shopper:
        """
        provides a context manager for test execution where the store can record the session
        :param kwargs: values passed from test execution wrapper (e.g. run_test) to override MALL configs for this store
        :return a Shopper ready to enter the store
        """
        return Shopper(store=self, **kwargs)

    def update(self, req_obj: Union[BaseMockRequest, str], factory_name: str,
               response: Union[Any, List[Any]],
               response_is_sut: Optional[bool] = False):
        """
        adds factory-made test doubles to this Store
        :param req_obj: the input to the system-under-test or depended-on-component
        :param factory_name: the name of the factory that created the test double being added to Store
        :param response: the output from the depended-on-component or the system-under-test itself
        :param response_is_sut: if True, response is the system-under-test
        """
        exchange_id = req_obj.exchange_id if hasattr(req_obj, 'exchange_id') else None
        responses = TrackedResponses.from_any(exchange_id=exchange_id, response=response)
        self.factory_names.add(factory_name)
        if not hasattr(self, factory_name) or getattr(self, factory_name) is None:
            new_factory = Factory(req_obj=req_obj, responses=responses)
            if response_is_sut:
                self._sut_factory = new_factory
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
            ex = exceptions.MissingFactoryException(factory_name=factory_name)
            if self.assert_no_missing_calls:
                raise ex
            else:
                return None
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
            ex = exceptions.MissingTestDoubleException(req_obj=req_obj)
            if self.assert_no_missing_calls:
                raise ex
            return mock_responses
        next_response = mock_responses.mark_and_retrieve_next()
        if isinstance(next_response, Callable):
            try:
                final_response = next_response(req_obj)
            except AssertionError as ae:
                doc_exc = exceptions.DocAssertionException(assertion_error=ae, factory_name=factory_name,
                                                           req_obj=req_obj)
                raise doc_exc from ae
        else:
            final_response = next_response

        if mock_responses and final_response is None:
            final_response = self._check_overcalled_test_doubles(req_obj=req_obj, mock_responses=mock_responses)
        return final_response

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
                        if factory_name is not self._sut_factory.FACTORY_NAME}
        return test_doubles

    def check_no_uncalled_test_doubles(self):
        """
        checks if this Store has any test_doubles that have not been called the
        number of times expected by default, it will log warnings to logger
        """
        uncalled_test_doubles = {}

        for test_double, response_dict in self._get_test_doubles.items():
            if response_dict == self._sut_factory:
                continue
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
    """
    captures all Messages between SUT and DOC in three phases:
    1. capture input to SUT
    2. yield to test execution, during which DOC I/O are captured
    3. capture SUT output
    """
    def __init__(self, response_attr: str, request_attr: str, store: Store, *_, **kwargs):
        self.store = store
        self.response_attr = response_attr
        self.request_attr = request_attr
        for k, v in kwargs.items():
            if v is not None:
                setattr(self.store, k, v)

    def __enter__(self):
        sut_input = getattr(self.store.sut, self.request_attr)
        self.store.messages.append(sut_input)
        return self.store

    def __exit__(self, exc_type, exc_val, traceback):
        response = exc_val if exc_val else getattr(self.store.sut, self.response_attr)
        self.store.messages.append(response)
        if len(self.store.messages) % 2 != 0:
            raise exceptions.RecorderException(log_msg='failed to record even number of messages!')
        self.store.check_no_uncalled_test_doubles()
