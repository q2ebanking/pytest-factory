import json

from pytest_factory.http import MockHttpRequest, BasePlugin
from pytest_factory.framework.factory import make_factory


class MockPlugin(BasePlugin):
    PLUGIN_URL = 'http://somedomain.com'

    def map_request_to_factory(self, req_obj: MockHttpRequest) -> str:
        body_dict = json.loads(req_obj.content)
        factory_name = body_dict.get('service_name')
        return factory_name


def mock_service0(key: str, response: str):
    return make_factory(req_obj=key, response=response)


def mock_service1(key: str, response: str):
    return make_factory(req_obj=key, response=response)
