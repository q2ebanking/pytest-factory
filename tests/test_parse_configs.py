import pytest

from pytest_factory.framework.parse_configs import prep_stores_update_local, get_config_parser

from tests.passthru_app import PassthruTestHandler


@pytest.fixture(scope="function")
def setup_config_test():
    dir_name = "config_test"
    config = get_config_parser(filename='test_config.ini')

    return dir_name, config


def test_prep_local_config(setup_config_test):
    dir_name, config = setup_config_test
    conf_dict = prep_stores_update_local(
        dir_name=dir_name, conf=config
    )

    assert conf_dict == {
        'http_req_wildcard_fields': ['otherfield'],
        'request_handler_class': PassthruTestHandler
    }
