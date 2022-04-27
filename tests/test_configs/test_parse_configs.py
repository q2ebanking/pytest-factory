from pytest_factory.framework.parse_configs import prep_stores_update_local
from pytest_factory.framework.mall import MALL


def test_configs():
    prep_stores_update_local(dir_name='test_configs')
    assert MALL.current_test == 'test_configs'
    assert MALL._by_dir['test_configs']['string_var'] == 'BAR'

    conf_dict = prep_stores_update_local(dir_name='tests')
    assert conf_dict['tests']['string_var'] == 'FOO'
    assert MALL._by_dir['tests']['string_var'] == 'FOO'
    assert MALL.string_var == 'BAR'
    MALL._current_test_dir = 'tests'
    assert MALL.string_var == 'FOO'
