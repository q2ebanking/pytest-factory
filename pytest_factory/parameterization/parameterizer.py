"""
TODO generic logic for taking a test Item, checking which parameterizations are
active, then creating new tests for each permutation of each fixture associated
with that Item.

gets used in pytest hook in pytest.py
"""
from pytest import Item
from typing import List


def parameterize(item: Item) -> List[Item]:
    return []
