from json import JSONDecodeError

from pytest_factory.lifecycle.writer import List, Recording, Writer
from pytest_factory.framework.base_types import Exchange
from pytest_factory.http import MockHttpResponse
from pytest_factory.monkeypatch.tornado import TornadoRequest, MockHttpRequest
from tests.test_lifecycle.utils import get_file_path


class TestWriter:
    def test_unexpected_xml(self):
        """
        this test will create a test module
        """
        test_file_path = get_file_path('test_factory_tests/test_unexpected_xml.py')
        hp = 'tests.test_http.passthru_app.PassthruTestHandler'
        request = TornadoRequest(method='post', url='/', body=b'<xmlDoc>foo</xmlDoc>', sut_callable=hp)
        response = JSONDecodeError
        se: Exchange = (request, response)
        r = Recording(incident_type=JSONDecodeError, sut_exchange=se)
        w = Writer(recording=r)
        w.write_test(test_file_path)

    def test_500_doc(self):
        test_file_path = get_file_path('test_factory_tests/test_500_doc.py')
        hp = 'tests.test_http.passthru_app.PassthruTestHandler'
        request = TornadoRequest(url='endpoint0', sut_callable=hp)
        response = MockHttpResponse(status=500, body=b'ERROR: 500')
        se: Exchange = (request, response)
        de: List[Exchange] = [
            (MockHttpRequest(url='http://www.test.com/endpoint0'), response)
        ]
        r = Recording(incident_type=Exception, sut_exchange=se, doc_exchanges=de)
        w = Writer(recording=r)
        w.write_test(test_file_path)
