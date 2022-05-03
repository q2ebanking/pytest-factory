"""
pytest integration hooks

import path to this file must be in pytest_plugins in conftest.py

"""
import pytest

from pytest_factory.framework.mall import MALL, DEFAULT_FOLDER_NAME


@pytest.fixture()
def store(request):
    """
    store fixture - this is where the test-specific store gets assigned to the
    test function
    :return:
    """
    store = MALL.get_store(item=request.node)
    store.register_plugins(plugins=MALL.plugins)
    store.open()
    yield store
    store.close()


@pytest.fixture(autouse=True)
def patch_callables(monkeypatch, request):
    """
    we are grabbing request here because it appears to be the first time we can positively identify which test we are
    running and need to set the "_current_test" MALL property
    """

    MALL.get_store(item=request.node)
    for configs in MALL.get_monkeypatch_configs():
        callable_obj = configs.get('callable')
        for member_name, member_patch in configs.get('patch_methods').items():
            monkeypatch.setattr(callable_obj, member_name, member_patch, raising=False)


@pytest.hookimpl(hookwrapper=True)
def pytest_collect_file(file_path, path, parent):
    if file_path.parts[-1][:4] == 'test_' and DEFAULT_FOLDER_NAME \
            in {parent.name, parent.parent.name if parent.parent else None}:
        MALL._current_test_dir = parent.name
    outcome = yield
    if isinstance(outcome, Exception):
        raise outcome


@pytest.hookimpl(hookwrapper=True)
def pytest_collection(session):
    test_dir = session.config.invocation_dir.basename
    MALL.open(test_dir=test_dir)
    outcome = yield
    if isinstance(outcome, Exception):
        raise outcome
    MALL.close()
