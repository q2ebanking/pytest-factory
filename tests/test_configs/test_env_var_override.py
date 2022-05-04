import os

from tests.test_factory import make_factory, BaseMockRequest


class Foo:
    def __init__(self, *_, **__):
        pass

    def get_env(self, var_name: str):
        return os.environ.get(var_name)


class MockRequest(BaseMockRequest):
    def __init__(self):
        self.sut_callable = Foo


@make_factory(req_obj=MockRequest())
def test_env_var(store):
    result = store.sut.get_env('TEST')
    assert result == '404'