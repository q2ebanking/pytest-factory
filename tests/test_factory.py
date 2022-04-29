from pytest_factory.framework.factory import make_factory, BaseMockRequest
from pytest_factory.framework.store import Store
import pytest

pytestmark = pytest.mark.asyncio


class Foo:
    def __init__(self, req_obj):
        self.req_obj = req_obj

    def bar(self):
        return int(self.req_obj)


class MockRequest(BaseMockRequest):
    def __init__(self, i: int):
        self.i = i
        self.sut_callable = Foo

    def __int__(self):
        return self.i


@make_factory(req_obj=MockRequest(42))
def test_abtract(store):
    resp = store.sut.bar()
    assert resp == 42


def _setup(store: Store):
    # TODO not sure about this - do we want these to have side effects on store?
    store.ASDF = 'asfd'
    return 'jkl;'


def _teardown(store: Store, resp: str):
    assert resp == 'jkl;'


@make_factory(req_obj=MockRequest(42), setup=_setup, teardown=_teardown)
def test_setup(store):
    resp = store.sut.bar()
    assert resp == 42
