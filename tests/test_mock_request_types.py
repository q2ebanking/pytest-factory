"""
non async unit tests
"""
from pytest_factory.outbound_mock_request import MockHttpRequest


def test_mock_http_request_compare():
    mhr0 = MockHttpRequest(path='abcd/fdsa?a=0&b=true')
    mhr1 = MockHttpRequest(path='abcd/fdsa?a=0&b=true', headers={'a': 'b'})
    mhr2 = MockHttpRequest(path='abcd/fdsa?b=true&a=0')
    assert mhr0.compare(mhr2)
    assert mhr0.compare(mhr1)
