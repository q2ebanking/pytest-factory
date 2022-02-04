"""
settings for plugin

this is where you integrate plugin code

the example below shows how a complex service or service layer can be mocked
by mapping the service's url to an adapter module. see adapter_test.py
"""
from pytest_factory.framework.settings import Settings
from pytest_factory.framework.stores import Store
from pytest_factory.mock_request_types import MockHttpRequest
import adapter_test as adapter

MOCK_SERVICE_LAYER_URL = "https://www.fakeservicelayer.com"
init_store = Store(mock_http_server={
    MockHttpRequest(path=MOCK_SERVICE_LAYER_URL): adapter
})

SETTINGS = Settings()
