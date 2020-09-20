"""
TODO parameterize given test by failure modes of its fixtures
"""
from pytest import Item
from typing import List

from pytest_factory.framework.stores import STORES
from pytest_factory.framework.settings import LOGGER
import pytest_factory.mock_request_types as mrt


class FailureMode:
    def __init__(self, name: str, request: mrt.BaseMockRequest,
                 response: mrt.MOCK_HTTP_RESPONSE):
        self.name = name
        self.request = request
        self.response = response


def cause_failures(item: Item) -> List[Item]:
    store = STORES.get_store(item.name)
    new_tests: List[Item] = []
    for factory_name, response_dict in store.get_fixtures.items():
        failure_modes = response_dict.get('_failure_modes')
        if not failure_modes:
            LOGGER.warning(f'test {item.name} could not be parameterized by'
                           'failure modes because fixture created by '
                           '{factory_name} does not define them!')
            continue
        for failure_mode in failure_modes:
            test_name = f'{item.name}_{failure_mode.name}'
            new_test = Item(name=test_name, parent=item)
            new_tests.append(new_test)

    return new_tests
