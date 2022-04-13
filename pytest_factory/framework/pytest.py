"""
pytest integration hooks

import path to this file must be in pytest_plugins in conftest.py

"""
import os
import pytest

from pytest_factory.framework.mall import MALL


@pytest.fixture()
def store():
    """
    store fixture - this is where the test-specific store gets assigned to the
    test function
    :return:
    """
    store = MALL.get_store()
    store.register_plugins(plugins=MALL.plugins)
    return store


# def monkey_patch_all(monkeypatch, request) -> None:
#     """
#     """
#     patch_callables(monkeypatch)
#     patch_env_vars(monkeypatch)


@pytest.fixture(autouse=True)
def patch_callables(monkeypatch, request):
    """
    we are grabbing request here because it appears to be the first time we can positively identify which test we are
    running and need to set the "current_test" MALL property
    """
    test_name = request.node.name
    MALL.current_test = test_name
    for _, configs in MALL.monkey_patch_configs.items():
        callable_obj = configs.get('callable')
        for member_name, member_patch in configs.get('patch_methods').items():
            monkeypatch.setattr(callable_obj, member_name, member_patch, raising=False)


@pytest.fixture(autouse=True)
def patch_env_vars(monkeypatch):
    current_env_vars = {k: os.getenv(k) for k, v in MALL.env_vars.items()}
    envs = [monkeypatch.setenv(k, v) for k, v in MALL.env_vars.items()]

    yield envs
    for k, v in current_env_vars.items():
        if v:
            os.environ[k] = v
