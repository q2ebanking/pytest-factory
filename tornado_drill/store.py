import pytest
from typing import Dict, List

from tornado_drill.fixtures.base import BaseMockRequest


class Store:
    """
    stores fixtures for a given async test method
    """

    def __init__(self):
        self.fixtures: Dict[str, List[BaseMockRequest]] = {}


global STORES
STORES: List[Store] = {}


@pytest.fixture(scope='function')
def mocks(request):
    """
    fixture container, just used as marker, pytest_generate_tests will set appropriate values based
    on decorators.
    :return:
    """
    STORES[]
    STORES = MocksHolder()
    return MOCKS_HOLDER
