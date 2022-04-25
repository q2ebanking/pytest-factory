import pytest

from pytest_factory.framework.parse_configs import prep_stores_update_local, get_config_parser
from pytest_factory.framework.mall import MALL

from tests.passthru_app import PassthruTestHandler


def test_prep_local_config():
    conf_dict = prep_stores_update_local(
        dir_name='config_test', path='**/test_config.ini'
    )

    assert conf_dict == {
        'assert_no_extra_calls': False,
        'assert_no_missing_calls': True,
        'http_req_wildcard_fields': ['otherfield'],
        'request_handler_class': PassthruTestHandler,
        'string_var': 'BAR'
    }


def test_untyped_config():
    prep_stores_update_local(
        dir_name='config_test', path='**/test_config.ini'
    )
    assert MALL.current_test == 'test_untyped_config'
    assert MALL._by_dir['config_test']['string_var'] == 'BAR'

    conf_dict = prep_stores_update_local(dir_name='tests', path='**/test_config.ini')
    assert conf_dict['string_var'] == 'FOO'
    assert MALL._by_dir['tests']['string_var'] == 'FOO'

