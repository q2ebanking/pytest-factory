"""
pytest integration hooks

import path to this file must be in pytest_plugins in conftest.py

"""
import pytest

from pytest_factory.framework.mall import MALL
from pytest_factory import logger

logger = logger.get_logger(__name__)  # TODO user logger in here!


@pytest.fixture()
def store(request):
    """
    store fixture - this is where the test-specific store gets assigned to the
    test function
    :return:
    """
    test_name = request.node.name
    store = MALL.get_store(test_name=test_name)
    store.register_plugins(plugins=MALL.plugins)
    return store


@pytest.fixture(scope='function', autouse=True)
def monkey_patch_all(monkeypatch) -> None:
    """
    this method MUST be imported into conftest.py in order for non HQ mocks to work!
    :param monkeypatch:
    :return:
    """
    for _, configs in MALL.monkey_patch_configs.items():
        callable_obj = configs.get('callable')
        for member_name, member_patch in configs.get('patch_methods').items():
            monkeypatch.setattr(callable_obj, member_name, member_patch, raising=False)
