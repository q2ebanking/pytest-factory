import json

from pytest_factory.http import MockHttpRequest, BasePlugin
from pytest_factory.framework.factory import make_factory


class MockPlugin(BasePlugin):
    PLUGIN_URL = 'http://somedomain.com'

    @staticmethod
    def map_request_to_factory(req_obj: MockHttpRequest) -> str:
        """
        note there is no "self" because this method will be used as an independent function
        in this example we will keep the factory name and service name the same but this is rarely the case in real life
        """
        body_dict = json.loads(req_obj.content)
        factory_name = body_dict.get('service_name')
        return factory_name

    @staticmethod
    def parse_test_double_key(req_obj: MockHttpRequest) -> str:
        body_dict = json.loads(req_obj.content)
        routing_param = body_dict.get('service_param')
        return routing_param


def mock_service0(key: str, response: str):
    return make_factory(req_obj=key, response=response)


def mock_service1(key: str, response: str):
    return make_factory(req_obj=key, response=response)