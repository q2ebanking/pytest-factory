import configparser
from pathlib import PosixPath

import pytest

from pytest_factory.framework.parse_configs import prep_stores_update_local


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

    assert request_handler == PosixPath(
        "tests/mock_plugin/another_plugin/AnotherHandler"
    )
    assert conf_dict == {
        "demo_key_path": PosixPath("tests/mock_plugin/another_plugin.py"),
        "http_req_wildcard_fields": ["query", " otherfield"],
        "hq_url": "http://someotherdomain.com",
    }
