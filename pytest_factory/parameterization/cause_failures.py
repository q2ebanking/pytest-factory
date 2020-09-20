"""
TODO parameterize given test by failure modes of its fixtures
"""
from pytest import Item
from typing import List

from pytest_factory.framework.stores import STORES
from pytest_factory.framework.settings import LOGGER


def cause_failures(item: Item) -> List[Item]:
    store = STORES.get_store(item.name)
    new_tests: List[Item] = []
    for factory_name, response_dict in store.get_fixtures.items():
        failure_modes = response_dict.get('_failure_modes')
        if not failure_modes:
            LOGGER.warning(f'test {item.name} could not be parameterized to'
                           'test failure modes because fixture created by '
                           '{factory_name} does not define them!')
            continue
        for request, response in failure_modes:
            new_test = Item(parent=item)
            new_tests.append(new_test)

    return new_tests
