import pytest
from typing import Dict, List

from tornado_drill.fixtures.base import BaseMockRequest, MOCK_HTTP_RESPONSE
from tornado_drill.settings import Settings


class Store:
    """
    stores fixtures for a given async test method
    """

    def __init__(self, settings: Settings):
        self.fixtures_by_test: Dict[str, List[BaseMockRequest]] = {}

        if settings:
            self.load(settings)

    def load(settings: Settings):
        """
        TODO make this load self.fixtures_by_test with '*' as test_qualname
        so that the test wrapper will attach settings fixtures as fallback if
        no test class or function defines anything more specific
        """

    def update(self, test_qualname: str, fixture_name: str,
               req_obj: BaseMockRequest,
               response=MOCK_HTTP_RESPONSE):
        test_fixtures = self.fixtures_by_test.get(test_qualname)
        if not test_fixtures:
            new_fixture = {
                fixture_name: {
                    req_obj: response
                }
            }
            self.fixtures_by_test[test_qualname] = new_fixture
        else:
            fixture_def = test_fixtures.get(fixture_name)
            if not fixture_def:
                test_fixtures[fixture_name] = {req_obj: response}
            else:
                fixture_def[req_obj] = response


# used to store mock request definitions as the test hierarchy is traversed
global STORE
STORE = Store()


@pytest.fixture(scope='function')
def mocks(request):
    """
    fixture container, just used as marker, pytest_generate_tests will set appropriate values based
    on decorators.
    :return:
    """
    pass
