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
    with MALL.stock():
        store.register_plugins(plugins=MALL.plugins)
        yield store


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
    """
    this is where the MALL gets stocked: during the collection of each test file, as each factory is invoked

    Note: the last two params are for compatibility with pytest
    """
    parts = file_path.parts
    test_dir = None
    if len(parts) > 1 and parts[-2] == DEFAULT_FOLDER_NAME:
        test_dir = parts[-2]
    elif len(parts) > 2 and parts[-3] == DEFAULT_FOLDER_NAME:
        test_dir = parts[-2]
    file_name = parts[-1]
    if test_dir and len(file_name) >= 7 and 'test' in [file_name[:4], file_name[-7:-3]]:
        with MALL.stock(test_dir=test_dir):
            outcome = yield
    else:
        outcome = yield
    outcome.get_result()
