from json import JSONDecodeError

from requests import Response
from pytest_factory.writer import Exchange, List, Recording, Writer
from pytest_factory.monkeypatch.tornado import TornadoRequest


class TestWriter:
    def test_unexpected_xml(self):
        """
        this test will create a test module
        """
        hp = 'tests.passthru_app.PassthruTestHandler'
        request = TornadoRequest(method='post', path='/', body='<xmlDoc>foo</xmlDoc>')
        setattr(request, 'factory_name', 'tornado_handler')
        setattr(request, 'factory_path', 'pytest_factory.monkeypatch.tornado')
        response = JSONDecodeError
        se: Exchange = (request, response)
        r = Recording(incident_type=JSONDecodeError, sut_exchange=se)
        w = Writer(recording=r, handler_path=hp)
        w.write_test('tests/test_unexpected_xml.py')

    # def test_500_doc(self):
    #     hp = 'tests.passthru_app.PassthruTestHandler'
    #     request = MockHttpRequest(path='/endpoint0')
    #     setattr(request, 'FACTORY_NAME', 'mock_request')
    #     setattr(request, 'FACTORY_PATH', 'pytest_factory.inbound_request_double')
    #     response = Response()
    #     response.status_code = 500
    #     response._content = b''
    #     se: Exchange = (request, response)
    #     de: List[Exchange] = [
    #         (MockHttpRequest(path='http://www.test.com/endpoint0'), response)
    #     ]
    #     r = Recording(incident_type=JSONDecodeError, sut_exchange=se, doc_exchanges=de)
    #     w = Writer(recording=r, handler_path=hp)
    #     w.write_test('tests/test_500_doc.py')
