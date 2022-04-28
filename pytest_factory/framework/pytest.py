"""
pytest integration hooks

import path to this file must be in pytest_plugins in conftest.py

"""
import pytest

from pytest_factory.framework.mall import MALL
from pytest_factory.framework.parse_configs import DEFAULT_FOLDER_NAME


@pytest.fixture()
def store():
    """
    store fixture - this is where the test-specific store gets assigned to the
    test function
    :return:
    """
    store = MALL.get_store()
    store.register_plugins(plugins=MALL.plugins)
    store.open()
    yield store
    store.close()


@pytest.fixture(autouse=True)
def patch_callables(monkeypatch, request):
    """
    we are grabbing request here because it appears to be the first time we can positively identify which test we are
    running and need to set the "current_test" MALL property
    """
    if hasattr(request, 'path'):
        test_dir = request.path.parent.name
    else:
        test_dir = DEFAULT_FOLDER_NAME
    MALL.get_store(test_name=request.node.name, test_dir=test_dir)
    for configs in MALL.get_monkeypatch_configs():
        callable_obj = configs.get('callable')
        for member_name, member_patch in configs.get('patch_methods').items():
            monkeypatch.setattr(callable_obj, member_name, member_patch, raising=False)


def pytest_configure(config):
    test_dir = config.invocation_dir.basename
    test_dir = test_dir if test_dir[:5] == 'test_' else DEFAULT_FOLDER_NAME
    MALL.open(test_dir=test_dir)


def pytest_sessionfinish(session, exitstatus):
    MALL.close()