import os
from typing import Optional, Union, List, Any

import requests
from requests import Response
from tornado.web import RequestHandler, Application
from tornado.httputil import HTTPServerRequest

from pytest_factory.lifecycle.recording import Recording, types
from pytest_factory.http import MockHttpRequest, MockHttpResponse
from pytest_factory.monkeypatch.tornado import read_from_write_buffer


class TornadoRecorderRequestHandler(RequestHandler):
    def __init__(self, application: Application, request: HTTPServerRequest, **kwargs) -> None:
        super().__init__(application=application, request=request, **kwargs)
        self._doc_exchanges: List[types.Exchange] = []
        self._incident_type: Optional[Exception] = None

    def call_get(self, *args, **kwargs) -> Response:
        """
        example of how a DOC exchange is registered
        """
        response: Response = requests.get(*args, **kwargs)
        try:
            recorded_request = MockHttpRequest(method='get', **kwargs)
            recorded_response = MockHttpResponse(status=response.status_code, body=response.content,
                                                 exchange_id=recorded_request.exchange_id,
                                                 headers=response.headers)
            exchange = (recorded_request, recorded_response)
            self._doc_exchanges.append(exchange)
        finally:
            return response

    def send_error(self, status_code: int = 500, **kwargs: Any) -> None:
        incident_type = kwargs.pop('exception')
        super().send_error(status_code=status_code, **kwargs)
        request = MockHttpRequest(method=self.request.method, url=self.request.uri, body=self.request.body)
        status = self.get_status()
        body = read_from_write_buffer(self._write_buffer)
        response = MockHttpResponse(status=status, body=body, exchange_id=request.exchange_id)
        sut_exchange = (request, response)
        # TODO capture env vars - scrub them of test environment vars in test code
        r = Recording(sut_exchange=sut_exchange, doc_exchanges=self._doc_exchanges, incident_type=incident_type)
        url = os.environ.get('accumulator_url')
        requests.post(url=url, data=r.serialize())
