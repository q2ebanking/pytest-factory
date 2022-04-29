import os
from typing import Optional, Union, List

import requests
from tornado.web import RequestHandler, Application
from tornado.httputil import HTTPServerRequest
from tornado.concurrent import Future

from pytest_factory.lifecycle.recording import Recording, Exchange
from pytest_factory.http import MockHttpRequest
from pytest_factory.monkeypatch.tornado import read_from_write_buffer


class TornadoRecorderRequestHandler(RequestHandler):
    def __init__(self, application: Application, request: HTTPServerRequest, **kwargs) -> None:
        super().__init__(application=application, request=request, **kwargs)
        self._doc_exchanges: List[Exchange] = []
        self._incident_type: Optional[Exception] = None

    def call_get(self, *args, **kwargs) -> requests.Response:
        """
        example of how a DOC exchange is registered
        """
        response = requests.get(*args, **kwargs)
        exchange = (MockHttpRequest(method='get', **kwargs), response)
        self._doc_exchanges.append(exchange)
        return response

    def _handle_request_exception(self, e: BaseException) -> None:
        self._incident_type = e
        super()._handle_request_exception(e=e)

    def _get_response(self) -> requests.Response:
        if not self._finished:
            raise Exception('too early to capture handle response!')
        r = requests.Response()
        r.status_code = self.get_status()
        r._content = read_from_write_buffer(self._write_buffer)  # TODO bytes or str?
        return r

    def finish(self, chunk: Optional[Union[str, bytes, dict]] = None) -> "Future[None]":
        future = super().finish(chunk=chunk)
        request = self.request  # TODO
        response = self._get_response()
        sut_exchange = (request, response)
        incident_type = self._incident_type
        r = Recording(sut_exchange=sut_exchange, doc_exchanges=self._doc_exchanges, incident_type=incident_type)
        url = os.environ.get('accumulator_url')
        resp = requests.post(url=url, data=r.serialize())
        # TODO handle error
        return future
