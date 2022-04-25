import pytest
import os

from requests import Response

from pytest_factory.monkeypatch.requests import _request_callable, _response_callable, TypeTestDoubleException

url = 'http://www.aol.com'


def test_env_var(store):
    assert os.getenv('TEST') == '420'


class TestRequestCallable:
    def test_happy(self):
        o = _request_callable(method_name='get', url=url)
        assert o.uri == url
        assert o.method == 'get'

    def test_no_url(self):
        with pytest.raises(expected_exception=TypeError,
                           match=r'get\(\) missing 1 required positional argument: \'url\''):
            _request_callable(method_name='get')

    def test_json(self):
        o = _request_callable(method_name='post', url=url, json={'foo': 'bar'})
        assert o.body == b'{"foo": "bar"}'
        assert o.headers.get('Content-Type') == 'application/json'

    def test_body_str(self):
        o = _request_callable(method_name='post', url=url, body='{"foo": "bar"}')
        assert o.body == b'{"foo": "bar"}'

    def test_headers(self):
        o = _request_callable(method_name='delete', url=url,
                              headers={'Content-Type': 'application/json'})
        assert o.headers['Content-Type'] == 'application/json'


class TestResponseCallable:
    def test_none(self):
        o = _response_callable(mock_response=None)
        assert o.status_code == 404
        assert not o.ok

    def test_response(self):
        r = Response()
        r.status_code = 500
        r._content = b'blah'
        o = _response_callable(mock_response=r)
        assert o == r

    def test_bytes(self):
        o = _response_callable(mock_response=b'blah')
        assert o.content == b'blah'

    def test_str(self):
        o = _response_callable(mock_response='blah')
        assert o.content == b'blah'

    def test_json(self):
        d = {'foo': 'bar'}
        o = _response_callable(mock_response=d)
        assert o.json() == d

    def test_unknown(self):
        class Foo:
            pass

        with pytest.raises(expected_exception=TypeTestDoubleException):
            _response_callable(mock_response=Foo())
