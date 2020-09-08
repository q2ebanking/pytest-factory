"""
non async unit tests
"""
from tornado_drill.fixtures.http import MockHttpRequest


def test_mock_http_request_hash():
    mhr0 = MockHttpRequest(path='abcd/fdsa', query='a=0&b=true')
    mhr1 = MockHttpRequest(
        path='abcd/fdsa', query='a=0&b=true', headers={'a': 'b'})
    mhr2 = MockHttpRequest(path='abcd/fdsa', query='b=true&a=0')
    assert hash(mhr0) == hash(mhr2)
    print('assert hash(mhr0) != hash(mhr1)')
    assert hash(mhr0) != hash(mhr1)
