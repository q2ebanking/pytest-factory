"""
TODO parameterize given test by failure modes of its fixtures
"""
from pytest import Item
from typing import List

from pytest_factory.framework.stores import STORES


def cause_failures(item: Item) -> List[Item]:
    store = STORES.get_store(item.name)
    for fixture in store
    return [item]
