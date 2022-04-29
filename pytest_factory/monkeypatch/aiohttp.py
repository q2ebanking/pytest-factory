import json

from aiohttp import ClientSession, ClientResponse

from pytest_factory.monkeypatch.utils import update_monkey_patch_configs, get_generic_caller
from pytest_factory.framework.exceptions import TypeTestDoubleException
from pytest_factory.http import MockHttpRequest, MockHttpResponse
from pytest_factory.framework.base_types import ANY_MOCK_RESPONSE


class MockClientResponse(ClientResponse):
    def __init__(self, body: bytes = None, status=200, headers: dict = None):
        self._body = body
        self.status = status
        self._cache = {}
        self._headers = headers or {}


def _request_callable(*_, **kwargs) -> MockHttpRequest:
    qwargs = {k: v for k, v in kwargs.items() if k in {'url', 'method', 'headers'}}
    mhr = MockHttpRequest(**qwargs)
    return mhr


MOCK_RESP_TYPE = ANY_MOCK_RESPONSE[ClientResponse]


def _response_callable(*_, mock_response: MOCK_RESP_TYPE, **kwargs) -> ClientResponse:
    """
    for some very strange reason, if you put a breakpoint here, debug mode passes all aiohttp tests
    if you don't, but run in debug mode, all aiohttp tests fail!
    """
    if isinstance(mock_response, ClientResponse):
        response = mock_response
    else:
        args = {'status': 200}
        if mock_response is None:
            args['status'] = 404
        elif isinstance(mock_response, MockHttpResponse):
            args['body'] = mock_response.body
            args['status'] = mock_response.status
            args['headers'] = mock_response.headers
        elif isinstance(mock_response, bytes):  # bytes body 200
            args['body'] = mock_response
        elif isinstance(mock_response, str):
            args['body'] = mock_response.encode()
        elif isinstance(mock_response, dict):  # json body 200
            args['body'] = json.dumps(mock_response).encode()
        else:
            raise TypeTestDoubleException(request_module_name='aiohttp', response=mock_response)

        response = MockClientResponse(**args)
    response._cache = {}
    response._url = kwargs.get('url')
    # TODO need to replicate redirect behavior unless allow_redirects==False.
    #  how though? could return an array instead and then it's up to
    # if response.status_code == 302 and kwargs.get('allow_redirects') is not False:
    # wut do
    return response


new_method = get_generic_caller(method_name='request',
                                request_callable=_request_callable,
                                response_callable=_response_callable)

patch_members = {
    'request': new_method
}

update_monkey_patch_configs(callable_obj=ClientSession, patch_members=patch_members)
