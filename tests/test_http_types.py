from pytest_factory.framework.http_types import MockHttpResponse, Response, MockHttpRequest


def test_response():
    mhr = MockHttpResponse(content=b'asdf', status_code=203)

    assert isinstance(mhr, Response)
    assert mhr.text == 'asdf'
    assert mhr.ok


def test_request_compare_same_path():
    m0 = MockHttpRequest(path='https://www.google.com/maps')
    m1 = MockHttpRequest(path='https://www.google.com/maps')
    assert m0.compare(m1)


def test_request_compare_missing_netloc():
    m0 = MockHttpRequest(path='https://www.google.com/maps')
    m1 = MockHttpRequest(path='/maps')
    assert not m0.compare(m1)


def test_request_compare_missing_schema():
    m0 = MockHttpRequest(path='https://www.google.com/maps')
    m1 = MockHttpRequest(path='www.google.com/maps')
    assert not m0.compare(m1)


def test_request_compare_same_path_diff_method():
    m0 = MockHttpRequest(method='get', path='https://www.google.com/maps')
    m1 = MockHttpRequest(method='post', path='https://www.google.com/maps')
    assert not m0.compare(m1)


def test_request_compare_missing_query():
    m0 = MockHttpRequest(path='https://www.google.com/maps')
    m1 = MockHttpRequest(path='https://www.google.com/maps?a=b')
    assert m0.compare(m1)


def test_request_compare_diff_query():
    m0 = MockHttpRequest(path='https://www.google.com/maps?b=a')
    m1 = MockHttpRequest(path='https://www.google.com/maps?a=b')
    assert not m0.compare(m1)


def test_request_compare_wild_query():
    m0 = MockHttpRequest(path='https://www.google.com/maps?*')
    m1 = MockHttpRequest(path='https://www.google.com/maps?a=b')
    assert m0.compare(m1)


def test_request_compare_wild_reverse():
    m0 = MockHttpRequest(path='https://www.google.com/maps?b=a')
    m1 = MockHttpRequest(path='https://www.google.com/maps?*')
    assert m0.compare(m1)


def test_request_compare_wild_url():
    m0 = MockHttpRequest(path='https://www.google.com/maps')
    m1 = MockHttpRequest(path='https://www.google.com/*')
    assert m0.compare(m1)
