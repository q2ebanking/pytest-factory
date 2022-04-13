import pytest

from pytest_factory.framework.parse_configs import prep_stores_update_local, get_config_parser
from pytest_factory.framework.mall import MALL

from tests.passthru_app import PassthruTestHandler


@pytest.fixture(scope="function")
def setup_config_test():
    dir_name = "config_test"
    config = get_config_parser(path='**/test_config.ini')

    return dir_name, config


def test_prep_local_config(setup_config_test):
    dir_name, config = setup_config_test
    conf_dict = prep_stores_update_local(
        dir_name=dir_name, conf=config
    )

    assert conf_dict == {
        'assert_no_extra_calls': False,
        'assert_no_missing_calls': True,
        'http_req_wildcard_fields': ['otherfield'],
        'request_handler_class': PassthruTestHandler,
        'string_var': 'BAR'
    }


def test_untyped_config(setup_config_test):
    dir_name, config = setup_config_test

    # Add to MALL for this test dir
    conf_dict = prep_stores_update_local(dir_name=dir_name, conf=config)
    MALL.load(conf=conf_dict, key=dir_name)
    assert MALL.current_test == 'test_untyped_config'
    assert MALL._by_dir['config_test']['string_var'] == 'BAR'

    config = get_config_parser(path='**/test_config.ini')
    conf_dict = prep_stores_update_local(dir_name='default', conf=config)
    MALL.load(conf=conf_dict, key='tests')
    assert MALL._by_dir['tests']['string_var'] == 'FOO'
