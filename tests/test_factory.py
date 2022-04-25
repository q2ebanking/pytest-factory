from pytest_factory.framework.factory import make_factory
from pytest_factory.framework.store import Store
import pytest

pytestmark = pytest.mark.asyncio


class Foo:
    def __init__(self, req_obj):
        self.req_obj = req_obj

    @classmethod
    def _from_request(cls, req_obj):
        return cls(req_obj)

    def bar(self):
        return int(self.req_obj)


@make_factory(req_obj='42', handler_class=Foo)
def test_abtract(store):
    resp = store.handler.bar()
    assert resp == 42


def _setup(store: Store):
    # TODO not sure about this - do we want these to have side effects on store?
    store.ASDF = 'asfd'
    return 'jkl;'


def _teardown(store: Store, resp: str):
    assert resp == 'jkl;'


@make_factory(req_obj='42', handler_class=Foo, setup=_setup, teardown=_teardown)
def test_setup(store):
    resp = store.handler.bar()
    assert resp == 42
