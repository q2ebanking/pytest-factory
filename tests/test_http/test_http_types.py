from pytest_factory.framework.http_types import MockHttpRequest



def test_request_compare_same_path():
    m0 = MockHttpRequest(url='https://www.google.com/maps')
    m1 = MockHttpRequest(url='https://www.google.com/maps')
    assert m0.compare(m1)


def test_request_compare_missing_netloc():
    m0 = MockHttpRequest(url='https://www.google.com/maps')
    m1 = MockHttpRequest(url='/maps')
    assert not m0.compare(m1)


def test_request_compare_missing_schema():
    m0 = MockHttpRequest(url='https://www.google.com/maps')
    m1 = MockHttpRequest(url='www.google.com/maps')
    assert not m0.compare(m1)


def test_request_compare_same_path_diff_method():
    m0 = MockHttpRequest(method='get', url='https://www.google.com/maps')
    m1 = MockHttpRequest(method='post', url='https://www.google.com/maps')
    assert not m0.compare(m1)


def test_request_compare_missing_query():
    m0 = MockHttpRequest(url='https://www.google.com/maps')
    m1 = MockHttpRequest(url='https://www.google.com/maps?a=b')
    assert m0.compare(m1)


def test_request_compare_diff_query():
    m0 = MockHttpRequest(url='https://www.google.com/maps?b=a')
    m1 = MockHttpRequest(url='https://www.google.com/maps?a=b')
    assert not m0.compare(m1)


def test_request_compare_wild_query():
    m0 = MockHttpRequest(url='https://www.google.com/maps?*')
    m1 = MockHttpRequest(url='https://www.google.com/maps?a=b')
    assert m0.compare(m1)


def test_request_compare_wild_reverse():
    m0 = MockHttpRequest(url='https://www.google.com/maps?b=a')
    m1 = MockHttpRequest(url='https://www.google.com/maps?*')
    assert m0.compare(m1)


def test_request_compare_wild_url():
    m0 = MockHttpRequest(url='https://www.google.com/maps')
    m1 = MockHttpRequest(url='https://www.google.com/*')
    assert m0.compare(m1)
