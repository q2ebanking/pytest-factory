import configparser
import pytest

from pytest_factory.framework.parse_configs import prep_stores_update_local

from tests.app import MainHandler


@pytest.fixture(scope="function")
def setup_config_test():

    dir_name = "config_test"
    config = configparser.ConfigParser()
    config.read("tests/test_data/test_config.ini")

    return dir_name, config


def test_prep_local_config(setup_config_test):
    dir_name, config = setup_config_test
    request_handler, conf_dict = prep_stores_update_local(
        dir_name=dir_name, conf=config
    )

    assert request_handler == MainHandler
    assert conf_dict == {
        "demo_key_path": "tests/mock_plugin/another_plugin.py",
        "http_req_wildcard_fields": ["query", " otherfield"],
        "plugin_url": "http://someotherdomain.com",
    }
