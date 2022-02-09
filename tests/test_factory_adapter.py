# import pytest
#
# from pytest_factory.http import mock_http_server
# from pytest_factory import mock_request
# from pytest_factory.framework.pytest import LOGGER
#
# pytestmark = pytest.mark.asyncio
#
# EXPECTED_WARNINGS = {
#     'test_http_no_calls_warning': '''
# pytest-factory WARNING: the following fixtures have not been called: {'mock_http_server': {MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None): ['yup']}}!
# pytest-factory WARNING: if this is not expected, consider this a test failure!''',
#     'test_http_extra_call_warning': '''
# pytest-factory WARNING: UNEXPECTED CALL DETECTED. expected only 1 calls to MockHttpRequest(protocol='http', host='127.0.0.1', method='get', uri='http://www.test.com/mock_endpoint', version='HTTP/1.0', remote_ip=None)
# pytest-factory WARNING: will repeat last response: yup'''
# }
#
#
# @mock_http_server(path='http://www.test.com/mock_endpoint', response='yup')
# @mock_request()
# class TestHttp:
#     @mock_http_server(path='http://www.test.com/mock_endpoint',
#                       response='nope')
#     async def test_http_func_override(self, store):
#         resp = await store.handler.run_test()
#         assert resp == 'nope'
#
#     @mock_http_server(path='http://www.test.com/*', response='wild')
#     async def test_http_wildcard_path(self, store):
#         """
#         TODO this might just be stupid hard
#         :param handler:
#         :param store:
#         :return:
#         """
#         resp = await store.handler.run_test()
#         assert resp == 'wild'
#
#     @mock_http_server(path='http://www.test.com/mock_endpoint',
#                       response=lambda x: x.path)
#     async def test_http_response_function(self, store):
#         resp = await store.handler.run_test()
#         assert resp == 'http://www.test.com/mock_endpoint'
#
#     class TestResponseTracking:
#         @mock_request(path='?num=0')
#         async def test_http_no_calls_warning(self, store):
#             """
#             see self.teardown_method
#             """
#             resp = await store.handler.run_test()
#             assert resp == ''
#
#         @mock_request(path='?num=2')
#         async def test_http_extra_call_warning(self, store):
#             """
#             please note that this test is expected to raise a non-fatal
#             UserWarning
#             see self.teardown_method
#             """
#             resp = await store.handler.run_test(assert_no_extra_calls=False)
#             assert resp == 'yupyup'
#
#         async def test_http_call_same_endpoint_diff_test(self, store):
#             """
#             """
#             resp = await store.handler.run_test()
#             assert resp == 'yup'
#
#         def teardown_method(self, method):
#             """
#             be aware that if AssertionError gets raised here the debugger will
#             likely jump context to a method called f"{test_func}_teardown" that
#             does not exist after the pytest.Session ends.
#
#             for PyCharm this means when attempting to debug just the method
#             from within the dedicated "Debug" tile, it will try to execute and
#             debug the "_teardown" method which no longer exists, and PyTest
#             will claim it could not find any tests to collect.
#
#             manually select the actual test method and execute debug instead.
#
#             :param method:
#             :return:
#             """
#             expected = EXPECTED_WARNINGS.get(method.__name__)
#             if expected:
#                 actual = LOGGER.buffer[-1]
#                 assert actual == expected
