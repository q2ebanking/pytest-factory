from json import JSONDecodeError
from typing import List

from pytest_factory.lifecycle.writer import Recording
from pytest_factory.framework.base_types import Exchange
from pytest_factory.http import MockHttpResponse
from pytest_factory.monkeypatch.tornado import TornadoRequest, MockHttpRequest

from tests.test_http.passthru_app import PassthruTestHandler


class TestRecording:
    def test_serialize_all_messages(self):
        hp = f"{PassthruTestHandler.__module__}.{PassthruTestHandler.__name__}"
        request = TornadoRequest(url='endpoint0', sut_callable=hp)
        response = MockHttpResponse(status=500, body=b'ERROR: 500')
        se: Exchange = (request, response)
        de: List[Exchange] = [
            (MockHttpRequest(url='http://www.test.com/endpoint0'), response)
        ]
        r0 = Recording(incident_type=Exception, sut_exchange=se, doc_exchanges=de)
        serialized_recording = r0.serialize()
        r1 = Recording.deserialize(b_a=serialized_recording)
        assert serialized_recording == r1.serialize()

    def test_serialize_with_exception(self):
        """
        this test will serialize and deserialize a recording
        """
        hp = f"{PassthruTestHandler.__module__}.{PassthruTestHandler.__name__}"
        request = TornadoRequest(method='post', url='/', body=b'<xmlDoc>foo</xmlDoc>', sut_callable=hp)
        response = JSONDecodeError
        se: Exchange = (request, response)
        r0 = Recording(incident_type=JSONDecodeError, sut_exchange=se)
        serialized_recording = r0.serialize()
        r1 = Recording.deserialize(b_a=serialized_recording)
        assert serialized_recording == r1.serialize()
