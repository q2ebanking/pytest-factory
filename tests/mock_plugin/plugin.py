import json
from typing import Any

from pytest_factory.http import MockHttpRequest, BasePlugin
from pytest_factory.framework.factory import make_factory
from pytest_factory.framework.mall import MALL


class MockPlugin(BasePlugin):
    PLUGIN_URL = 'http://somedomain.com'

    @staticmethod
    def get_plugin_responses(req_obj: MockHttpRequest) -> Any:
        """
        note there is no "self" because this method will be used as an independent function
        in this example we will keep the factory name and service name the same but this is rarely the case in real life
        """
        body_dict = json.loads(req_obj.content)
        factory_name = body_dict.get('service_name')
        routing_param = body_dict.get('service_param')
        store = MALL.get_store()
        factory = getattr(store, factory_name)
        responses = factory.get(routing_param)
        return responses


def mock_service0(key: str, response: str):
    return make_factory(req_obj=key, response=response)


def mock_service1(key: str, response: str):
    return make_factory(req_obj=key, response=response)
