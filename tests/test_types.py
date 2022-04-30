"""
non async unit tests
"""
from pytest_factory.http import MockHttpRequest, MockHttpResponse
from pytest_factory.lifecycle.recording import reify


def test_mock_http_request_compare():
    mhr0 = MockHttpRequest(url='abcd/fdsa?a=0&b=true')
    mhr1 = MockHttpRequest(url='abcd/fdsa?a=0&b=true', headers={'a': 'b'})
    mhr2 = MockHttpRequest(url='abcd/fdsa?b=true&a=0')
    assert mhr0.compare(mhr2)
    assert mhr0.compare(mhr1)
    assert str(mhr0) == ('<class pytest_factory.framework.http_types.MockHttpRequest: '
                         "{'allow_redirects': False, 'url': 'abcd/fdsa?a=0&b=true', 'method': 'get', "
                         "'body': b'', 'headers': {}}>")
    s = mhr0.serialize()
    mhr3 = reify(s)
    assert mhr0.kwargs == mhr3.kwargs


def test_http_response():
    mhr0 = MockHttpResponse(body=b'hi', status=201, headers={'Content-Type': 'text'})
    s = mhr0.serialize()
    mhr1 = reify(s)
    p = mhr0.write()
    args = mhr0.write(just_args=True)
    assert args == "body=b'hi', status=201, headers={'Content-Type': 'text'}"
    assert p == "MockHttpResponse(body=b'hi', status=201, headers={'Content-Type': 'text'})"
    assert mhr0.kwargs == mhr1.kwargs
    assert mhr0.body == mhr1.body
    assert mhr0.status == mhr1.status
    assert mhr0.headers == mhr1.headers
